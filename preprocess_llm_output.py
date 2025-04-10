raw_text = """Дата анализа: 2022-04-15

Билирубин общий
16.0 ммоль/л
20.0 - 50.0

Билирубин прямой
2.7 мкмоль/л
0.0 - 5.0

Билирубин непрямой
12.2 мкмоль/л
0.0 - 10.0

Гамма-глутамилтрансфераза
17.0 Ед/л
0.00 - 1.70

Щелочная фосфатаза
44.0 Ед/л
0.00 - 120.0

Аспартатаминотрансфераза
25.0 Ед/л
0.00 - 40.0

Аланинаминотрансфераза
25.0 Ед/л
0.00 - 55.0"""

import re

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

def clean_group(group, removed_items):
    """Обрабатывает одну группу строк."""
    cleaned = []
    word_patterns = [
        r'\b\w*органическ\w*\b',
        r'\b\w*общий\w*\b',
        r'\b\w*определение\w*\b',
        r'\b\w*конъюгирован\w*\b'
    ]

    for line in group:
        # Удалить строку полностью, если она содержит 'дата' или 'date'
        if re.search(r'\b(дата|date)\b', line, re.IGNORECASE):
            removed_items['date_lines'].append(line)
            continue

        # Если в строке есть "концентрация", обрезаем от неё до конца
        match = re.search(r'концентраци[яи]', line, re.IGNORECASE)
        if match:
            idx = match.start()
            before = line[:idx].strip()
            removed_items['ion_blocks'].append(line)
            if before:
                line = before  # сохраняем только начало строки
            else:
                continue  # ничего не осталось — пропускаем

        # Удаление слов с заданными паттернами
        original_line = line
        for pat in word_patterns:
            line = re.sub(pat, '', line, flags=re.IGNORECASE)

        if line.strip():
            if line != original_line:
                removed_items['matched_words'].append(original_line)
            cleaned.append(line.strip())

    return cleaned


def preprocess_text_to_groups(text):
    removed_items = {
        'matched_words': [],
        'ion_blocks': [],
        'date_lines': []
    }

    groups = split_into_groups(text)
    cleaned_groups = []

    for group in groups:
        cleaned = clean_group(group, removed_items)
        if cleaned:
            cleaned_groups.append(cleaned)

    return cleaned_groups, removed_items


# Использование

clean_text, log = preprocess_text_to_groups(raw_text)


print('Очищенный текст:\n', clean_text)
print('Лог:\n', log)

