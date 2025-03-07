import os
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import logging

def draw_text_top_left(draw, x, y, text, font, fill="white"):
    left0, top0, right0, bottom0 = draw.textbbox((0, 0), text, font=font)
    text_w = right0 - left0
    text_h = bottom0 - top0
    draw_x = x - left0
    draw_y = y - top0
    draw.text((draw_x, draw_y), text, font=font, fill=fill)
    return (x, y, x + text_w, y + text_h)

def make_cover(poster_url: str, title_text: str, year_text: str, duration_text: str, subtitle_text: str = None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    background_path = os.path.join(script_dir, "img/red_background.png")
    if not os.path.exists(background_path):
        raise FileNotFoundError(f"Фоновая картинка не найдена: {background_path}")
    fira_font_path = os.path.join(script_dir, "fonts/FiraSansExtraCondensed-Regular.ttf")
    calendar_path = os.path.join(script_dir, "img/calendar.png")
    clock_path = os.path.join(script_dir, "img/clock.png")
    if not os.path.exists(calendar_path):
        raise FileNotFoundError(f"Изображение календаря не найдено: {calendar_path}")
    if not os.path.exists(clock_path):
        raise FileNotFoundError(f"Изображение часов не найдено: {clock_path}")

    background = Image.open(background_path).convert("RGB")
    bg_w, bg_h = background.size

    if not poster_url:
        raise ValueError("URL обложки не указан")
    try:
        response = requests.get(poster_url, timeout=10)
        response.raise_for_status()
        poster = Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        logging.error(f"Ошибка загрузки обложки: {e}")
        poster = Image.new("RGBA", (1200, 900), (255, 0, 0, 255))

    new_poster_height = 330
    w_orig, h_orig = poster.size
    aspect_ratio = w_orig / h_orig
    new_poster_width = int(aspect_ratio * new_poster_height)
    poster = poster.resize((new_poster_width, new_poster_height), Image.LANCZOS)
    poster_x = bg_w - 60 - new_poster_width
    poster_y = bg_h - 60 - new_poster_height
    background.paste(poster, (poster_x, poster_y), poster)

    draw = ImageDraw.Draw(background)
    try:
        font_title = ImageFont.truetype(fira_font_path, 60)
        font_subtitle = ImageFont.truetype(fira_font_path, 34)
        font_text = ImageFont.truetype(fira_font_path, 48)
    except Exception as e:
        logging.error(f"Ошибка при загрузке шрифтов: {e}")
        raise

    # Загружаем изображения для календаря и часов
    calendar_img = Image.open(calendar_path).convert("RGBA").resize((48, 48), Image.LANCZOS)
    clock_img = Image.open(clock_path).convert("RGBA").resize((48, 48), Image.LANCZOS)

    # Рисуем заголовок
    title_x, title_y = 60, 60
    title_bbox = draw_text_top_left(draw, title_x, title_y, title_text, font_title, fill="white")
    
    # Рисуем подзаголовок, если он есть, с уменьшенным отступом (5 пикселей)
    if subtitle_text:
        subtitle_x = title_x
        subtitle_y = title_bbox[3] + 5  # Было 10, стало 5
        draw_text_top_left(draw, subtitle_x, subtitle_y, subtitle_text, font_subtitle, fill="white")

    # Вычисляем размеры текста для года и продолжительности
    year_bbox = draw.textbbox((0, 0), year_text, font=font_text)
    year_w, year_h = year_bbox[2] - year_bbox[0], year_bbox[3] - year_bbox[1]
    duration_bbox = draw.textbbox((0, 0), duration_text, font=font_text)
    duration_w, duration_h = duration_bbox[2] - duration_bbox[0], duration_bbox[3] - duration_bbox[1]

    # Размеры изображений (48x48)
    icon_w, icon_h = 48, 48

    # Отступы
    icon_text_gap = 10  # Отступ между иконкой и текстом
    line_gap = 10       # Отступ между строками (год и продолжительность)

    # Общая высота блока (иконка + текст)
    line1_h = max(icon_h, year_h)
    line2_h = max(icon_h, duration_h)
    total_block_h = line1_h + line_gap + line2_h

    # Центрируем блок по вертикали
    block_y = (bg_h - total_block_h) // 2

    # Рисуем год (иконка + текст)
    line1_x = 60
    y_icon1 = block_y + (line1_h - icon_h) // 2
    background.paste(calendar_img, (line1_x, y_icon1), calendar_img)
    x_year = line1_x + icon_w + icon_text_gap
    y_year = block_y + (line1_h - year_h) // 2
    draw_text_top_left(draw, x_year, y_year, year_text, font_text, fill="white")

    # Рисуем продолжительность (иконка + текст)
    line2_x = 60
    y_icon2 = block_y + line1_h + line_gap + (line2_h - icon_h) // 2
    background.paste(clock_img, (line2_x, y_icon2), clock_img)
    x_duration = line2_x + icon_w + icon_text_gap
    y_duration = block_y + line1_h + line_gap + (line2_h - duration_h) // 2
    draw_text_top_left(draw, x_duration, y_duration, duration_text, font_text, fill="white")

    output = BytesIO()
    background.save(output, format='PNG')
    output.seek(0)
    return output

if __name__ == "__main__":
    cover = make_cover(
        poster_url="https://i.ytimg.com/vi/wDmPgXhlDIg/maxresdefault.jpg",
        title_text="Курс по SQL для начинающих",
        year_text="2022",
        duration_text="15 часов",
        subtitle_text="Основы баз данных"
    )
    with open("img/output_cover.png", "wb") as f:
        f.write(cover.getvalue())
    print("Обложка сохранена: img/output_cover.png")