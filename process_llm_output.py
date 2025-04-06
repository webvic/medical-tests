from constants import biomarkers_dict
from identify_biomarkers import process_match
import re
from pprint import pprint

def parse_lab_results(text: str, biomarkers_dict: dict) -> dict:
    lines = text.splitlines()  # Разбиваем отчет на строки
    lines = [
        line for line in lines 
        if line.strip()                        # пропускаем пустые строки
        and "дата" not in line.lower() 
        and "date" not in line.lower()
    ]
    result = {}

    # Группируем по 3 строки: [название, значение+единица, референсы]
    for i in range(0, len(lines), 3):
        try:
            name = lines[i]
            value_line = lines[i + 1]
            # Извлекаем число и единицу измерения
            match = re.match(r"([\d.,]+)\s*(\S+)", value_line)
            if not match:
                continue
            value_str, unit = match.groups()
            value = float(value_str.replace(',', '.'))

            # Получаем ID через process_match (3-й элемент кортежа. Если None, то 0)
            id_ = process_match(name)[2] or 0

            result[name] = {
                "id": id_,
                "Значение": value,
                "Единица измерения": unit
            }
        except IndexError:
            # Если строк не кратно 3
            continue
        except ValueError:
            # Ошибка приведения значения к float
            continue

    return result


test_text = '''
Дата анализа: 2024-06-16

Билирубин прямой (конъюгированный)
3.3 мкмоль/л
0 - 5

Глюкоза
5.0 ммоль/л
4.2 - 6.4

К+
1.5 ммоль/л
3.3 - 5.8

Na+
122 ммоль/л
132 - 155

Ca2+
1.05 ммоль/л
1.13 - 1.32

CI-
84 ммоль/л
95 - 115

Lac
1.1 ммоль/л
0.5 - 1.6

IciBil
3 мкмоль/л
9 - 21

ACТ
19.8 Ед/л
0 - 39

Билирубин общий
4.1 мкмоль/л
1.7 - 21

Общий белок
63.7 г/л
64 - 83
'''

res = parse_lab_results(text=test_text, biomarkers_dict=biomarkers_dict)
pprint(res, sort_dicts=False, width=120)