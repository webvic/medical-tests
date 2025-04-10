from identify_biomarkers import process_match
import re
from pprint import pprint


def split_into_groups(text):
    """Разбивает текст на группы строк, разделённые пустыми строками."""
    raw_lines = text.splitlines()
    groups = []
    current_group = []

    for line in raw_lines:
        if line.strip() == '':
            if current_group:
                groups.append(current_group)
                current_group = []
        else:
            current_group.append(line)
    if current_group:
        groups.append(current_group)

    return groups

def clean_group(group):
    """Очищает одну группу строк от лишнего текста."""
    cleaned = []
    word_patterns = [
        r'\b\w*органическ\w*\b',
        r'\b\w*концентрация\w*\b',
        r'\b\w*ионов\w*\b',
        r'\b\w*в крови\w*\b',
        r'\b\w*определение\w*\b',
        r'\b\w*конъюгирован\w*\b'
    ]

    for line in group:
        # Удалить строку, если содержит 'дата' или 'date'
        if re.search(r'\b(дата|date)\b', line, re.IGNORECASE):
            continue

        # # Если в строке есть "концентрация", обрезаем от неё до конца
        # match = re.search(r'концентраци[яи]', line, re.IGNORECASE)
        # if match:
        #     idx = match.start()
        #     line = line[:idx].strip()
        #     if not line:
        #         continue  # если ничего не осталось — пропускаем строку

        # Удаление слов с заданными паттернами
        for pat in word_patterns:
            line = re.sub(pat, '', line, flags=re.IGNORECASE)

        if line.strip():
            cleaned.append(line.strip())

    return cleaned

def preprocess_text_to_groups(text):
    groups = split_into_groups(text)
    cleaned_groups = []

    for group in groups:
        cleaned = clean_group(group)
        if cleaned:
            cleaned_groups.append(cleaned)

    return cleaned_groups

def parse_lab_results(text: str) -> dict:
    if not text or not isinstance(text, str):
        return None

    blocks = preprocess_text_to_groups(text)

    result = {}

    for block in blocks:
        if len(block) < 2:
            continue

        name = block[0]
        value_line = block[1]

        match = re.match(r"([\d.,]+)\s*(\S+)", value_line)
        if not match:
            continue

        value_str, unit = match.groups()

        try:
            value = float(value_str.replace(',', '.'))
        except ValueError:
            continue

        id_ = process_match(name)[2] or 0

        result[name] = {
            "id": id_,
            "Значение": value,
            "Единица измерения": unit
        }

    return result


test_text = '''
Дата анализа: 2023-04-01

Билирубин общий
36.0 ммоль/л
3.0 - 21.0

Глюкоза
7.10 ммоль/л
4.10 - 6.0

Гамма-глутамиптрансфераза
15.0 Ед/л
0 - Щелочная фосфатаза
88.0 Ед/л
40.0 - 150.0

Аспартатаминотрансфераза
34.0 Ед/л*
0 - 25.0

Аланинаминотрансфераза
37.0 Ед/л*
0 - 25.0

Креатинфосфокиназа
102 Ед/л
148 Ед/л

Холесторин
6.51 ммоль/л*
До 5.0

ЛПВП
1.45 ммоль/л (жен)
1.2 ммоль/л (муж)

ЛПНП
4.17 ммоль/л*
4.51 ммоль/л*

Триглицериды
3.30 ммоль/л*
До 1.7

Коэффициент атерогенности
2.9
'''

res = parse_lab_results(text=test_text)
pprint(res, sort_dicts=False, width=120)