from constants import biomarkers_dict
from test_ocr_gen import generate_test_set
import difflib
import pandas as pd
import re
import itertools

# Таблицы для замены символов
RUS_TO_LAT = {'а': 'a', 'е': 'e', 'о': 'o', 'с': 'c', 'р': 'p', 'у': 'y', 'к': 'k', 'х': 'x'}
LAT_TO_RUS = {v: k for k, v in RUS_TO_LAT.items()}
CHAR_TO_DIGIT = {'o': '0', 'O': '0', 'I': '1', 'l': '1', 'B': '8', 'S': '5', 'Z': '2', 'Э': '3', 'Ч': '4', 'э': '3', 'ч': '4'}
DIGIT_TO_CHAR = {'0': 'O', '1': 'I', '5': 'S', '2': 'Z', '8': 'B', '3': 'Э', '4': 'Ч'}

# Функция очистки текста
def clean_text(text):
    if text is None:
        return ''
    # Убираем все символы, кроме букв, цифр и пробелов
    text = re.sub(r'[^a-zа-я0-9\s]', '', text.lower())
    # Убираем лишние пробелы между словами
    text = re.sub(r'\s+', ' ', text)
    # Убираем пробелы в начале и конце строки
    return text.strip()


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
    for index, (key, data) in enumerate(biomarkers_dict.items()):
        normalized_key = key.lower()
        normalized_synonyms = [clean_text(syn) for syn in data["синонимы"]]
        normalized_dict[normalized_key] = {
            "синонимы": normalized_synonyms,
            "индекс": index
        }
    return normalized_dict


# Ищем OCR текст в словаре синонимов
def process_match(query, biomarkers_dict):
    """
    Выполняет поиск совпадений в словаре биомаркеров.

    Параметры:
        query (str): Входной текст для поиска.
        biomarkers_dict (dict): Словарь биомаркеров, где ключ — название группы, значение словарь - индекс группы, список синонимов.

    Возвращает:
        predicted_group (str): Найденная группа биомаркеров или None, если совпадений нет.
        similarity (float): Процент схожести (0.0–100.0) с найденным синонимом.
        group_index (int): Индекс группы в словаре или None, если совпадений нет.
    """
    # ✅ Нормализация текста
    query_norm = clean_text(normalize_text(query))

    # ✅ Внутренняя функция для поиска совпадений
    def find_best_match(text, biomarkers_dict, cutoff=0.7):
        all_synonyms = {clean_text(syn): (group, idx) for idx, (group, data) in enumerate(biomarkers_dict.items()) for syn in data['синонимы']}

        # Полное совпадение
        if text in all_synonyms:
            group, index = all_synonyms[text]
            return group, 100.0, index

        # Частичное совпадение через difflib
        matches = difflib.get_close_matches(text, all_synonyms, n=1, cutoff=cutoff)
        if matches:
            match = matches[0]
            similarity = difflib.SequenceMatcher(None, text, match).ratio() * 100
            group, index = all_synonyms[match]
            return group, similarity, index

        return None, 0.0, None

    # ✅ Основной поиск
    predicted_group, similarity, group_index = find_best_match(query_norm, biomarkers_dict)

    # ✅ Перебор всех возможных перестановок слов
    if not predicted_group and ' ' in query_norm:
        words = query_norm.split()
        for permutation in itertools.permutations(words):
            alt_query = ' '.join(permutation)
            predicted_group, similarity, group_index = find_best_match(alt_query, biomarkers_dict)
            if predicted_group:
                break

    rus, lat, digits = analyze_text(query_norm)

    # ✅ Приведение к латинице при равном количестве русских и латинских символов
    if not predicted_group and abs(rus - lat) <= 1:
        query_norm = ''.join(RUS_TO_LAT.get(c, c) for c in query_norm)
        predicted_group, similarity, group_index = find_best_match(query_norm, biomarkers_dict)

    # ✅ Если совпадений нет и есть цифры → пробуем заменить цифры на буквы
    if not predicted_group and digits > 0:
        query_norm = ''.join(DIGIT_TO_CHAR.get(c, c) for c in query_norm).lower()
        predicted_group, similarity, group_index = find_best_match(query_norm, biomarkers_dict)                

    return predicted_group, similarity, group_index

# Оценка точности метода
def evaluate_accuracy(test_dict, biomarkers_dict):
    exact_matches, partial_matches, low_confidence_matches = 0, 0, 0
    results = []

    for original, query in test_dict.items():
        predicted_group, similarity, group_index = process_match(query, biomarkers_dict)

        original_norm = clean_text(original.split('_')[0])
        true_group = next((group for group, syns in biomarkers_dict.items() if original_norm in syns['синонимы']), None)

        rus, lat, digits = analyze_text(query)

        if predicted_group == true_group:
            if similarity >= 99:
                exact_matches += 1
                result = "✔️ Полное совпадение"
            elif similarity >= 70:
                partial_matches += 1
                result = "🟠 Частичное совпадение"
            else:
                low_confidence_matches += 1
                result = "❔ Неуверенное совпадение"
        else:
            result = "❌ Неверное совпадение"

        results.append({
            "Исходный текст": original,
            "Распознанный текст": query,
            "Предсказанная группа": predicted_group if predicted_group else "-",
            "Индекс группы": group_index if group_index else "-",
            "Уверенность (%)": f"{similarity:.2f}" if similarity is not None else "-",
            "Результат": result,
            "Русских букв": rus,
            "Латинских букв": lat,
            "Цифр": digits
        })

    exact_acc = (exact_matches / len(test_dict)) * 100
    partial_acc = ((exact_matches + partial_matches) / len(test_dict)) * 100
    uncertain_acc = ((exact_matches + partial_matches + low_confidence_matches) / len(test_dict)) * 100

    print(f"Полная точность: {exact_acc:.2f}%")
    print(f"Точность с учётом частичных совпадений: {partial_acc:.2f}%")
    print(f"Точность с учётом неуверенных совпадений: {uncertain_acc:.2f}%")

    df = pd.DataFrame(results)
    df.to_csv('results.csv', index=False)

# Запуск теста
test_dict = generate_test_set(biomarkers_dict)
biomarkers_dict_prepared = prepare_biomarkers_dict(biomarkers_dict)
evaluate_accuracy(test_dict, biomarkers_dict_prepared)
