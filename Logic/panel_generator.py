"""
Logic/panel_generator.py
────────────────────────
Генерация изображений для панелей комикса через Google Imagen 3 API.
"""

from __future__ import annotations

import os
import time
from typing import List, Dict, Optional, Callable, Tuple
from PIL import Image

from .text_processor import Panel, Scene, Chapter
from .prompt_builder import build_panel_prompt, build_negative_prompt, detect_mood, detect_shot_type
from .config import OUTPUT_DIR, TEMP_DIR, DEFAULT_ASPECT_RATIO, DEFAULT_GUIDANCE_SCALE, DEFAULT_STEPS
from API.google_imagen_api import GoogleImagenAPI


def generate_panel_image(
    api: GoogleImagenAPI,
    panel: Panel,
    style: str = "marvel",
    seed: int = -1,
    guidance_scale: float = DEFAULT_GUIDANCE_SCALE,
    steps: int = DEFAULT_STEPS,
    output_dir: str = OUTPUT_DIR,
    model_name: str = "",
    lora_name: str = "",
    lora_weight: float = 1.0,
    fooocus_style: str = "general",
    generation_mode: str = "imagen",
    character_references: Optional[Dict[str, str]] = None,  # {character_name: image_path}
    location_references: Optional[Dict[str, str]] = None,  # {location_name: image_path}
    allow_moderate_violence: bool = False,
) -> Optional[str]:
    """
    Генерирует изображение для одной панели через Google Imagen 3.

    Args:
        api: API клиент Google Imagen
        panel: Объект панели
        style: Стиль комикса
        seed: Seed для генерации
        guidance_scale: CFG scale (не используется в Imagen)
        steps: Количество шагов (не используется в Imagen)
        output_dir: Директория для сохранения
        model_name: Имя модели
        lora_name: Не используется
        lora_weight: Не используется
        fooocus_style: Не используется
        generation_mode: Режим генерации (всегда "imagen")
        character_references: Словарь референсов персонажей для консистентности
        location_references: Словарь референсов локаций для консистентности
        allow_moderate_violence: Разрешить сцены с умеренным насилием (ранения, кровь)
    """
    # Определяем настроение и тип кадра
    if panel.mood == "neutral":
        panel.mood = detect_mood(panel.text + " " + panel.description)

    shot_type = detect_shot_type(panel)

    # Строим промпт
    prompt = build_panel_prompt(panel, style, shot_type, generation_mode="imagen")
    negative = build_negative_prompt(style)

    print(f"[PANEL] Генерация панели #{panel.index}")
    print(f"[PANEL] Промпт: {prompt[:100]}...")
    print(f"[PANEL] Режим: imagen")

    images = None

    # Генерация через Google Imagen 3
    if (character_references or location_references) and (panel.characters or panel.location):
        # Фильтруем референсы только для персонажей и локаций в этой панели
        active_chars = {
            name: path for name, path in character_references.items()
            if name in panel.characters
        } if character_references else {}
        
        active_locs = {
            name: path for name, path in location_references.items()
            if name == panel.location or (hasattr(panel, 'location') and panel.location)
        } if location_references else {}
        
        if active_chars or active_locs:
            print(f"[PANEL] Используем референсы:")
            if active_chars:
                print(f"  - Персонажи: {list(active_chars.keys())}")
            if active_locs:
                print(f"  - Локации: {list(active_locs.keys())}")
            
            images = api.generate_multi_character_scene(
                prompt=prompt,
                characters=active_chars,
                locations=active_locs if active_locs else None,
                aspect_ratio=DEFAULT_ASPECT_RATIO.replace("*", ":"),
                image_number=1,
                allow_moderate_violence=allow_moderate_violence,
            )
    
    # Если нет референсов или ошибка, генерируем без них
    if not images:
        images = api.generate_image(
            prompt=prompt,
            negative_prompt=negative,
            aspect_ratio=DEFAULT_ASPECT_RATIO.replace("*", ":"),
            image_number=1,
            seed=seed,
            model_name=model_name or "google/imagen-3",
        )

    if images and len(images) > 0:
        # Сохраняем изображение
        os.makedirs(output_dir, exist_ok=True)
        filename = f"panel_{panel.index:04d}.png"
        filepath = os.path.join(output_dir, filename)
        images[0].save(filepath, "PNG")
        panel.image_path = filepath
        print(f"[PANEL] Сохранено: {filepath}")
        return filepath

    print(f"[PANEL] Ошибка генерации панели #{panel.index}")
    return None


def generate_scene_images(
    api: GoogleImagenAPI,
    scene: Scene,
    style: str = "marvel",
    seed: int = -1,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None,
    model_name: str = "",
    lora_name: str = "",
    lora_weight: float = 1.0,
    fooocus_style: str = "general",
    generation_mode: str = "imagen",
    character_references: Optional[Dict[str, str]] = None,
) -> Tuple[int, int]:
    """
    Генерирует изображения для всех панелей сцены.

    Returns:
        (успешные, всего)
    """
    total = len(scene.panels)
    success = 0

    for i, panel in enumerate(scene.panels):
        if stop_flag and stop_flag():
            print("[PANEL] Генерация остановлена пользователем")
            break

        if progress_callback:
            progress_callback(i + 1, total, f"Панель #{panel.index}")

        # Используем seed + i для вариативности
        panel_seed = seed if seed == -1 else seed + i

        result = generate_panel_image(
            api=api,
            panel=panel,
            style=style,
            seed=panel_seed,
            model_name=model_name,
            lora_name=lora_name,
            lora_weight=lora_weight,
            fooocus_style=fooocus_style,
            generation_mode=generation_mode,
            character_references=character_references,
        )

        if result:
            success += 1

    return success, total


def generate_chapter_images(
    api: GoogleImagenAPI,
    chapter: Chapter,
    style: str = "marvel",
    seed: int = -1,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None,
    model_name: str = "",
    lora_name: str = "",
    lora_weight: float = 1.0,
    fooocus_style: str = "general",
    generation_mode: str = "imagen",
    character_references: Optional[Dict[str, str]] = None,
) -> Tuple[int, int]:
    """
    Генерирует изображения для всех панелей главы.

    Returns:
        (успешные, всего)
    """
    total_panels = sum(len(scene.panels) for scene in chapter.scenes)
    success = 0
    processed = 0

    for scene in chapter.scenes:
        scene_success, scene_total = generate_scene_images(
            api=api,
            scene=scene,
            style=style,
            seed=seed,
            progress_callback=progress_callback,
            stop_flag=stop_flag,
            model_name=model_name,
            lora_name=lora_name,
            lora_weight=lora_weight,
            fooocus_style=fooocus_style,
            generation_mode=generation_mode,
            character_references=character_references,
        )
        success += scene_success
        processed += scene_total

    return success, total_panels


def generate_all_images(
    api: GoogleImagenAPI,
    chapters: List[Chapter],
    style: str = "marvel",
    seed: int = -1,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None,
    model_name: str = "",
    lora_name: str = "",
    lora_weight: float = 1.0,
    fooocus_style: str = "general",
    generation_mode: str = "imagen",
    character_references: Optional[Dict[str, str]] = None,
) -> Tuple[int, int]:
    """
    Генерирует изображения для всех глав через Google Imagen 3.

    Args:
        api: API клиент Google Imagen
        chapters: Список глав
        style: Стиль комикса
        seed: Seed для генерации
        progress_callback: Callback для прогресса
        stop_flag: Флаг остановки
        model_name: Имя модели
        lora_name: Не используется
        lora_weight: Не используется
        fooocus_style: Не используется
        generation_mode: Режим генерации (всегда "imagen")
        character_references: Словарь референсов персонажей

    Returns:
        (успешные, всего)
    """
    total_panels = sum(
        len(scene.panels)
        for ch in chapters
        for scene in ch.scenes
    )
    success = 0
    processed = 0

    for chapter in chapters:
        chapter_success, chapter_total = generate_chapter_images(
            api=api,
            chapter=chapter,
            style=style,
            seed=seed,
            progress_callback=progress_callback,
            stop_flag=stop_flag,
            model_name=model_name,
            lora_name=lora_name,
            lora_weight=lora_weight,
            fooocus_style=fooocus_style,
            generation_mode=generation_mode,
            character_references=character_references,
        )
        success += chapter_success
        processed += chapter_total

    return success, total_panels


def regenerate_single_panel(
    api: GoogleImagenAPI,
    panel: Panel,
    style: str = "marvel",
    seed: int = -1,
    model_name: str = "",
    lora_name: str = "",
    lora_weight: float = 1.0,
    fooocus_style: str = "general",
    generation_mode: str = "imagen",
    character_references: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """Перегенерировать одну панель через Google Imagen 3."""
    return generate_panel_image(
        api=api,
        panel=panel,
        style=style,
        seed=seed,
        model_name=model_name,
        lora_name=lora_name,
        lora_weight=lora_weight,
        fooocus_style=fooocus_style,
        generation_mode=generation_mode,
        character_references=character_references,
    )


def get_panel_preview(panel: Panel) -> Optional[Image.Image]:
    """Получить превью панели для отображения в UI."""
    if panel.image_path and os.path.exists(panel.image_path):
        return Image.open(panel.image_path)
    return None