from constants import biomarkers_dict
import re
import random
import pandas as pd

# Таблицы для замены символов
RUS_TO_LAT = {'а': 'a', 'е': 'e', 'о': 'o', 'с': 'c', 'р': 'p', 'у': 'y', 'к': 'k', 'х': 'x'}
LAT_TO_RUS = {v: k for k, v in RUS_TO_LAT.items()}
CHAR_TO_DIGIT = {'o': '0', 'O': '0', 'I': '1', 'l': '1', 'B': '8', 'S': '5', 'Z': '2', 'Э': '3', 'Ч': '4', 'э': '3', 'ч': '4'}
DIGIT_TO_CHAR = {'0': 'O', '1': 'I', '5': 'S', '2': 'Z', '8': 'B', '3': 'Э', '4': 'Ч'}

# Функция для генерации случайных искажений
def generate_variations(word, max_variations=8, max_attempts=20):
    variations = set()
    attempts = 0

    while len(variations) < max_variations and attempts < max_attempts:
        variation = list(word)
        errors_count = random.randint(1, 2 if len(word) >= 7 else 1)

        applied_errors = set()

        for _ in range(errors_count):
            error_type = random.choice(['lang', 'digit', 'register', 'space', 'delete', 'cut', 'hyphen', 'swap_words'])

            if error_type == 'swap_words' and ' ' in word and 'swap_words' not in applied_errors and random.random() < 0.2:
                words = ''.join(variation).split()
                random.shuffle(words)
                variation = list(' '.join(words))
                applied_errors.add('swap_words')
                continue

            pos = random.randint(0, len(variation) - 1)
            orig_char = variation[pos]

            if error_type == 'lang':
                variation[pos] = RUS_TO_LAT.get(orig_char, LAT_TO_RUS.get(orig_char, orig_char))

            elif error_type == 'digit':
                if random.random() < 0.5:
                    variation[pos] = CHAR_TO_DIGIT.get(orig_char, DIGIT_TO_CHAR.get(orig_char, orig_char))

            elif error_type == 'register':
                variation[pos] = orig_char.swapcase()

            elif error_type == 'space' and len(word) > 3 and 'space' not in applied_errors:
                insert_pos = random.randint(1, len(variation) - 2)
                variation.insert(insert_pos, ' ')
                applied_errors.add('space')

            elif error_type == 'delete' and len(word) > 3:
                del variation[pos]

            elif error_type == 'cut' and len(word) > 3:
                if len(word) <= 6:
                    variation = variation[1:] if random.random() > 0.5 else variation[:-1]
                else:
                    cut_len = random.randint(1, 2)
                    variation = variation[cut_len:] if random.random() > 0.5 else variation[:-cut_len]

            elif error_type == 'hyphen' and '-' in variation and 'hyphen' not in applied_errors and random.random() < 0.3:
                variation = ''.join(variation).replace('-', '')
                variation = list(variation)
                applied_errors.add('hyphen')

        variations.add(''.join(variation))
        attempts += 1

    return list(variations)

# Генерация тестового набора
def generate_test_set(biomarkers_dict):
    test_dict = {}
    for biomarker, data in biomarkers_dict.items():
        for synonym in data['синонимы']:
            variations = generate_variations(synonym)
            for idx, variation in enumerate(variations):
                if variation != synonym:
                    test_dict[f"{synonym}_{idx}"] = variation
    return test_dict

# Генерация тестов
print('Длина справочника маркеров', len(biomarkers_dict))
test_dict = generate_test_set(biomarkers_dict)
print('Длина списка тестов', len(test_dict))

# Создание таблицы pandas
df = pd.DataFrame(list(test_dict.items()), columns=["Исходный текст", "Распознанный текст"])

# Устанавливаем максимальное количество отображаемых строк
pd.set_option('display.max_rows', None)  # Показывает все строки без ограничений
pd.set_option('display.max_columns', None)  # Показывает все столбцы без ограничений

# Печать таблицы
print(df.to_string(index=False))
df.to_csv('test_dict.csv', index=False)