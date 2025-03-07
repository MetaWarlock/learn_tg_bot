import os
import logging
import sys
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from video_parser import get_video_info, extract_video_id
from youtube_parser import get_playlist_info, extract_playlist_id
from post_generator import generate_post_text, extract_title_and_subtitle, generate_cover
from io import BytesIO

# Настройка логирования
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

# Словарь для хранения состояний пользователей
user_states = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    logging.info("Команда /start получена")
    bot.send_message(message.chat.id, "Привет! Отправь мне ссылку на YouTube плейлист или видео, и я пришлю информацию и обложку.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    if user_states.get(chat_id, {}).get('state') == 'waiting_for_title':
        handle_new_title(message)
        return

    url = message.text.strip()
    logging.debug(f"Получена ссылка: {url}")

    try:
        data = None
        course_info = None
        poster_url = None
        year_text = "Неизвестно"
        duration_text = "Неизвестно"

        # Определяем тип ссылки
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
            logging.warning("Неизвестный формат ссылки.")
            bot.send_message(chat_id, "⛔ Некорректный формат ссылки")
            return

        if not all([data, poster_url, course_info]):
            raise ValueError("Одно из ключевых значений отсутствует")

        # Генерация поста и обложки
        post_text = generate_post_text(course_info)
        title_text, subtitle_text = extract_title_and_subtitle(post_text)
        cover_image = generate_cover(poster_url, title_text, year_text, duration_text, subtitle_text)

        # Преобразование изображения в байты
        cover_image_bytes = BytesIO()
        cover_image.seek(0)
        cover_image_bytes.write(cover_image.getvalue())
        cover_image_bytes.seek(0)

        # Преобразование подписи в HTML
        post_text_html = post_text.replace('**', '<b>').replace('__', '<i>')

        # Отправка поста с обложкой
        bot.send_photo(
            chat_id,
            cover_image_bytes,
            caption=post_text_html,
            parse_mode='HTML'
        )

        # Сохранение состояния
        user_states[chat_id] = {
            'data': data,
            'course_info': course_info,
            'poster_url': poster_url,
            'year_text': year_text,
            'duration_text': duration_text,
            'post_text': post_text,
            'cover_image': cover_image_bytes.getvalue()
        }

        # Добавление кнопок
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(
            InlineKeyboardButton("Всё окей", callback_data="approve"),
            InlineKeyboardButton("Поменять заголовок", callback_data="change_title")
        )
        bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

    except Exception as e:
        logging.error(f"Ошибка: {e}", exc_info=True)
        bot.send_message(chat_id, f"⛔ Ошибка: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if call.data == "approve":
        bot.answer_callback_query(call.id, "Пост одобрен!")
        if chat_id in user_states:
            del user_states[chat_id]
    elif call.data == "change_title":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "Пожалуйста, введите новый заголовок (две строчки):")
        user_states[chat_id]['state'] = 'waiting_for_title'

def handle_new_title(message):
    chat_id = message.chat.id
    new_title = message.text.strip()
    if chat_id not in user_states:
        bot.send_message(chat_id, "Произошла ошибка. Начните заново.")
        return

    title_lines = new_title.split('\n')
    if len(title_lines) != 2:
        bot.send_message(chat_id, "Введите заголовок в две строчки.")
        return

    title_text = title_lines[0].strip()
    subtitle_text = title_lines[1].strip()

    # Получаем сохраненные данные
    poster_url = user_states[chat_id]['poster_url']
    year_text = user_states[chat_id]['year_text']
    duration_text = user_states[chat_id]['duration_text']
    post_text = user_states[chat_id]['post_text']

    # Обновляем текст поста
    lines = post_text.split('\n')
    if lines:
        lines[0] = f"<b>{title_text}</b>"
        if len(lines) > 1:
            lines[1] = subtitle_text
        else:
            lines.append(subtitle_text)
        updated_post_text = '\n'.join(lines)
    else:
        updated_post_text = f"<b>{title_text}</b>\n{subtitle_text}"

    # Генерация новой обложки
    new_cover_image = generate_cover(poster_url, title_text, year_text, duration_text, subtitle_text)
    new_cover_image_bytes = BytesIO()
    new_cover_image.seek(0)
    new_cover_image_bytes.write(new_cover_image.getvalue())
    new_cover_image_bytes.seek(0)

    # Отправка обновленного поста
    bot.send_photo(
        chat_id,
        new_cover_image_bytes,
        caption=updated_post_text,
        parse_mode='HTML'
    )

    # Сброс состояния
    del user_states[chat_id]

if __name__ == "__main__":
    logging.info("Бот запущен!")
    bot.polling(none_stop=True)