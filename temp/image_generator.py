import os
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def draw_text_top_left(draw, x, y, text, font, fill="white"):
    bbox = draw.textbbox((x, y), text, font=font)
    draw.text((x, y), text, font=font, fill=fill, anchor="la")
    return bbox

def make_cover(poster_url: str, title_text: str, year_text: str, duration_text: str) -> BytesIO:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    background_path = os.path.join(script_dir, "red_background.png")
    fira_font_path = os.path.join(script_dir, "FiraSansExtraCondensed-Regular.ttf")
    emoji_font_path = os.path.join(script_dir, "EmojiOneColor.otf")

    background = Image.open(background_path).convert("RGB")
    bg_w, bg_h = background.size

    poster = None
    if poster_url:
        try:
            response = requests.get(poster_url)
            response.raise_for_status()
            poster = Image.open(BytesIO(response.content)).convert("RGBA")
            new_poster_height = 330
            aspect_ratio = poster.width / poster.height
            new_poster_width = int(new_poster_height * aspect_ratio)
            poster = poster.resize((new_poster_width, new_poster_height), Image.LANCZOS)
            poster_x = bg_w - 60 - new_poster_width
            poster_y = bg_h - 60 - new_poster_height
            background.paste(poster, (poster_x, poster_y), poster)
        except Exception as e:
            print(f"Ошибка загрузки обложки: {e}")

    draw = ImageDraw.Draw(background)
    font_title = ImageFont.truetype(fira_font_path, 60)
    font_text = ImageFont.truetype(fira_font_path, 48)
    font_emoji = ImageFont.truetype(emoji_font_path, 48)

    draw_text_top_left(draw, 60, 60, title_text, font_title)

    line_y = bg_h - 60 - 330 - 20 if poster else bg_h - 100

    icon_bbox = draw_text_top_left(draw, 60, line_y, "📅", font_emoji)
    draw_text_top_left(draw, icon_bbox[2] + 10, line_y, year_text, font_text)

    clock_bbox = draw_text_top_left(draw, 60, line_y + 60, "⏳", font_emoji)
    draw_text_top_left(draw, clock_bbox[2] + 10, line_y + 60, duration_text, font_text)

    img_byte_arr = BytesIO()
    background.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr