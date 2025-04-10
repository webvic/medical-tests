import pandas as pd
import numpy as np
from typing import Tuple
from process_llm_output import parse_lab_results
from typing import Dict, Tuple

def safe_load_json(jstring: str):
    import json

    try:
        # Прямой parse — если это настоящий JSON
        return json.loads(jstring)
    except json.JSONDecodeError:
        try:
            # Если это JSON как строка — сначала декодируем \n, \" и пр.
            decoded = jstring.encode('utf-8').decode('unicode_escape')
            return json.loads(decoded)
        except Exception as e:
            raise ValueError(f"Невозможно распарсить JSON после двойного преобразования: {e}")


def compare_jsons(ref_data: Dict, rec_data: Dict) -> Tuple[int, int, int, float, str]:
    """
    Сравнивает 2 словаря биомаркеров, изготовленных из json с возможными ошибками
    """

    ref_values = {}
    rec_values = {}

    for name, values in ref_data.items():
        if values.get("id") != 0:
            ref_values[values["id"]] = str(values.get("Значение", "")).strip()

    for name, values in rec_data.items():
        if values.get("id") != 0:
            rec_values[values["id"]] = str(values.get("Значение", "")).strip()

    ref_ids = set(ref_values.keys())
    rec_ids = set(rec_values.keys())

    missing_ids = ref_ids - rec_ids
    extra_ids = rec_ids - ref_ids
    common_ids = ref_ids & rec_ids
    print('Отсутствуют id ',missing_ids, 'лишние id', extra_ids, 'Ошибки OCR',end = ' ')

    value_errors = 0
    error_details = []

    for i in common_ids:
        ref_val = ref_values[i]
        rec_val = rec_values[i]
        if ref_val == rec_val:
            continue
        try:
            ref_float = round(float(ref_val.replace(',', '.')), 2)
            rec_float = round(float(rec_val.replace(',', '.')), 2)
            if not np.isclose(ref_float, rec_float, atol=0.01):
                value_errors += 1
                error_details.append(f"id: {i} ({ref_val}->{rec_val})")
        except ValueError:
            value_errors += 1
            error_details.append(f"id: {i} ({ref_val}->{rec_val})")

    total_ref = len(ref_ids)
    total_errors = len(missing_ids) + len(extra_ids) + value_errors
    print(value_errors, error_details)
    total_possible = total_ref + len(extra_ids)
    error_percent = (total_errors / total_possible) * 100 if total_possible > 0 else 0.0

    return len(missing_ids), len(extra_ids), value_errors, round(error_percent, 2), "; ".join(error_details)

# Функция тестирования
def test_compare_json(df):
    """
    Прогоняет функцию сравнения по таблице тестирования для подготовки статистики для анализа точности
    """

    # Добавляем нужные столбцы заранее (на случай, если они отсутствуют)
    for col in ["Недостающие ID", "Лишние ID", "Ошибки значений", "Интегральная ошибка (%)", "Детали ошибок"]:
        if col not in df.columns:
            df[col] = None

    # print(df.columns.tolist())
    # print(df[["LLM - Шаг 1"]])


    # Основной цикл сравнения
    for i, row in df.iterrows():
        print("Строка ",i,row["Документ"],"Эталон ", end=' ')
        reference_json = fix_and_parse_json(row["Эталонный json"])
        print("ОК, OCR ",end=' ')
        
        # Преобразуем структурированный текст в словарь
        # recognized_json =parse_lab_results(row["LLM - Шаг 1"])
        recognized_json = fix_and_parse_json(row["JSON - шаг 2"])
        print("ОК ")

        if not reference_json or not recognized_json:

            df.at[i, "Точность (%)"] = None
            df.at[i, "Недостающие ID"] = None
            df.at[i, "Лишние ID"] = None
            df.at[i, "Ошибки значений"] = None
            df.at[i, "Детали ошибок"] = None
        else:
            missing, extra, wrong, score, details = compare_jsons(reference_json, recognized_json)
            df.at[i, "Точность (%)"] = 100-score
            df.at[i, "Недостающие ID"] = missing
            df.at[i, "Лишние ID"] = extra
            df.at[i, "Ошибки значений"] = wrong
            df.at[i, "Детали ошибок"] = details
            print("Документ, missing, extra, wrong, score, details",df.at[i, "Документ"], missing, extra, wrong, score, details)

    return(df)

json_ref_raw = """"{
  ""Билирубин общий"": {
    ""id"": 10,
    ""Значение"": 15.0,
    ""Единица измерения"": ""мкмоль/л""
  },
  ""Билирубин прямой"": {
    ""id"": 11,
    ""Значение"": 2.7,
    ""Единица измерения"": ""мкмоль/л""
  },
  ""Билирубин непрямой"": {
    ""id"": 12,
    ""Значение"": 12.3,
    ""Единица измерения"": ""мкмоль/л""
  },
  ""Гамма-глутамилтрансфераза"": {
    ""id"": 25,
    ""Значение"": 17.0,
    ""Единица измерения"": ""Ед/л""
  },
  ""Щелочная фосфатаза"": {
    ""id"": 22,
    ""Значение"": 44.0,
    ""Единица измерения"": ""Ед/л""
  },
  ""Аспартатаминотрансфераза"": {
    ""id"": 20,
    ""Значение"": 25.0,
    ""Единица измерения"": ""Ед/л""
  },
  ""Аланинаминотрансфераза"": {
    ""id"": 21,
    ""Значение"": 25.0,
    ""Единица измерения"": ""Ед/л""
  }
}
"""

json_llm_raw = """{
  ""Билирубин общий"": {
    ""id"": 10,
    ""Значение"": 16.0,
    ""Единица измерения"": ""мкмоль/л""
  },
  ""Билирубин прямой"": {
    ""id"": 11,
    ""Значение"": 2.7,
    ""Единица измерения"": ""мкмоль/л""
  },
  ""Билирубин непрямой"": {
    ""id"": 12,
    ""Значение"": 12.2,
    ""Единица измерения"": ""мкмоль/л""
  },
  ""Гамма-глутамилтрансфераза"": {
    ""id"": 25,
    ""Значение"": 17.0,
    ""Единица измерения"": ""Ед/л""
  },
  ""Щелочная фосфатаза"": {
    ""id"": 22,
    ""Значение"": 44.0,
    ""Единица измерения"": ""Ед/л""
  },
  ""Аспартатаминотрансфераза"": {
    ""id"": 20,
    ""Значение"": 25.0,
    ""Единица измерения"": ""Ед/л""
  },
  ""Аланинаминотрансфераза"": {
    ""id"": 21,
    ""Значение"": 25.0,
    ""Единица измерения"": ""Ед/л""
  }
}
"""

import re

def fix_and_parse_json(jstr: str):
    """
    преобразует битый json-выход LLM в словарь биомаркеров
    """
    if not jstr or not isinstance(jstr, str):
        return None

    # Убираем управляющие символы и двойные кавычки
    cleaned = re.sub(r'[\n\r\t]', '', jstr)
    cleaned = cleaned.replace('""', '"')

    pattern = re.compile(
        r'"([^"]+)"\s*:\s*\{'
        r'\s*"id"\s*:\s*(\d+),'
        r'\s*"Значение"\s*:\s*([\d.]+),'
        r'\s*"Единица измерения"\s*:\s*(?:"([^"]+)"|null)'
        r'\s*\}',
        re.UNICODE
    )

    result = {}
    for match in pattern.finditer(cleaned):
        name = match.group(1)
        _id = int(match.group(2))
        value = float(match.group(3))
        unit = match.group(4)
        result[name] = {"id": _id, "Значение": value, "Единица измерения": unit}

    return result if result else None

def summarize_sections_optimized(df: pd.DataFrame) -> pd.DataFrame:
    """
    Вычисляет и печатает средние метрики по папкам в зависимости от качества оригиналов а также общие метрики по всем тестам
    """
    
    numeric_cols = ["Точность (%)", "Недостающие ID", "Лишние ID", "Ошибки значений"]
    result_rows = []
    section_data = []
    section_number = -1

    def append_section_summary(sec_num, data_rows):
        if not data_rows:
            return
        section_df = pd.DataFrame(data_rows)
        mean_vals = section_df[numeric_cols].mean(numeric_only=True)
        result_rows.append({
            "Документ": f"ИТОГО ПАПКИ {sec_num}",
            "Секция": sec_num,
            **{col: round(mean_vals[col], 1) for col in numeric_cols}
        })

    for _, row in df.iterrows():
        doc = row["Документ"]

        # Пропускаем пустые строки и строки с "ИТОГО"
        if not isinstance(doc, str) or "ИТОГО" in doc:
            continue

        if "папка" in doc:
            append_section_summary(section_number, section_data)
            section_number += 1
            section_data = []
            continue

        if pd.notna(row["Точность (%)"]):
            new_row = row.copy()
            new_row["Секция"] = section_number
            section_data.append(new_row)
            result_rows.append(new_row.to_dict())

    # Последняя секция — только если она не пуста
    if section_data:
        append_section_summary(section_number, section_data)

    # Собираем итоговый DataFrame
    final_df = pd.DataFrame(result_rows)

    # Общие итоги
    overall = final_df[numeric_cols].mean(numeric_only=True)
    final_df.loc[len(final_df)] = {
        "Документ": "ИТОГО ОБЩИЙ",
        "Секция": "",
        **{col: round(overall[col], 1) for col in numeric_cols}
    }

    # Вывод
    columns_to_show = ["Документ", "Секция"] + numeric_cols
    print("\n📊 Итоговая таблица по секциям:\n")
    print(final_df[columns_to_show].to_string(index=False))

    return final_df[columns_to_show]

def convert_google_sheet_link_to_csv(original_link: str, gid: str = "0") -> str:
    # Извлекаем ID таблицы
    import re
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", original_link)
    if not match:
        raise ValueError("Невозможно извлечь ID из ссылки")

    sheet_id = match.group(1)
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


json_ref = fix_and_parse_json(json_ref_raw)
json_llm = fix_and_parse_json(json_llm_raw)

missing_ids, extra_ids, value_errors, error_percent, error_details = compare_jsons(json_ref, json_llm)
print("missing_ids, extra_ids, value_errors, error_percent, error_details",missing_ids, extra_ids, value_errors, error_percent, error_details)

path = "https://docs.google.com/spreadsheets/d/1lVHwpk8C4bfkAqTIFqOr82v0P1V75_n9WNZEoxhpVGA/export?format=csv&gid=0"

test_table_path = 'https://docs.google.com/spreadsheets/d/1Xh4LBFGmi8KTyOYAEVB3ymGiuMpJYpRNBVpYpKoY9xs/export?format=csv&gid=0'

df_test = pd.read_csv('Результаты - Новые тксты (1 модель).csv')

print(df_test)

df = test_compare_json(df_test)
summarize_sections_optimized(df)