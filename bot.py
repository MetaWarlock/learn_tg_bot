import os
import re
import logging
import sys
from telebot import TeleBot
from dotenv import load_dotenv
from video_parser import get_video_info, extract_video_id
from youtube_parser import get_playlist_info, extract_playlist_id
from post_image import make_cover
from chatgpt import generate_post
from io import BytesIO

# ==========================
# Настройка общего логгера
# ==========================
# Логи будем писать и в файл bot_errors.log (режим "a" или "w") и дублировать в консоль
logging.basicConfig(
    level=logging.DEBUG,  # или logging.INFO, если слишком многословно
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_errors.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Загружаем переменные окружения
load_dotenv()
TG_TOKEN = os.getenv("TG_TOKEN")
if not TG_TOKEN:
    raise ValueError("Токен Telegram не найден в .env файле")

# Создаем экземпляр бота
bot = TeleBot(TG_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    logging.info("Команда /start получена")
    bot.send_message(message.chat.id, "Привет! Отправь мне ссылку на YouTube плейлист или видео, и я пришлю информацию и обложку.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    logging.debug(f"Получена ссылка: {url}")

    try:
        # Инициализируем переменные, чтобы видно было, если что-то не заполнено
        data = None
        course_info = None
        poster_url = None
        year_text = "Неизвестно"
        duration_text = "Неизвестно"

        if "/playlist" in url:
            logging.debug("Обнаружен плейлист, парсим...")
            data = get_playlist_info(url)
            if not data:
                raise ValueError("get_playlist_info вернул None")

            clean_link = f"https://www.youtube.com/playlist?list={extract_playlist_id(url)}"
            course_info = f"📼 Название плейлиста: {data['title']}\n"
            if data['course_year']:
                course_info += f"📅 Год курса: {data['course_year']}\n"
            course_info += f"📝 Описание: {data['description'] or 'Описание отсутствует'}\n"
            course_info += f"⏳ Продолжительность курса: {data['total_hours']} часов\n"
            course_info += f"🔗 Ссылка на курс: {clean_link}\n"
            course_info += f"🎬 Всего видео: {len(data['videos'])}\n"
            for idx, video in enumerate(data['videos'], 1):
                course_info += f"\n{idx}. {video['title']}\n"
                course_info += f"   📅 Дата публикации: {video['published'].strftime('%Y-%m-%d')}\n"
                course_info += f"   ⏱ Продолжительность: {video['duration'] // 60} мин"

            poster_url = data['cover_url']
            year_text = str(data['course_year']) if data['course_year'] else "Неизвестно"
            duration_text = f"{data['total_hours']} часов"

        elif "/watch" in url or "youtu.be" in url:
            logging.debug("Обнаружено видео, парсим...")
            data = get_video_info(url)
            if not data:
                raise ValueError("get_video_info вернул None")

            clean_link = f"https://youtu.be/{extract_video_id(url)}"
            course_info = f"📼 Название курса: {data['title']}\n"
            course_info += f"📅 Год курса: {data['course_year']}\n"
            course_info += f"⏳ Продолжительность курса: {data['total_hours']} часов\n"
            course_info += f"📝 Описание: {data['description'] or 'Описание отсутствует'}\n"
            course_info += f"🔗 Ссылка на курс: {clean_link}"

            poster_url = data['cover_url']
            year_text = str(data['course_year'])
            duration_text = f"{data['total_hours']} часов"

        else:
            logging.warning("Неизвестный формат ссылки, отправляем ошибку пользователю.")
            bot.send_message(message.chat.id, "⛔ Неизвестный формат ссылки")
            return

        # Генерируем пост через ChatGPT
        logging.debug("Вызываем generate_post...")
        post_text = generate_post(course_info)

        if not post_text:
            raise ValueError("Не удалось получить пост от ChatGPT (post_text == None)")

        # Извлекаем заголовок и подзаголовок
        lines = post_text.split('\n')
        title_text = None
        subtitle_text = None
        for line in lines:
            if line.strip().startswith('**') and line.strip().endswith('**'):
                if title_text is None:
                    title_text = line.strip('*').strip()
                elif subtitle_text is None:
                    subtitle_text = line.strip('*').strip()
                    break
        
        if subtitle_text is None:
            # Ищем первую строку, которая может подойти на роль подзаголовка
            for line in lines[1:]:
                if line.strip() and not line.strip().startswith(('🗓', '⏰', '__', '🔹', '♦️')):
                    subtitle_text = line.strip()
                    break

        logging.debug(f"Итоговые title_text='{title_text}' subtitle_text='{subtitle_text}'")

        # Генерируем обложку
        logging.debug("Создаём обложку...")
        cover_image = make_cover(
            poster_url,
            title_text or "Без названия",
            year_text,
            duration_text,
            subtitle_text
        )
        if not cover_image:
            raise ValueError("make_cover вернула None или произошла ошибка при создании обложки.")

        # Преобразуем изображение в байты
        cover_image_bytes = BytesIO()
        cover_image.seek(0)
        cover_image_bytes.write(cover_image.getvalue())
        cover_image_bytes.seek(0)

        logging.debug("Отправляем картинку пользователю...")
        bot.send_photo(
            message.chat.id,
            cover_image_bytes,
            caption=post_text,
            parse_mode='HTML'
        )

    except Exception as e:
        logging.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)
        bot.send_message(message.chat.id, f"⛔ Ошибка: {str(e)}")

if __name__ == "__main__":
    logging.info("Бот запущен!")
    bot.polling(none_stop=True)
