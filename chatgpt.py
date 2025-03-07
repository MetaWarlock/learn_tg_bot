import os
import requests
from dotenv import load_dotenv
import logging

# Логгер для запросов к GPT
gpt_logger = logging.getLogger("gpt_logger")
gpt_logger.setLevel(logging.DEBUG)

gpt_file_handler = logging.FileHandler("gpt_log.txt", mode="w", encoding="utf-8")
gpt_file_handler.setLevel(logging.DEBUG)
gpt_file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
gpt_file_handler.setFormatter(gpt_file_formatter)

if gpt_logger.hasHandlers():
    gpt_logger.handlers.clear()
gpt_logger.addHandler(gpt_file_handler)

load_dotenv()
CHATGPT_API_KEY = os.getenv("CHATGPT_API_KEY")
if not CHATGPT_API_KEY:
    raise ValueError("Токен ChatGPT не найден в .env файле")

def load_prompt_template():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(script_dir, "promt.txt")
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.error("Файл promt.txt не найден")
        return None

def generate_post(course_info: str) -> str:
    """
    Генерирует пост, используя OpenAI Chat Completion.
    Записывает полный запрос и ответ в gpt_log.txt.
    Возвращает сгенерированный текст поста или None в случае ошибки.
    """
    prompt_template = load_prompt_template()
    if not prompt_template:
        return None
    prompt = prompt_template.format(course_info=course_info)

    gpt_logger.debug("=== Запрос к GPT ===\n" + prompt.strip() + "\n=== Конец запроса ===")

    headers = {
        "Authorization": f"Bearer {CHATGPT_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    except Exception as e:
        gpt_logger.error(f"Ошибка сети при запросе к GPT: {e}")
        return None

    gpt_logger.debug("=== RAW ответ от GPT ===\n" + response.text + "\n=== Конец ответа ===")

    try:
        response.raise_for_status()
    except Exception as e:
        gpt_logger.error(f"Ошибка при запросе к GPT: {e}")
        return None

    json_data = response.json()
    if not json_data["choices"]:
        gpt_logger.error("Ответ GPT не содержит choices.")
        return None

    content = json_data["choices"][0]["message"]["content"].strip()
    gpt_logger.debug("=== Очищенный ответ от GPT ===\n" + content + "\n=== Конец очищенного ответа ===")

    return content
