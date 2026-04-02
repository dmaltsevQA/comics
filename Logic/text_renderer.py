"""
Logic/text_renderer.py
───────────────────────
Рендеринг текста (подписей, диалогов) поверх изображений панелей комикса.

SD1.5 и SDXL не умеют генерировать текст, поэтому текст добавляется
отдельно поверх готовых изображений с помощью PIL.
"""

from __future__ import annotations

import os
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont


# ─── Настройки текста ────────────────────────────────────────────────────────

# Размеры и позиции элементов
SPEECH_BUBBLE = {
    "padding": 10,         # Отступ текста от краёв пузыря
    "corner_radius": 15,   # Радиус скругления углов
    "border_width": 2,     # Толщина обводки пузыря
    "tail_length": 20,     # Длина "хвостика" пузыря
    "tail_width": 15,      # Ширина основания хвостика
}

# Цвета
COLORS = {
    "bubble_fill": (255, 255, 255),       # Белый фон пузыря
    "bubble_border": (0, 0, 0),           # Чёрная обводка
    "text_color": (0, 0, 0),              # Чёрный текст
    "caption_bg": (255, 255, 200, 200),   # Полупрозрачный жёлтый для подписей
    "caption_text": (0, 0, 0),            # Чёрный текст подписей
    "thought_bg": (240, 240, 240),        # Светло-серый для мыслей
}

# Шрифты (будем искать системные)
DEFAULT_FONT_SIZE = 16
CAPTION_FONT_SIZE = 14


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """
    Получает шрифт для рендеринга текста.
    Пробует системные шрифты, fallback на default.
    """
    # Пути к системным шрифтам Windows
    font_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Arial.ttf",
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/comic.ttf",      # Comic Sans - идеально для комиксов!
        "C:/Windows/Fonts/comicbd.ttf",    # Comic Sans Bold
    ]

    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    # Fallback на default шрифт
    return ImageFont.load_default()


def wrap_text(text: str, max_width: int, font: ImageFont.FreeTypeFont) -> list[str]:
    """
    Разбивает текст на строки по максимальной ширине.
    """
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        text_width = bbox[2] - bbox[0] if bbox else len(test_line) * font.size

        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines if lines else [text]


def draw_rounded_rectangle(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int, int, int],
    radius: int,
    fill: Optional[tuple] = None,
    outline: Optional[tuple] = None,
    width: int = 1,
) -> None:
    """
    Рисует прямоугольник со скруглёнными углами.
    """
    x0, y0, x1, y1 = xy

    # Основная область
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)

    # Углы (четверти круга)
    draw.pieslice([x0, y0, x0 + 2 * radius, y0 + 2 * radius], 180, 270, fill=fill)
    draw.pieslice([x1 - 2 * radius, y0, x1, y0 + 2 * radius], 270, 360, fill=fill)
    draw.pieslice([x0, y1 - 2 * radius, x0 + 2 * radius, y1], 90, 180, fill=fill)
    draw.pieslice([x1 - 2 * radius, y1 - 2 * radius, x1, y1], 0, 90, fill=fill)

    # Обводка
    if outline:
        # Верх и низ
        draw.line([x0 + radius, y0, x1 - radius, y0], fill=outline, width=width)
        draw.line([x0 + radius, y1, x1 - radius, y1], fill=outline, width=width)
        # Лево и право
        draw.line([x0, y0 + radius, x0, y1 - radius], fill=outline, width=width)
        draw.line([x1, y0 + radius, x1, y1 - radius], fill=outline, width=width)
        # Углы
        draw.arc([x0, y0, x0 + 2 * radius, y0 + 2 * radius], 180, 270, fill=outline, width=width)
        draw.arc([x1 - 2 * radius, y0, x1, y0 + 2 * radius], 270, 360, fill=outline, width=width)
        draw.arc([x0, y1 - 2 * radius, x0 + 2 * radius, y1], 90, 180, fill=outline, width=width)
        draw.arc([x1 - 2 * radius, y1 - 2 * radius, x1, y1], 0, 90, fill=outline, width=width)


def add_speech_bubble(
    image: Image.Image,
    text: str,
    position: Tuple[int, int] = None,
    bubble_type: str = "speech",  # speech, thought, caption
) -> Image.Image:
    """
    Добавляет речевой пузырь с текстом на изображение.

    Args:
        image: Исходное изображение панели
        text: Текст для отображения
        position: Позиция (x, y) или None для авто
        bubble_type: Тип пузыря (speech, thought, caption)

    Returns:
        Изображение с добавленным пузырём
    """
    if not text or not text.strip():
        return image

    # Создаём копию для редактирования
    result = image.convert("RGBA")
    txt_layer = Image.new("RGBA", result.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    width, height = result.size

    # Настройки шрифта
    font = get_font(DEFAULT_FONT_SIZE)
    padding = SPEECH_BUBBLE["padding"]

    # Разбиваем текст на строки
    max_bubble_width = width // 2  # Максимальная ширина пузыря
    lines = wrap_text(text, max_bubble_width - 2 * padding, font)

    # Рассчитываем размер пузыря
    line_height = font.size + 4
    bubble_height = len(lines) * line_height + 2 * padding
    bubble_width = max_bubble_width

    # Позиция пузыря
    if position:
        bx, by = position
    else:
        # По умолчанию - верхняя часть панели
        bx = (width - bubble_width) // 2
        by = 20

    # Ограничиваем позицию
    bx = max(0, min(bx, width - bubble_width))
    by = max(0, min(by, height - bubble_height - 30))

    # Цвета в зависимости от типа
    if bubble_type == "speech":
        fill_color = COLORS["bubble_fill"] + (230,)
        border_color = COLORS["bubble_border"]
    elif bubble_type == "thought":
        fill_color = COLORS["thought_bg"] + (200,)
        border_color = (150, 150, 150)
    else:  # caption
        fill_color = COLORS["caption_bg"]
        border_color = COLORS["bubble_border"]

    # Рисуем пузырь
    bubble_rect = [bx, by, bx + bubble_width, by + bubble_height]
    draw_rounded_rectangle(
        draw,
        bubble_rect,
        radius=SPEECH_BUBBLE["corner_radius"],
        fill=fill_color,
        outline=border_color,
        width=SPEECH_BUBBLE["border_width"],
    )

    # Рисуем текст
    text_color = COLORS["text_color"]
    y_offset = by + padding
    for line in lines:
        # Центрируем текст
        bbox = font.getbbox(line)
        text_w = bbox[2] - bbox[0] if bbox else len(line) * font.size
        x_offset = bx + (bubble_width - text_w) // 2
        draw.text((x_offset, y_offset), line, fill=text_color, font=font)
        y_offset += line_height

    # Накладываем слой с пузырём
    result = Image.alpha_composite(result, txt_layer)
    return result.convert("RGB")


def add_caption_bar(
    image: Image.Image,
    text: str,
    position: str = "top",  # top, bottom
) -> Image.Image:
    """
    Добавляет полосу подписи (как в комиксах - narration box).

    Args:
        image: Исходное изображение
        text: Текст подписи
        position: Позиция (top или bottom)

    Returns:
        Изображение с подписью
    """
    if not text or not text.strip():
        return image

    result = image.convert("RGBA")
    width, height = result.size

    # Создаём слой для подписи
    bar_height = 40
    if position == "bottom":
        bar_y = height - bar_height
    else:
        bar_y = 0

    # Рисуем полосу
    txt_layer = Image.new("RGBA", result.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    # Жёлтый фон подписи
    bg_color = (255, 255, 200, 220)
    draw.rectangle([0, bar_y, width, bar_y + bar_height], fill=bg_color)

    # Чёрная рамка
    border_color = (0, 0, 0)
    draw.rectangle([0, bar_y, width, bar_y + bar_height], outline=border_color, width=2)

    # Текст
    font = get_font(CAPTION_FONT_SIZE, bold=True)
    text_color = (0, 0, 0)

    # Разбиваем на строки если нужно
    lines = wrap_text(text, width - 20, font)
    y_offset = bar_y + 5
    for line in lines[:2]:  # Максимум 2 строки
        bbox = font.getbbox(line)
        text_w = bbox[2] - bbox[0] if bbox else len(line) * font.size
        x_offset = (width - text_w) // 2
        draw.text((x_offset, y_offset), line, fill=text_color, font=font)
        y_offset += font.size + 2

    result = Image.alpha_composite(result, txt_layer)
    return result.convert("RGB")


def render_panel_with_text(
    image: Image.Image,
    panel_text: str,
    description: str = "",
    bubble_type: str = "speech",
    caption_position: str = "top",
) -> Image.Image:
    """
    Полный рендеринг панели с текстом.

    Args:
        image: Изображение панели
        panel_text: Текст диалога/мысли
        description: Описание сцены (для подписи)
        bubble_type: Тип пузыря (speech, thought, caption)
        caption_position: Позиция подписи

    Returns:
        Готовое изображение панели с текстом
    """
    result = image

    # Добавляем подпись описания если есть
    if description and caption_position:
        result = add_caption_bar(result, description[:100], caption_position)

    # Добавляем речевой пузырь если есть текст
    if panel_text:
        result = add_speech_bubble(result, panel_text, bubble_type=bubble_type)

    return result


def render_panel_text_only(
    image: Image.Image,
    text: str,
    max_width_ratio: float = 0.8,
) -> Image.Image:
    """
    Простой рендеринг текста поверх изображения (без пузыря).
    Используется для подписей внизу панели.

    Args:
        image: Изображение панели
        text: Текст для отображения
        max_width_ratio: Максимальная ширина текста относительно изображения

    Returns:
        Изображение с текстом
    """
    if not text or not text.strip():
        return image

    result = image.convert("RGBA")
    width, height = result.size

    # Создаём полупрозрачный фон для текста внизу
    txt_layer = Image.new("RGBA", result.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    font = get_font(DEFAULT_FONT_SIZE)
    padding = 10

    # Разбиваем текст на строки
    max_text_width = int(width * max_width_ratio)
    lines = wrap_text(text, max_text_width, font)

    # Высота текстовой области
    line_height = font.size + 4
    text_height = len(lines) * line_height + 2 * padding

    # Позиция - внизу панели
    text_y = height - text_height - 10
    text_x = (width - max_text_width) // 2

    # Фон под текст
    bg_color = (0, 0, 0, 150)  # Полупрозрачный чёрный
    draw.rectangle(
        [text_x - padding, text_y - padding,
         text_x + max_text_width + padding, text_y + text_height + padding],
        fill=bg_color,
    )

    # Текст
    text_color = (255, 255, 255)  # Белый текст
    y_offset = text_y
    for line in lines:
        bbox = font.getbbox(line)
        text_w = bbox[2] - bbox[0] if bbox else len(line) * font.size
        x_offset = text_x + (max_text_width - text_w) // 2
        draw.text((x_offset, y_offset), line, fill=text_color, font=font)
        y_offset += line_height

    result = Image.alpha_composite(result, txt_layer)
    return result.convert("RGB")