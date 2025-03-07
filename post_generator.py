import re
from post_image import make_cover
from chatgpt import generate_post

def generate_post_text(course_info):
    """Генерирует текст поста с помощью ChatGPT."""
    post_text = generate_post(course_info)
    if not post_text:
        raise ValueError("Не удалось получить пост от ChatGPT (post_text == None)")
    post_text = post_text.replace("```", "")
    return post_text

def extract_title_and_subtitle(post_text):
    """Извлекает заголовок и подзаголовок из текста поста."""
    lines = post_text.split('\n')
    title_text = None
    subtitle_text = None
    title_pattern = re.compile(r'<b>(.*?)</b>', re.IGNORECASE)
    for i, line in enumerate(lines):
        match = title_pattern.search(line)
        if match:
            title_text = match.group(1).strip()
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line and not next_line.startswith(('🗓', '⏰', '🔹', '♦️', '<a')):
                    subtitle_text = next_line
            break
    if title_text and len(title_text) > 30:
        words = title_text.split()
        title_text = " ".join(words[:3])
        subtitle_text = " ".join(words[3:]) if not subtitle_text else subtitle_text
    return title_text, subtitle_text

def generate_cover(poster_url, title_text, year_text, duration_text, subtitle_text):
    """Генерирует обложку для поста."""
    cover_image = make_cover(
        poster_url,
        title_text or "Без названия",
        year_text,
        duration_text,
        subtitle_text
    )
    if not cover_image:
        raise ValueError("make_cover вернула None или произошла ошибка при создании обложки.")
    return cover_image