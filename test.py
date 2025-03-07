from PIL import Image, ImageDraw, ImageFont

# Создаём тестовое изображение
test_img = Image.new("RGBA", (200, 100), (255, 255, 255, 255))  # Белый фон
draw = ImageDraw.Draw(test_img)

# Загружаем шрифт
try:
    font_emoji = ImageFont.truetype("fonts/NotoColorEmoji.ttf", 24)
    draw.text((10, 10), "📅", font=font_emoji, embedded_color=True)  # Рисуем эмодзи с цветом
    test_img.save("img/test_emoji.png")
    print("Тестовая картинка сохранена: test_emoji.png")
except Exception as e:
    print(f"Ошибка: {e}")