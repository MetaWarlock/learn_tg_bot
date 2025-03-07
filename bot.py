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

# Настройка логирования: вывод в консоль и запись в файл bot_errors.log
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_errors.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Загрузка переменных окружения
load_dotenv()
TG_TOKEN = os.getenv("TG_TOKEN")
if not TG_TOKEN:
    raise ValueError("Токен Telegram не найден в .env файле")

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
        data = None
        course_info = None
        poster_url = None
        year_text = "Неизвестно"
        duration_text = "Неизвестно"

        # Определяем тип ссылки через функции извлечения ID
        playlist_id = extract_playlist_id(url)
        video_id = extract_video_id(url)
        
        if playlist_id:
            logging.debug("Обнаружен плейлист, парсим...")
            data = get_playlist_info(url)
            if not data:
                raise ValueError("get_playlist_info вернул None")
            clean_link = f"https://www.youtube.com/playlist?list={playlist_id}"
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

        elif video_id:
            logging.debug("Обнаружено видео, парсим...")
            data = get_video_info(url)
            if not data:
                raise ValueError("get_video_info вернул None")
            clean_link = f"https://youtu.be/{video_id}"
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
            bot.send_message(message.chat.id, "⛔ Некорректный формат ссылки")
            return

        # Проверка наличия ключевых данных
        if not all([data, poster_url, course_info]):
            raise ValueError("Одно из ключевых значений отсутствует")

        # Генерация поста через ChatGPT
        logging.debug("Вызываем generate_post...")
        post_text = generate_post(course_info)
        if not post_text:
            raise ValueError("Не удалось получить пост от ChatGPT (post_text == None)")
        
        # Убираем лишние тройные кавычки, если они присутствуют
        post_text = post_text.replace("```", "")

        # Извлечение заголовка и подзаголовка
        lines = post_text.split('\n')
        title_text = None
        subtitle_text = None

        # Шаблон для поиска текста между <b>...</b>
        title_pattern = re.compile(r'<b>(.*?)</b>', re.IGNORECASE)

        for i, line in enumerate(lines):
            match = title_pattern.search(line)
            if match:
                # В group(1) будет содержаться всё, что между <b> и </b>
                title_text = match.group(1).strip()
                # Попробуем взять подзаголовок из следующей строки, если она есть
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    # Проверяем, что строка не начинается с эмодзи или тегов
                    if next_line and not next_line.startswith(('🗓', '⏰', '🔹', '♦️', '<a')):
                        subtitle_text = next_line
                break

        logging.debug(f"Итоговые title_text='{title_text}' subtitle_text='{subtitle_text}'")

        # Если заголовок длиннее 30 символов, обрезаем его и формируем подзаголовок
        if title_text and len(title_text) > 30:
            words = title_text.split()
            title_text = " ".join(words[:3])
            subtitle_text = " ".join(words[3:]) if not subtitle_text else subtitle_text
            logging.debug(f"Заголовок обрезан: title_text='{title_text}', subtitle_text='{subtitle_text}'")

        # Генерация обложки
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

        # Преобразование изображения в байты
        cover_image_bytes = BytesIO()
        cover_image.seek(0)
        cover_image_bytes.write(cover_image.getvalue())
        cover_image_bytes.seek(0)

        # Преобразование подписи из Markdown в HTML: убираем замену эмодзи, чтобы оставить их оригинал
        post_text_html = post_text.replace('**', '<b>').replace('__', '<i>')
        logging.debug("Отправляем картинку пользователю...")
        bot.send_photo(
            message.chat.id,
            cover_image_bytes,
            caption=post_text_html,
            parse_mode='HTML'
        )

    except Exception as e:
        logging.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)
        bot.send_message(message.chat.id, f"⛔ Ошибка: {str(e)}")

if __name__ == "__main__":
    logging.info("Бот запущен!")
    bot.polling(none_stop=True)
