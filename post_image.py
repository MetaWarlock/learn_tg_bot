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
    emoji_font_path = os.path.join(script_dir, "fonts/EmojiOneColor.otf")

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
    font_title = ImageFont.truetype(fira_font_path, 60)
    font_subtitle = ImageFont.truetype(fira_font_path, 30)
    font_text = ImageFont.truetype(fira_font_path, 48)
    font_emoji = ImageFont.truetype(emoji_font_path, 48)

    # Рисуем заголовок
    title_x, title_y = 60, 60
    title_bbox = draw_text_top_left(draw, title_x, title_y, title_text, font_title, fill="white")
    
    # Рисуем подзаголовок, если он есть
    if subtitle_text:
        subtitle_x = title_x
        subtitle_y = title_bbox[3] + 10
        draw_text_top_left(draw, subtitle_x, subtitle_y, subtitle_text, font_subtitle, fill="white")

    # Рисуем год (с иконкой)
    line_1_x = 60
    line_1_y = poster_y
    left_icon, top_icon, right_icon, bottom_icon = draw.textbbox((0, 0), "📅", font=font_emoji)
    icon_w, icon_h = right_icon - left_icon, bottom_icon - top_icon
    left_year, top_year, right_year, bottom_year = draw.textbbox((0, 0), year_text, font=font_text)
    year_w, year_h = right_year - left_year, bottom_year - top_year
    max_line1_h = max(icon_h, year_h)
    y_icon = line_1_y + (max_line1_h - icon_h) // 2
    y_year = line_1_y + (max_line1_h - year_h) // 2
    draw_text_top_left(draw, line_1_x, y_icon, "📅", font=font_emoji)
    x_year = line_1_x + icon_w + 10
    draw_text_top_left(draw, x_year, y_year, year_text, font=font_text)

    # Рисуем продолжительность (с иконкой)
    line_2_x = 60
    line_2_y = line_1_y + max_line1_h + 10
    left_clock, top_clock, right_clock, bottom_clock = draw.textbbox((0, 0), "⏰", font=font_emoji)
    clock_w, clock_h = right_clock - left_clock, bottom_clock - top_clock
    left_dur, top_dur, right_dur, bottom_dur = draw.textbbox((0, 0), duration_text, font=font_text)
    dur_w, dur_h = right_dur - left_dur, bottom_dur - top_dur
    max_line2_h = max(clock_h, dur_h)
    y_clock = line_2_y + (max_line2_h - clock_h) // 2
    y_dur = line_2_y + (max_line2_h - dur_h) // 2
    draw_text_top_left(draw, line_2_x, y_clock, "⏰", font=font_emoji)
    x_dur = line_2_x + clock_w + 10
    draw_text_top_left(draw, x_dur, y_dur, duration_text, font=font_text)

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
