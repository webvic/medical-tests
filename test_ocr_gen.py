import random
import re
import pandas as pd
from constants import biomarkers_dict

# Таблицы для замены символов
RUS_TO_LAT = {'а': 'a', 'е': 'e', 'о': 'o', 'с': 'c', 'р': 'p', 'у': 'y', 'к': 'k', 'х': 'x'}
LAT_TO_RUS = {v: k for k, v in RUS_TO_LAT.items()}
CHAR_TO_DIGIT = {'o': '0', 'O': '0', 'I': '1', 'l': '1', 'B': '8', 'S': '5', 'Z': '2', 'Э': '3', 'Ч': '4', 'э': '3', 'ч': '4'}
DIGIT_TO_CHAR = {'0': 'O', '1': 'I', '5': 'S', '2': 'Z', '8': 'B', '3': 'Э', '4': 'Ч'}

# ✅ Функция для генерации искажений
def generate_variations(word, max_variations=8, max_attempts=20):
    variations = set()
    attempts = 0
    
    # ✅ Ограничиваем число ошибок в зависимости от длины слова
    max_errors = 1 if len(word) <= 6 else 2

    while len(variations) < max_variations and attempts < max_attempts:
        variation = list(word)
        errors_count = random.randint(1, max_errors)

        applied_errors = set()

        for _ in range(errors_count):
            error_type = random.choice([
                'lang', 'digit', 'register', 'space', 'delete', 'cut', 'hyphen'
            ])

            # ✅ Ограничиваем длину для коротких слов
            if len(word) <= 6 and error_type in ['space', 'cut']:
                continue

            pos = random.randint(0, len(variation) - 1)
            orig_char = variation[pos]

            # ✅ Замена кириллицы ↔ латиницы
            if error_type == 'lang':
                if orig_char in RUS_TO_LAT:
                    variation[pos] = RUS_TO_LAT[orig_char]
                elif orig_char in LAT_TO_RUS:
                    variation[pos] = LAT_TO_RUS[orig_char]

            # ✅ Замена символов на цифры (и обратно)
            elif error_type == 'digit':
                if orig_char in CHAR_TO_DIGIT:
                    variation[pos] = CHAR_TO_DIGIT[orig_char]
                elif orig_char in DIGIT_TO_CHAR:
                    variation[pos] = DIGIT_TO_CHAR[orig_char]

            # ✅ Изменение регистра
            elif error_type == 'register':
                variation[pos] = orig_char.swapcase()

            # ✅ Вставка пробела (только в длинных словах)
            elif error_type == 'space' and len(variation) > 6 and 'space' not in applied_errors:
                insert_pos = random.randint(1, len(variation) - 2)
                variation.insert(insert_pos, ' ')
                applied_errors.add('space')

            # ✅ Удаление символов (только в длинных словах)
            elif error_type == 'delete' and len(variation) > 6:
                del variation[pos]

            # ✅ Обрезка символов
            elif error_type == 'cut' and len(variation) > 6:
                cut_len = random.randint(1, 2)
                variation = variation[cut_len:] if random.random() > 0.5 else variation[:-cut_len]

            # ✅ Удаление дефиса (если он есть)
            elif error_type == 'hyphen' and '-' in variation and 'hyphen' not in applied_errors:
                variation = ''.join(variation).replace('-', '')
                variation = list(variation)
                applied_errors.add('hyphen')

        # ✅ Если все символы стали кириллическими/латинскими → откат к исходному
        rus = sum(1 for c in variation if 'а' <= c <= 'я' or 'А' <= c <= 'Я')
        lat = sum(1 for c in variation if 'a' <= c <= 'z' or 'A' <= c <= 'Z')
        if rus == len(variation) or lat == len(variation):
            variation = list(word)

        variations.add(''.join(variation))
        attempts += 1

    return list(variations)

# ✅ Генерация тестового набора
def generate_test_set(biomarkers_dict):
    test_dict = {}
    for biomarker, data in biomarkers_dict.items():
        for synonym in data['синонимы']:
            variations = generate_variations(synonym)
            for idx, variation in enumerate(variations):
                if variation != synonym:
                    test_dict[f"{synonym}_{idx}"] = variation
    return test_dict

# ✅ Генерация тестов
print(f'Длина справочника маркеров: {len(biomarkers_dict)}')
test_dict = generate_test_set(biomarkers_dict)
print(f'Длина списка тестов: {len(test_dict)}')

# ✅ Создание таблицы pandas
df = pd.DataFrame(list(test_dict.items()), columns=["Исходный текст", "Распознанный текст"])

# ✅ Устанавливаем максимальное количество отображаемых строк
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# ✅ Печать таблицы
print(df.to_string(index=False))
df.to_csv('test_dict.csv', index=False)
