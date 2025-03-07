import os
import re
import math
from datetime import datetime, timezone
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

def extract_video_id(url):
    """Извлекаем ID видео из разных форматов URL"""
    parsed = urlparse(url)
    if 'youtu.be' in parsed.netloc:
        # Короткий формат: youtu.be/ID
        return parsed.path.lstrip('/')
    elif 'youtube.com' in parsed.netloc:
        # Формат: youtube.com/watch?v=ID
        query = parsed.query
        params = parse_qs(query)
        return params.get('v', [None])[0]
    return None

def parse_duration(duration):
    """Парсинг ISO-8601 продолжительности видео в секунды"""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0
    return hours * 3600 + minutes * 60 + seconds

def get_max_thumbnail(thumbnails):
    """Выбираем обложку с максимально доступным качеством"""
    for quality in ["maxres", "standard", "high", "medium", "default"]:
        if quality in thumbnails:
            return thumbnails[quality]["url"]
    return None

def get_video_info(video_url):
    """Получение информации об отдельном видео"""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("API ключ не найден в .env файле")
    
    video_id = extract_video_id(video_url)
    if not video_id:
        raise ValueError("Некорректная ссылка на видео")
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    response = youtube.videos().list(
        part='contentDetails,snippet',
        id=video_id
    ).execute()
    
    if not response['items']:
        raise ValueError("Видео не найдено")
    
    detail = response['items'][0]
    
    published = datetime.fromisoformat(
        detail['snippet']['publishedAt'].replace('Z', '+00:00')
    )
    
    duration_sec = parse_duration(detail['contentDetails']['duration'])
    total_hours = math.ceil(duration_sec / 3600)
    cover_url = get_max_thumbnail(detail['snippet']['thumbnails'])
    
    return {
        'title': detail['snippet']['title'],
        'course_year': published.year,
        'total_hours': total_hours,
        'description': detail['snippet'].get('description', ''),
        'cover_url': cover_url
    }
