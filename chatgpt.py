import os
import requests
from dotenv import load_dotenv
import logging

# ==========================
# Логгер для запросов к GPT
# ==========================
gpt_logger = logging.getLogger("gpt_logger")
gpt_logger.setLevel(logging.DEBUG)

# Хендлер для записи в gpt_log.txt (каждый раз затираем старые логи)
gpt_file_handler = logging.FileHandler("gpt_log.txt", mode="w", encoding="utf-8")
gpt_file_handler.setLevel(logging.DEBUG)
gpt_file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
gpt_file_handler.setFormatter(gpt_file_formatter)

# Очищаем предыдущие хендлеры (на случай повторного импорта)
if gpt_logger.hasHandlers():
    gpt_logger.handlers.clear()
gpt_logger.addHandler(gpt_file_handler)

# Загружаем переменные окружения
load_dotenv()
CHATGPT_API_KEY = os.getenv("CHATGPT_API_KEY")
if not CHATGPT_API_KEY:
    raise ValueError("Токен ChatGPT не найден в .env файле")

def generate_post(course_info: str) -> str:
    """
    Генерирует пост, используя OpenAI Chat Completion.
    Записывает полный запрос и полный ответ в gpt_log.txt (перезаписывая при новом запуске).
    Возвращает строку поста или None в случае ошибки.
    """

    # Формируем prompt
    prompt = f"""
Мне нужно сделать оформление поста для соцсети, в котором будет описан учебный курс, по образцу.
Вся информация берётся из описания курса:

{course_info}

Ответ верни без лишних символов, строго по формату.
"""

    # Логируем запрос
    gpt_logger.debug("=== Запрос к GPT ===\n" + prompt.strip() + "\n=== Конец запроса ===")

    headers = {
        "Authorization": f"Bearer {CHATGPT_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        # Используйте модель, доступную в вашем аккаунте
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    except Exception as e:
        gpt_logger.error(f"Ошибка сети при запросе к GPT: {e}")
        return None

    # Логируем сырое тело ответа
    gpt_logger.debug("=== RAW ответ от GPT ===\n" + response.text + "\n=== Конец ответа ===")

    # Проверяем статус
    try:
        response.raise_for_status()
    except Exception as e:
        gpt_logger.error(f"Ошибка при запросе к GPT: {e}")
        return None

    json_data = response.json()
    if not json_data["choices"]:
        gpt_logger.error("Ответ GPT не содержит choices.")
        return None

    # Извлекаем текст ответа
    content = json_data["choices"][0]["message"]["content"].strip()
    gpt_logger.debug("=== Очищенный ответ от GPT ===\n" + content + "\n=== Конец очищенного ответа ===")

    return content
