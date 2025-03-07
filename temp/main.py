from youtube_parser import get_playlist_info, extract_playlist_id
from video_parser import get_video_info, extract_video_id
from post_image import make_cover

def main():
    url = input("Введите URL YouTube плейлиста или видео: ").strip()
    
    try:
        if "/playlist" in url:
            data = get_playlist_info(url)
            clean_link = f"https://www.youtube.com/playlist?list={extract_playlist_id(url)}"
            print(f"\n📼 Название плейлиста: {data['title']}")
            if data['course_year']:
                print(f"📅 Год курса: {data['course_year']}")
            print(f"📝 Описание: {data['description'] or 'Описание отсутствует'}")
            print(f"⏳ Продолжительность курса: {data['total_hours']} часов")
            print(f"🖼 Ссылка на обложку: {data['cover_url'] or 'Отсутствует'}")
            print(f"🔗 Ссылка на курс: {clean_link}")
            
            print(f"\n🎬 Всего видео: {len(data['videos'])}")
            for idx, video in enumerate(data['videos'], 1):
                print(f"\n{idx}. {video['title']}")
                print(f"   📅 Дата публикации: {video['published'].strftime('%Y-%m-%d')}")
                print(f"   ⏱ Продолжительность: {video['duration'] // 60} мин")
            
            # Создаем и сохраняем обложку
            cover_image = make_cover(
                data['cover_url'],
                data['title'],
                str(data['course_year']) if data['course_year'] else "Неизвестно",
                f"{data['total_hours']} часов"
            )
            with open("output_cover.png", "wb") as f:
                f.write(cover_image.getvalue())
            print("🖼 Обложка сохранена в output_cover.png")
            
        elif "/watch" in url or "youtu.be" in url:
            data = get_video_info(url)
            clean_link = f"https://youtu.be/{extract_video_id(url)}"
            print(f"\n📼 Название курса: {data['title']}")
            print(f"📅 Год курса: {data['course_year']}")
            print(f"⏳ Продолжительность курса: {data['total_hours']} часов")
            print(f"📝 Описание: {data['description'] or 'Описание отсутствует'}")
            print(f"🖼 Ссылка на обложку: {data['cover_url'] or 'Отсутствует'}")
            print(f"🔗 Ссылка на курс: {clean_link}")
            
            # Создаем и сохраняем обложку
            cover_image = make_cover(
                data['cover_url'],
                data['title'],
                str(data['course_year']),
                f"{data['total_hours']} часов"
            )
            with open("output_cover.png", "wb") as f:
                f.write(cover_image.getvalue())
            print("🖼 Обложка сохранена в output_cover.png")
            
        else:
            print("⛔ Неизвестный формат ссылки")
    except Exception as e:
        print(f"⛔ Ошибка: {str(e)}")

if __name__ == "__main__":
    main()