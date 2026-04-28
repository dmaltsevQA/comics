"""
Logic/config.py — Конфигурация Comics Generator
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

for d in (OUTPUT_DIR, UPLOAD_DIR, TEMP_DIR):
    os.makedirs(d, exist_ok=True)

# Google Imagen 3 API (облачная генерация через RouterAI)
ROUTERAI_API_KEY = os.getenv("ROUTERAI_API_KEY", "")
ROUTERAI_BASE_URL = os.getenv("ROUTERAI_BASE_URL", "https://api.routerai.ru")
IMAGEN_MODEL_NAME = os.getenv("IMAGEN_MODEL_NAME", "google/imagen-3")

# Параметры генерации
DEFAULT_ASPECT_RATIO = "1024*1024"
DEFAULT_GUIDANCE_SCALE = 4.0
DEFAULT_STEPS = 30
DEFAULT_SEED = -1  # -1 = случайный

# Стили комиксов
COMIC_STYLES = {
    "marvel": {
        "name": "Marvel/DC",
        "description": "Яркий американский комикс",
        "style_prompt": "comic book style, Marvel style, bold lines, vibrant colors, dynamic composition",
        "negative_prompt": "photorealistic, 3d render, blurry, low quality",
    },
    "manga": {
        "name": "Манга",
        "description": "Японский стиль манги",
        "style_prompt": "manga style, black and white, clean lineart, screentones, Japanese comic style",
        "negative_prompt": "color, photorealistic, 3d render, blurry",
    },
    "european": {
        "name": "Европейский",
        "description": "Европейский комикс (bande dessinée)",
        "style_prompt": "European comic style, ligne claire, detailed backgrounds, Franco-Belgian style",
        "negative_prompt": "manga, anime, photorealistic, 3d render",
    },
    "webtoon": {
        "name": "Вебтун",
        "description": "Корейский вебтун",
        "style_prompt": "webtoon style, vertical scroll, digital art, Korean manhwa style, full color",
        "negative_prompt": "traditional comic, manga, photorealistic",
    },
    "minimalist": {
        "name": "Минимализм",
        "description": "Простой минималистичный стиль",
        "style_prompt": "minimalist comic, simple lines, limited color palette, clean design",
        "negative_prompt": "complex, detailed, photorealistic, 3d render",
    },
    "noir": {
        "name": "Нуар",
        "description": "Темный нуарный стиль",
        "style_prompt": "comic noir style, high contrast, black and white, dramatic shadows, film noir atmosphere",
        "negative_prompt": "colorful, bright, cheerful, photorealistic",
    },
}

# Параметры панелей
PANEL_LAYOUTS = {
    "standard": {
        "name": "Стандартная сетка",
        "description": "Классическая сетка 2x2 или 3x2",
        "panels_per_page": 4,
    },
    "cinematic": {
        "name": "Кинематографичная",
        "description": "Широкие панели как в кино",
        "panels_per_page": 2,
    },
    "dynamic": {
        "name": "Динамичная",
        "description": "Разные размеры панелей",
        "panels_per_page": 5,
    },
    "manga": {
        "name": "Манга",
        "description": "Стиль манги с разными размерами",
        "panels_per_page": 6,
    },
}

# Параметры текста
MAX_CHARS_PER_PANEL = 200  # Максимум символов на панель
MAX_PANELS_PER_CHAPTER = 20  # Максимум панелей на главу

# Параметры PDF
PDF_PAGE_SIZE = "A4"  # A4, Letter, Custom
PDF_DPI = 150
PDF_MARGIN = 20  # пиксели