import os
import re
import math
from datetime import datetime, timezone
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

def extract_playlist_id(url):
    """Извлекаем ID плейлиста из ссылки"""
    query = urlparse(url).query
    params = parse_qs(query)
    return params.get('list', [None])[0]

def parse_duration(duration):
    """Парсинг ISO-8601 продолжительности (PT#H#M#S) в секунды"""
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

def get_playlist_info(playlist_url):
    """Получение данных плейлиста с дополнительной информацией об обложке"""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("API ключ не найден в .env файле")
    
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        raise ValueError("Некорректная ссылка на плейлист")
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    # Получение метаданных плейлиста
    playlist = youtube.playlists().list(
        part='snippet',
        id=playlist_id
    ).execute()['items'][0]['snippet']
    
    videos = []
    next_page_token = None
    total_seconds = 0
    latest_date = datetime.min.replace(tzinfo=timezone.utc)
    cover_url = None  # Обложка берётся из первого видео
    
    while True:
        items = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        
        video_ids = [i['snippet']['resourceId']['videoId'] for i in items['items']]
        
        # Получение деталей видео
        details = youtube.videos().list(
            part='contentDetails,snippet',
            id=','.join(video_ids)
        ).execute()
        
        for item, detail in zip(items['items'], details['items']):
            published = datetime.fromisoformat(
                item['snippet']['publishedAt'].replace('Z', '+00:00')
            )
            duration_sec = parse_duration(detail['contentDetails']['duration'])
            
            videos.append({
                'title': item['snippet']['title'],
                'published': published,
                'duration': duration_sec
            })
            
            total_seconds += duration_sec
            if published > latest_date:
                latest_date = published
            
            # Если обложка еще не установлена, берём её из первого видео
            if cover_url is None:
                cover_url = get_max_thumbnail(detail['snippet']['thumbnails'])
        
        next_page_token = items.get('nextPageToken')
        if not next_page_token:
            break
    
    course_year = latest_date.year if latest_date != datetime.min.replace(tzinfo=timezone.utc) else None
    total_hours = math.ceil(total_seconds / 3600)
    
    return {
        'title': playlist['title'],
        'description': playlist.get('description', ''),
        'course_year': course_year,
        'total_hours': total_hours,
        'cover_url': cover_url,
        'videos': videos
    }
