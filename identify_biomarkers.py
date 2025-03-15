from constants import biomarkers_dict
from test_ocr_gen import generate_test_set
import difflib
import pandas as pd
import re

# Таблицы для замены символов
RUS_TO_LAT = {'а': 'a', 'е': 'e', 'о': 'o', 'с': 'c', 'р': 'p', 'у': 'y', 'к': 'k', 'х': 'x'}
LAT_TO_RUS = {v: k for k, v in RUS_TO_LAT.items()}
CHAR_TO_DIGIT = {'o': '0', 'O': '0', 'I': '1', 'l': '1', 'B': '8', 'S': '5', 'Z': '2', 'Э': '3', 'Ч': '4', 'э': '3', 'ч': '4'}
DIGIT_TO_CHAR = {'0': 'O', '1': 'I', '5': 'S', '2': 'Z', '8': 'B', '3': 'Э', '4': 'Ч'}

# Функция очистки текста
def clean_text(text):
    if text is None:
        return ''
    return re.sub(r'[^a-zа-я0-9]', '', text.lower())

# Анализ текста
def analyze_text(text):
    rus = sum('а' <= c <= 'я' or 'А' <= c <= 'Я' for c in text)
    lat = sum('a' <= c <= 'z' or 'A' <= c <= 'Z' for c in text)
    digits = sum(c.isdigit() for c in text)
    return rus, lat, digits

# Нормализация текста
def normalize_text(text):
    text = text.strip().lower()
    rus, lat, digits = analyze_text(text)

    if rus > lat:
        text = ''.join(LAT_TO_RUS.get(c, c) for c in text)
    elif lat > rus and digits == 0:
        text = ''.join(RUS_TO_LAT.get(c, c) for c in text)

    if digits > 0:
        new_text = []
        for i, c in enumerate(text):
            if c.isdigit() and 0 < i < len(text)-1 and text[i-1].isalpha() and text[i+1].isalpha():
                c = DIGIT_TO_CHAR.get(c, c)
            new_text.append(c)
        text = ''.join(new_text)

    return text

# Подготовка словаря
def prepare_biomarkers_dict(biomarkers_dict):
    normalized_dict = {}
    for key, data in biomarkers_dict.items():
        normalized_key = key.lower()
        normalized_synonyms = [clean_text(syn) for syn in data["синонимы"]]
        normalized_dict[normalized_key] = normalized_synonyms
    return normalized_dict

# Поиск наилучшего совпадения
def find_best_match(text, biomarkers_dict, cutoff=0.7):
    text = normalize_text(text)
    all_synonyms = {syn: group for group, synonyms in biomarkers_dict.items() for syn in synonyms}

    if text in all_synonyms:
        return text, all_synonyms[text], 100.0

    matches = difflib.get_close_matches(text, all_synonyms, n=1, cutoff=cutoff)
    if matches:
        match = matches[0]
        similarity = difflib.SequenceMatcher(None, text, match).ratio() * 100
        group = all_synonyms[match]
        return match, group, similarity

    return None, None, 0.0

# Оценка точности метода
def evaluate_accuracy(test_dict, biomarkers_dict):
    exact_matches, partial_matches = 0, 0
    results = []

    for original, query in test_dict.items():
        query_norm = normalize_text(query)
        predicted_match, predicted_group, similarity = find_best_match(query_norm, biomarkers_dict)

        original_norm = clean_text(original.split('_')[0])
        true_group = next((group for group, syns in biomarkers_dict.items() if original_norm in syns), None)

        # Перестановка слов в многословных выражениях
        if not predicted_group and ' ' in query_norm:
            words = query_norm.split()
            for _ in range(len(words)):
                words.append(words.pop(0))
                alt_query = ' '.join(words)
                predicted_match, predicted_group, similarity = find_best_match(alt_query, biomarkers_dict)
                if predicted_group:
                    break

        # Если латинских и русских символов примерно поровну — приводим к латинице
        rus, lat, digits = analyze_text(query)
        if not predicted_group and abs(rus - lat) <= 1:
            query_norm = ''.join(RUS_TO_LAT.get(c, c) for c in query_norm)
            predicted_match, predicted_group, similarity = find_best_match(query_norm, biomarkers_dict)

        # Если нет совпадений, пробуем заменить цифры на символы и повторить
        if not predicted_group and digits > 0:
            query_norm = ''.join(DIGIT_TO_CHAR.get(c, c) for c in query_norm)
            predicted_match, predicted_group, similarity = find_best_match(query_norm, biomarkers_dict)

        if predicted_group is not None and true_group is not None:
            if clean_text(predicted_group) == clean_text(true_group):
                if similarity >= 99:
                    exact_matches += 1
                    result = "✔️ Полное совпадение"
                elif similarity >= 70:
                    partial_matches += 1
                    result = "🟠 Частичное совпадение"
                else:
                    result = "❌ Неверное совпадение"
            else:
                result = "❌ Неверное совпадение"
        else:
            result = "❌ Неверное совпадение"

        results.append({
            "Исходный текст": original,
            "Распознанный текст": query,
            "Предсказанная группа": predicted_group if predicted_group else "-",
            "Уверенность (%)": f"{similarity:.2f}",
            "Результат": result,
            "Русских букв": rus,
            "Латинских букв": lat,
            "Цифр": digits
        })

    exact_acc = (exact_matches / len(test_dict)) * 100
    partial_acc = ((exact_matches + partial_matches) / len(test_dict)) * 100

    print(f"Полная точность: {exact_acc:.2f}%")
    print(f"Точность с учётом частичных совпадений: {partial_acc:.2f}%")

    df = pd.DataFrame(results)
    df.to_csv('results.csv', index=False)

# Запуск теста
test_dict = generate_test_set(biomarkers_dict)
biomarkers_dict_prepared = prepare_biomarkers_dict(biomarkers_dict)
evaluate_accuracy(test_dict, biomarkers_dict_prepared)
