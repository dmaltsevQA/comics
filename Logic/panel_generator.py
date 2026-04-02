"""
Logic/panel_generator.py
────────────────────────
Генерация изображений для панелей комикса через Fooocus API.
"""

from __future__ import annotations

import os
import time
from typing import List, Dict, Optional, Callable, Tuple
from PIL import Image

from .text_processor import Panel, Scene, Chapter
from .prompt_builder import build_panel_prompt, build_negative_prompt, detect_mood, detect_shot_type
from .config import OUTPUT_DIR, TEMP_DIR, DEFAULT_ASPECT_RATIO, DEFAULT_GUIDANCE_SCALE, DEFAULT_STEPS
from API.fooocus_api import FooocusAPI


def generate_panel_image(
    api: FooocusAPI,
    panel: Panel,
    style: str = "marvel",
    seed: int = -1,
    guidance_scale: float = DEFAULT_GUIDANCE_SCALE,
    steps: int = DEFAULT_STEPS,
    output_dir: str = OUTPUT_DIR,
    model_name: str = "",
    lora_name: str = "",
    lora_weight: float = 1.0,
    fooocus_style: str = "Fooocus V2",
) -> Optional[str]:
    """
    Генерирует изображение для одной панели.

    Returns:
        Путь к сохраненному файлу или None
    """
    # Определяем настроение и тип кадра
    if panel.mood == "neutral":
        panel.mood = detect_mood(panel.text + " " + panel.description)

    shot_type = detect_shot_type(panel)

    # Строим промпт
    prompt = build_panel_prompt(panel, style, shot_type)
    negative = build_negative_prompt(style)

    print(f"[PANEL] Генерация панели #{panel.index}")
    print(f"[PANEL] Промпт: {prompt[:100]}...")

    # Генерируем изображение
    images = api.generate_image(
        prompt=prompt,
        negative_prompt=negative,
        style=fooocus_style,
        aspect_ratio=DEFAULT_ASPECT_RATIO,
        image_number=1,
        seed=seed,
        guidance_scale=guidance_scale,
        steps=steps,
        model_name=model_name,
        lora_name=lora_name,
        lora_weight=lora_weight,
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
    api: FooocusAPI,
    scene: Scene,
    style: str = "marvel",
    seed: int = -1,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None,
    model_name: str = "",
    lora_name: str = "",
    lora_weight: float = 1.0,
    fooocus_style: str = "Fooocus V2",
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
        )

        if result:
            success += 1

    return success, total


def generate_chapter_images(
    api: FooocusAPI,
    chapter: Chapter,
    style: str = "marvel",
    seed: int = -1,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None,
    model_name: str = "",
    lora_name: str = "",
    lora_weight: float = 1.0,
    fooocus_style: str = "Fooocus V2",
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
        )
        success += scene_success
        processed += scene_total

    return success, total_panels


def generate_all_images(
    api: FooocusAPI,
    chapters: List[Chapter],
    style: str = "marvel",
    seed: int = -1,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None,
    model_name: str = "",
    lora_name: str = "",
    lora_weight: float = 1.0,
    fooocus_style: str = "Fooocus V2",
) -> Tuple[int, int]:
    """
    Генерирует изображения для всех глав.

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
        )
        success += chapter_success
        processed += chapter_total

    return success, total_panels


def regenerate_single_panel(
    api: FooocusAPI,
    panel: Panel,
    style: str = "marvel",
    seed: int = -1,
    model_name: str = "",
    lora_name: str = "",
    lora_weight: float = 1.0,
    fooocus_style: str = "Fooocus V2",
) -> Optional[str]:
    """Перегенерировать одну панель."""
    return generate_panel_image(
        api=api,
        panel=panel,
        style=style,
        seed=seed,
        model_name=model_name,
        lora_name=lora_name,
        lora_weight=lora_weight,
        fooocus_style=fooocus_style,
    )


def get_panel_preview(panel: Panel) -> Optional[Image.Image]:
    """Получить превью панели для отображения в UI."""
    if panel.image_path and os.path.exists(panel.image_path):
        return Image.open(panel.image_path)
    return None