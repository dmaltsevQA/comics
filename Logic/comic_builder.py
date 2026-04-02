"""
Logic/comic_builder.py
───────────────────────
Сборка комикса в PDF и экспорт изображений.
"""

from __future__ import annotations

import os
from typing import List, Dict, Optional, Tuple
from PIL import Image

from .text_processor import Panel, Scene, Chapter
from .config import OUTPUT_DIR, PDF_DPI, PDF_MARGIN
from .text_renderer import render_panel_with_text, render_panel_text_only


def create_comic_page(
    panels: List[Panel],
    page_size: Tuple[int, int] = (1200, 1600),  # A4 при 150 DPI
    layout: str = "standard",
) -> Image.Image:
    """
    Создает страницу комикса из панелей.

    Args:
        panels: Список панелей для страницы
        page_size: Размер страницы (ширина, высота)
        layout: Тип раскладки

    Returns:
        PIL Image с собранной страницей
    """
    # Создаем белый фон
    page = Image.new("RGB", page_size, "white")

    if not panels:
        return page

    # Рассчитываем раскладку
    if layout == "cinematic":
        positions = _cinematic_layout(len(panels), page_size)
    elif layout == "manga":
        positions = _manga_layout(len(panels), page_size)
    else:
        positions = _standard_layout(len(panels), page_size)

    # Размещаем панели
    for i, (panel, (x, y, w, h)) in enumerate(zip(panels, positions)):
        if panel.image_path and os.path.exists(panel.image_path):
            try:
                img = Image.open(panel.image_path)
                img = img.resize((w, h), Image.LANCZOS)
                page.paste(img, (x, y))
            except Exception as e:
                print(f"[COMIC] Ошибка размещения панели: {e}")

    return page


def _standard_layout(
    num_panels: int,
    page_size: Tuple[int, int],
) -> List[Tuple[int, int, int, int]]:
    """Стандартная сетка 2x2 или 2x3."""
    width, height = page_size
    margin = PDF_MARGIN
    gap = 10

    if num_panels <= 2:
        # Одна панель на всю страницу или две горизонтально
        if num_panels == 1:
            return [(margin, margin, width - 2 * margin, height - 2 * margin)]
        h = (height - 2 * margin - gap) // 2
        return [
            (margin, margin, width - 2 * margin, h),
            (margin, margin + h + gap, width - 2 * margin, h),
        ]
    elif num_panels <= 4:
        # Сетка 2x2
        w = (width - 2 * margin - gap) // 2
        h = (height - 2 * margin - gap) // 2
        return [
            (margin, margin, w, h),
            (margin + w + gap, margin, w, h),
            (margin, margin + h + gap, w, h),
            (margin + w + gap, margin + h + gap, w, h),
        ]
    else:
        # Сетка 2x3
        w = (width - 2 * margin - gap) // 2
        h = (height - 2 * margin - 2 * gap) // 3
        positions = []
        for row in range(3):
            for col in range(2):
                x = margin + col * (w + gap)
                y = margin + row * (h + gap)
                positions.append((x, y, w, h))
        return positions[:num_panels]


def _cinematic_layout(
    num_panels: int,
    page_size: Tuple[int, int],
) -> List[Tuple[int, int, int, int]]:
    """Кинематографичная раскладка с широкими панелями."""
    width, height = page_size
    margin = PDF_MARGIN
    gap = 8

    if num_panels == 1:
        return [(margin, margin, width - 2 * margin, height - 2 * margin)]

    # Первая панель широкая, остальные поменьше
    first_h = height // 2
    remaining_h = height - first_h - 2 * margin - gap

    positions = [
        (margin, margin, width - 2 * margin, first_h - margin),
    ]

    if num_panels > 1:
        w = (width - 2 * margin - gap) // 2
        y = margin + first_h + gap
        for i in range(1, min(num_panels, 3)):
            x = margin + (i - 1) * (w + gap)
            positions.append((x, y, w, remaining_h))

    return positions[:num_panels]


def _manga_layout(
    num_panels: int,
    page_size: Tuple[int, int],
) -> List[Tuple[int, int, int, int]]:
    """Раскладка в стиле манги (справа налево)."""
    width, height = page_size
    margin = PDF_MARGIN
    gap = 8

    if num_panels <= 3:
        h = (height - 2 * margin - (num_panels - 1) * gap) // num_panels
        positions = []
        for i in range(num_panels):
            y = margin + i * (h + gap)
            positions.append((margin, y, width - 2 * margin, h))
        return positions
    else:
        # Сложная раскладка манги
        positions = []
        # Большая панель справа
        positions.append((width // 2, margin, width // 2 - margin, height // 2 - margin))
        # Маленькие слева
        small_h = (height // 2 - 2 * margin - gap) // 2
        positions.append((margin, margin, width // 2 - 2 * margin - gap, small_h))
        positions.append((margin, margin + small_h + gap, width // 2 - 2 * margin - gap, small_h))
        # Нижняя широкая
        positions.append((margin, height // 2 + gap, width - 2 * margin, height // 2 - 2 * margin - gap))
        return positions[:num_panels]


def export_pages_as_images(
    chapters: List[Chapter],
    output_dir: str = OUTPUT_DIR,
    layout: str = "standard",
    page_size: Tuple[int, int] = (1200, 1600),
) -> List[str]:
    """
    Экспортирует страницы комикса как отдельные изображения.

    Returns:
        Список путей к файлам
    """
    os.makedirs(output_dir, exist_ok=True)
    page_files = []
    page_num = 0

    for chapter in chapters:
        for scene in chapter.scenes:
            # Группируем панели по страницам (4 панели на страницу)
            panels_per_page = 4
            for i in range(0, len(scene.panels), panels_per_page):
                page_panels = scene.panels[i:i + panels_per_page]
                page = create_comic_page(page_panels, page_size, layout)

                page_num += 1
                filename = f"page_{page_num:04d}.png"
                filepath = os.path.join(output_dir, filename)
                page.save(filepath, "PNG")
                page_files.append(filepath)
                print(f"[COMIC] Страница {page_num} сохранена: {filepath}")

    return page_files


def export_as_pdf(
    chapters: List[Chapter],
    output_path: str,
    layout: str = "standard",
    page_size: Tuple[int, int] = (1200, 1600),
) -> bool:
    """
    Экспортирует комикс в PDF файл.

    Args:
        chapters: Список глав
        output_path: Путь для сохранения PDF
        layout: Тип раскладки
        page_size: Размер страницы

    Returns:
        True если успешно
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm,
        )

        story = []
        styles = getSampleStyleSheet()

        for chapter in chapters:
            # Заголовок главы
            story.append(Paragraph(
                f"<b>{chapter.title}</b>",
                styles["Title"]
            ))
            story.append(Spacer(1, 10*mm))

            for scene in chapter.scenes:
                # Группируем панели по страницам
                panels_per_page = 4
                for i in range(0, len(scene.panels), panels_per_page):
                    page_panels = scene.panels[i:i + panels_per_page]

                    # Создаем страницу
                    page = create_comic_page(page_panels, page_size, layout)

                    # Сохраняем временно
                    temp_path = os.path.join(output_path.replace(".pdf", "_temp.png"))
                    page.save(temp_path, "PNG")

                    # Добавляем в PDF
                    img = Image(temp_path, width=170*mm, height=227*mm)
                    story.append(img)
                    story.append(Spacer(1, 5*mm))

                    # Удаляем временный файл
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

        doc.build(story)
        print(f"[COMIC] PDF сохранен: {output_path}")
        return True

    except ImportError:
        print("[COMIC] reportlab не установлен. pip install reportlab")
        return False
    except Exception as e:
        print(f"[COMIC] Ошибка создания PDF: {e}")
        return False


def export_all_panels_with_text(
    chapters: List[Chapter],
    output_dir: str = OUTPUT_DIR,
    bubble_type: str = "speech",
    add_captions: bool = True,
) -> List[str]:
    """
    Экспортирует все панели как отдельные изображения с текстом.

    Returns:
        Список путей к файлам
    """
    os.makedirs(output_dir, exist_ok=True)
    files = []

    for chapter in chapters:
        chapter_dir = os.path.join(output_dir, f"chapter_{chapter.index + 1}")
        os.makedirs(chapter_dir, exist_ok=True)

        for scene in chapter.scenes:
            for panel in scene.panels:
                if panel.image_path and os.path.exists(panel.image_path):
                    img = Image.open(panel.image_path)

                    # Добавляем текст
                    if panel.text:
                        img = render_panel_with_text(
                            img,
                            panel.text,
                            description=panel.description[:80] if add_captions else "",
                            bubble_type=bubble_type,
                        )

                    filename = f"panel_{panel.index:04d}_text.png"
                    dest_path = os.path.join(chapter_dir, filename)
                    img.save(dest_path, "PNG")
                    files.append(dest_path)

    return files


def export_all_panels_as_individual_images(
    chapters: List[Chapter],
    output_dir: str = OUTPUT_DIR,
) -> List[str]:
    """
    Экспортирует все панели как отдельные изображения.

    Returns:
        Список путей к файлам
    """
    os.makedirs(output_dir, exist_ok=True)
    files = []

    for chapter in chapters:
        chapter_dir = os.path.join(output_dir, f"chapter_{chapter.index + 1}")
        os.makedirs(chapter_dir, exist_ok=True)

        for scene in chapter.scenes:
            for panel in scene.panels:
                if panel.image_path and os.path.exists(panel.image_path):
                    filename = f"panel_{panel.index:04d}.png"
                    dest_path = os.path.join(chapter_dir, filename)

                    # Копируем файл
                    img = Image.open(panel.image_path)
                    img.save(dest_path, "PNG")
                    files.append(dest_path)

    return files


def export_pages_with_text(
    chapters: List[Chapter],
    output_dir: str = OUTPUT_DIR,
    layout: str = "standard",
    page_size: Tuple[int, int] = (1200, 1600),
    bubble_type: str = "speech",
    add_captions: bool = True,
) -> List[str]:
    """
    Экспортирует страницы комикса с добавленным текстом (речевые пузыри).

    Returns:
        Список путей к файлам
    """
    os.makedirs(output_dir, exist_ok=True)
    page_files = []
    page_num = 0

    for chapter in chapters:
        for scene in chapter.scenes:
            # Группируем панели по страницам (4 панели на страницу)
            panels_per_page = 4
            for i in range(0, len(scene.panels), panels_per_page):
                page_panels = scene.panels[i:i + panels_per_page]

                # Создаем страницу с текстом
                page = create_comic_page_with_text(
                    page_panels, page_size, layout, bubble_type, add_captions
                )

                page_num += 1
                filename = f"page_{page_num:04d}_text.png"
                filepath = os.path.join(output_dir, filename)
                page.save(filepath, "PNG")
                page_files.append(filepath)
                print(f"[COMIC] Страница с текстом {page_num} сохранена: {filepath}")

    return page_files


def create_comic_page_with_text(
    panels: List[Panel],
    page_size: Tuple[int, int] = (1200, 1600),
    layout: str = "standard",
    bubble_type: str = "speech",
    add_captions: bool = True,
) -> Image.Image:
    """
    Создает страницу комикса из панелей с добавленным текстом.
    """
    # Создаем белый фон
    page = Image.new("RGB", page_size, "white")

    if not panels:
        return page

    # Рассчитываем раскладку
    if layout == "cinematic":
        positions = _cinematic_layout(len(panels), page_size)
    elif layout == "manga":
        positions = _manga_layout(len(panels), page_size)
    else:
        positions = _standard_layout(len(panels), page_size)

    # Размещаем панели с текстом
    for i, (panel, (x, y, w, h)) in enumerate(zip(panels, positions)):
        if panel.image_path and os.path.exists(panel.image_path):
            try:
                img = Image.open(panel.image_path)

                # Добавляем текст на панель
                if panel.text:
                    img = render_panel_with_text(
                        img,
                        panel.text,
                        description=panel.description[:80] if add_captions else "",
                        bubble_type=bubble_type,
                        caption_position="top",
                    )

                img = img.resize((w, h), Image.LANCZOS)
                page.paste(img, (x, y))
            except Exception as e:
                print(f"[COMIC] Ошибка размещения панели: {e}")

    return page


def get_comic_stats(chapters: List[Chapter]) -> Dict:
    """Статистика комикса."""
    total_panels = 0
    panels_with_images = 0
    panels_with_text = 0

    for chapter in chapters:
        for scene in chapter.scenes:
            for panel in scene.panels:
                total_panels += 1
                if panel.image_path and os.path.exists(panel.image_path):
                    panels_with_images += 1
                if panel.text:
                    panels_with_text += 1

    return {
        "chapters": len(chapters),
        "total_panels": total_panels,
        "panels_with_images": panels_with_images,
        "panels_with_text": panels_with_text,
        "completion_percent": round(panels_with_images / max(total_panels, 1) * 100, 1),
    }