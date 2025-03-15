import telebot
from telebot import types
import os
from PIL import Image
from io import BytesIO
import requests
from ocr_med_test import analyze_image_base64_via_gpt4
from pdf2image import convert_from_bytes
from dotenv import load_dotenv
import base64

# Загружаем переменные из .env
load_dotenv()

# Получаем токен из окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден. Проверьте файл .env.")

# Создаем объект бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Состояния меню
MAIN_MENU = "main_menu"
PROCESS_IMAGE = "process_image"

# Глобальное состояние для отслеживания пользователя
user_state = {}

def set_user_state(user_id, state):
    user_state[user_id] = state

def get_user_state(user_id):
    return user_state.get(user_id, MAIN_MENU)

# Главное меню
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    set_user_state(chat_id, MAIN_MENU)

    # Создаем меню кнопок
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_upload = types.KeyboardButton("Загрузить")
    btn_photo = types.KeyboardButton("Сфотографировать")
    btn_exit = types.KeyboardButton("Выйти")
    markup.add(btn_upload, btn_photo, btn_exit)

    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def message_handler(message):
    chat_id = message.chat.id
    text = message.text.lower()

    if get_user_state(chat_id) == MAIN_MENU:
        if text == "загрузить":
            bot.send_message(chat_id, "Пожалуйста, загрузите изображение результатов анализов.")
            set_user_state(chat_id, PROCESS_IMAGE)
        elif text == "сфотографировать":
            bot.send_message(chat_id, "Пожалуйста, отправьте фотографию результатов анализов.")
            set_user_state(chat_id, PROCESS_IMAGE)
        elif text == "выйти":
            bot.send_message(chat_id, "До свидания!", reply_markup=types.ReplyKeyboardRemove())
            set_user_state(chat_id, MAIN_MENU)
        else:
            bot.send_message(chat_id, "Я вас не понял. Пожалуйста, выберите действие из меню.")
    elif get_user_state(chat_id) == PROCESS_IMAGE:
        bot.send_message(chat_id, "Ожидается изображение. Пожалуйста, отправьте фотографию или загрузите файл.")

def process_and_get_data_url(file_url):
    try:
        # Скачиваем файл
        response = requests.get(file_url)
        response.raise_for_status()
        file_content = BytesIO(response.content)

        # Проверяем тип файла (PDF или изображение)
        content_type = response.headers.get('Content-Type')
        if content_type == 'application/pdf':
            # Конвертируем первую страницу PDF в изображение
            images = convert_from_bytes(file_content.read(), fmt="JPEG")
            img = images[0]  # Обрабатываем только первую страницу
        else:
            # Открываем изображение
            img = Image.open(file_content)
            if img.mode == "RGBA":
                img = img.convert("RGB")  # Конвертируем в RGB при необходимости

        # Конвертируем в base64
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Формируем data URL
        data_url = f"data:image/jpeg;base64,{img_base64}"
        return data_url

    except Exception as e:
        raise ValueError(f"Ошибка обработки файла: {e}")

# Универсальный обработчик для фотографий и документов
@bot.message_handler(content_types=['photo', 'document'])
def file_handler(message):
    chat_id = message.chat.id

    if get_user_state(chat_id) == PROCESS_IMAGE:
        try:
            # Определяем URL файла в зависимости от типа контента
            if message.content_type == 'photo':
                file_id = message.photo[-1].file_id
            elif message.content_type == 'document':
                file_id = message.document.file_id
            else:
                bot.send_message(chat_id, "Неверный формат файла.")
                return

            file_info = bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_info.file_path}"

            # Обрабатываем и формируем data URL
            bot.send_message(chat_id, "Обрабатываю файл...")
            data_url = process_and_get_data_url(file_url)

            model_reply = analyze_image_base64_via_gpt4(data_url)

            # Отправляем результат (для демонстрации)
            bot.send_message(chat_id, f"Результат анализа: {model_reply}")

        except Exception as e:
            bot.send_message(chat_id, f"Ошибка при обработке файла: {e}")

        # Возвращаемся в главное меню
        start_handler(message)

# Запуск бота
print("Бот запущен. Нажмите Ctrl+C для остановки.")
bot.polling(none_stop=True)
