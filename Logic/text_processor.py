"""
Logic/text_processor.py
────────────────────────
Обработка текста книги: загрузка, очистка, разбиение на сцены и панели.
"""

from __future__ import annotations

import os
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class Panel:
    """Одна панель комикса."""
    index: int
    text: str  # Текст для отображения на панели
    description: str  # Описание сцены для генерации изображения
    characters: List[str] = field(default_factory=list)
    location: str = ""
    mood: str = "neutral"
    image_path: Optional[str] = None


@dataclass
class Scene:
    """Сцена (группа панелей)."""
    index: int
    title: str
    panels: List[Panel] = field(default_factory=list)
    summary: str = ""


@dataclass
class Chapter:
    """Глава комикса."""
    index: int
    title: str
    scenes: List[Scene] = field(default_factory=list)
    summary: str = ""


# ─── Загрузка текста ──────────────────────────────────────────────────────────

def load_text_file(path: str) -> str:
    """Загружает TXT-файл с автоопределением кодировки."""
    for enc in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    raise ValueError(f"Не удалось прочитать файл: {path}")


def load_docx_file(path: str) -> str:
    """Загружает DOCX-файл."""
    try:
        from docx import Document
        doc = Document(path)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        raise ImportError("Установите python-docx: pip install python-docx")


def load_book(path: str) -> str:
    """Автоматически выбирает загрузчик по расширению файла."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return load_docx_file(path)
    return load_text_file(path)


# ─── Очистка текста ───────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Очистка текста от мусора."""
    # Убираем HTML-теги
    text = re.sub(r"<[^>]+>", "", text)
    # Убираем markdown-форматирование
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    # Множественные пробелы → один
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Множественные переводы строк → двойной
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Убираем строки-разделители
    text = re.sub(r"^[-=*#]{3,}\s*$", "", text, flags=re.MULTILINE)
    return text.strip()


# ─── Разбиение на главы ──────────────────────────────────────────────────────

_CHAPTER_PATTERN = re.compile(
    r"(?:Глава|Chapter|Глава\s*\d+|Ch\.\s*\d+)\s*[:.]?\s*(.+)?",
    re.IGNORECASE
)


def split_into_chapters(text: str) -> List[Tuple[str, str]]:
    """
    Разбивает текст на главы.

    Returns:
        Список кортежей (название_главы, текст_главы)
    """
    chapters = []
    lines = text.split("\n")
    current_chapter = None
    current_text = []

    for line in lines:
        match = _CHAPTER_PATTERN.match(line.strip())
        if match:
            # Сохраняем предыдущую главу
            if current_chapter is not None:
                chapters.append((current_chapter, "\n".join(current_text).strip()))
            current_chapter = match.group(1) or f"Глава {len(chapters) + 1}"
            current_text = []
        else:
            current_text.append(line)

    # Сохраняем последнюю главу
    if current_chapter is not None:
        chapters.append((current_chapter, "\n".join(current_text).strip()))
    else:
        # Если глав не найдено — весь текст как одна глава
        chapters.append(("Начало", text.strip()))

    return chapters


# ─── Разбиение на сцены ──────────────────────────────────────────────────────

_SCENE_PATTERNS = [
    re.compile(r"^(?:Сцена|Scene)\s*\d*\s*[:.]?\s*(.+)?", re.IGNORECASE),
    re.compile(r"^(?:\*\*\*|---|===)\s*$", re.MULTILINE),  # Разделители
]


def split_into_scenes(text: str, max_scenes: int = 10) -> List[str]:
    """Разбивает текст главы на сцены."""
    # Пробуем найти явные маркеры сцен
    for pattern in _SCENE_PATTERNS:
        parts = pattern.split(text)
        if len(parts) > 1:
            scenes = [p.strip() for p in parts if p.strip()]
            return scenes[:max_scenes]

    # Если маркеров нет — разбиваем по абзацам
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    scenes = []
    current_scene = []

    for para in paragraphs:
        current_scene.append(para)
        # Новая сцена каждые 3-5 абзацев
        if len(current_scene) >= 4:
            scenes.append("\n\n".join(current_scene))
            current_scene = []

    if current_scene:
        scenes.append("\n\n".join(current_scene))

    return scenes[:max_scenes]


# ─── Создание панелей ────────────────────────────────────────────────────────

def extract_dialogue(text: str) -> Tuple[str, List[str]]:
    """
    Извлекает диалоги из текста.

    Returns:
        (описание_сцены, список_реплик)
    """
    # Паттерны для диалогов
    dialogue_patterns = [
        r'["«"]([^"»"]+)["»"]',  # Кавычки
        r"—\s*(.+)",  # Тире
    ]

    dialogues = []
    description = text

    for pattern in dialogue_patterns:
        found = re.findall(pattern, text)
        if found:
            dialogues.extend([d.strip() for d in found if len(d.strip()) > 2])
            # Убираем диалоги из описания
            description = re.sub(pattern, "", text).strip()

    return description, dialogues


def create_panels(
    scene_text: str,
    scene_index: int,
    panel_index_start: int = 0,
    max_chars: int = 200,
) -> List[Panel]:
    """
    Создает панели из текста сцены.

    Args:
        scene_text: Текст сцены
        scene_index: Индекс сцены
        panel_index_start: Начальный индекс панели
        max_chars: Максимум символов на панель

    Returns:
        Список панелей
    """
    description, dialogues = extract_dialogue(scene_text)

    panels = []
    panel_idx = panel_index_start

    # Создаем панели из диалогов
    for dialogue in dialogues:
        # Обрезаем длинные реплики
        if len(dialogue) > max_chars:
            dialogue = dialogue[:max_chars - 3] + "..."

        panels.append(Panel(
            index=panel_idx,
            text=dialogue,
            description=description[:300] if description else f"Scene {scene_index}",
        ))
        panel_idx += 1

    # Если диалогов нет — создаем одну панель с описанием
    if not panels:
        text_chunk = scene_text[:max_chars]
        if len(scene_text) > max_chars:
            text_chunk += "..."
        panels.append(Panel(
            index=panel_idx,
            text=text_chunk,
            description=scene_text[:500],
        ))

    return panels


# ─── Полный пайплайн ─────────────────────────────────────────────────────────

def process_book(
    text: str,
    max_scenes_per_chapter: int = 5,
    max_chars_per_panel: int = 200,
) -> List[Chapter]:
    """
    Полный пайплайн обработки книги.

    Args:
        text: Полный текст книги
        max_scenes_per_chapter: Максимум сцен на главу
        max_chars_per_panel: Максимум символов на панель

    Returns:
        Список глав с панелями
    """
    cleaned = clean_text(text)
    chapters_data = split_into_chapters(cleaned)

    chapters = []
    for ch_idx, (title, ch_text) in enumerate(chapters_data):
        scenes_text = split_into_scenes(ch_text, max_scenes_per_chapter)
        scenes = []
        panel_counter = 0

        for sc_idx, scene_text in enumerate(scenes_text):
            panels = create_panels(
                scene_text,
                scene_index=sc_idx,
                panel_index_start=panel_counter,
                max_chars=max_chars_per_panel,
            )
            scenes.append(Scene(
                index=sc_idx,
                title=f"Сцена {sc_idx + 1}",
                panels=panels,
                summary=scene_text[:200],
            ))
            panel_counter += len(panels)

        chapters.append(Chapter(
            index=ch_idx,
            title=title,
            scenes=scenes,
            summary=ch_text[:300],
        ))

    return chapters


def get_book_stats(chapters: List[Chapter]) -> Dict:
    """Статистика книги."""
    total_panels = sum(
        len(scene.panels)
        for ch in chapters
        for scene in ch.scenes
    )
    total_scenes = sum(len(ch.scenes) for ch in chapters)

    return {
        "chapters": len(chapters),
        "scenes": total_scenes,
        "panels": total_panels,
    }