from telebot import TeleBot
from telebot.types import InputFile
import os
from dotenv import load_dotenv
from main import process_url, format_output
from image_generator import make_cover

load_dotenv()

bot = TeleBot(os.getenv("TG_TOKEN"))

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Отправь ссылку на YouTube плейлист или видео.")

@bot.message_handler(func=lambda m: True)
def handle_url(message):
    try:
        data, link, url_type = process_url(message.text)
        text = format_output(data, link, url_type)
        
        image = make_cover(
            data.get('cover_url', ''),
            data['title'],
            str(data.get('course_year', '')),
            f"{data['total_hours']} часов"
        )
        bot.send_photo(message.chat.id, InputFile(image, filename="cover.png"), caption=text)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("Бот запущен!")
    bot.polling()