import openai
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Получаем токен из окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не найден. Проверьте файл .env.")

"""
Model gpt-4o-mini
Pricing Pricing with Batch API*

$0.150 / 1M input tokens $0.075 / 1M input tokens $0.075 / 1M cached** input tokens
$0.600 / 1M output tokens $0.300 / 1M output tokens
"""

COST_INPUT_TOKENS_4OM_USD = 0.150
COST_OUTPUT_TOKENS_4OM_USD = 0.60
COST_USD_COPECK = 721*100/5.

# Переводим эти цены в доллары за 1 токен:
cost_input_per_token = COST_INPUT_TOKENS_4OM_USD * COST_USD_COPECK / 1_000_000    # = 0.00000015 $ за 1 входной токен
cost_output_per_token = COST_OUTPUT_TOKENS_4OM_USD * COST_USD_COPECK / 1_000_000   # = 0.00000060 $ за 1 выходной токен

# Установите ваш API-ключ
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def inflect_kopecks(number):
  """
  Inflects the word "копейки" (kopecks) based on the numerical value.

  Args:
    number: The numerical value.

  Returns:
    The correctly inflected word for "копейки".
  """
  number = abs(number)  # Consider only the absolute value for inflection
  if number % 10 == 1 and number % 100 != 11:
    return "копейка"
  elif 2 <= number % 10 <= 4 and (number % 100 < 10 or number % 100 >= 20):
    return "копейки"
  else:
    return "копеек"

def analyze_image_base64_via_gpt4(data_url):
    """
    Отправляет закодированное изображение (base64) в модель GPT-4 и возвращает её ответ.

    :return: Ответ модели (строка).
    """
    # Контекст и запрос
    context = """Ты сотрудник ФГБУ «НМИЦ ТПМ» Минздрава России. Ты помогаешь доктору обрабатывать результаты лабораторных анализов."""
    request = """Извлеки данные медицинских анализов из этого изображения."""

    # Отправляем запрос в модель GPT-4
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": context},
                {"role": "user",
                    "content": [
                        {"type": "text", "text": request},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        )

        # Обрабатываем ответ
        if response:
            model_reply = response.choices[0].message.content

            # Проверяем информацию об использовании токенов
            usage_info = response.usage
            if usage_info:
                prompt_tokens = usage_info.prompt_tokens
                completion_tokens = usage_info.completion_tokens
                # total_tokens = usage_info.total_tokens

                cost_input = prompt_tokens * cost_input_per_token
                cost_output = completion_tokens * cost_output_per_token
                total_cost = int(round(cost_input+cost_output))

                model_reply += f"\nСпасибо за использование сервиса ФГБУ «НМИЦ ТПМ» Минздрава России. \nС вас за услуги {total_cost} {inflect_kopecks(total_cost)}."

            return model_reply
        else:
            return "Не удалось получить ответ от модели."

    except Exception as e:
        return f"Ошибка при обращении к модели: {e}"


# if __name__ == "__main__":
    # request = """Извлеки данные медицинских анализов из этого изображения.
    # Снабди каждый показатель вероятностью его точного распознавания.
    # Подсчитай количество показателей, которые ты не смог определить
    # Подсчитай количество показателей в качестве распознавания которых не уверен.
    # Често сообщи о всех недочетах.
    # Выдели и перечисли в конце те показатели, которые выходят за референсные значения
    # """
    # context = """Ты сотрудник ФГБУ «НМИЦ ТПМ» Минздрава России. Ты помогаешь доктору обрабатывать результаты лабораторных анализов
    # Твоя задача - тщательно извлекать данные из сканированных или сфотографированных изображений
    # Данные приходят из разных источников и в разном формате, в том числе с искажениями и низкого качества.
    # Твоя задача очень ответственна. Главная заповедь врача "не навреди!"
    # Это означает не только распознать максимальное количество показателей, но и предупреждать доктора
    # о всех недочетах материалов или низкой вероятности качественного распознавания
    # Также тщательно проверь показатели, которые вышли за рамки рефернесных значений.
    # Все данные проверь 2 раза, чтобы избежать ошибок
    # Это 2 твои единственные задачи. Пожалуйста не прибавляй никаких дополнительных вежливых фраз типа
    # "Если вам нужны дополнительные пояснения или анализ, дайте знать!" или подобные им.
    # """


    # img_path = 'photo_2025-01-15_10-21-32.jpg'
    # print("Cсылка на изображение:", img_path)

    # reply_text = ocr_over_gpt4(img_path)

    # print(reply_text)
