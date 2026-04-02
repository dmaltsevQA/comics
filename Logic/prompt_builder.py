"""
Logic/prompt_builder.py
────────────────────────
Построение промптов для генерации изображений комиксов.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from .text_processor import Panel
from .config import COMIC_STYLES


# Шаблоны промптов для разных типов сцен
MOOD_KEYWORDS = {
    "happy": "bright lighting, cheerful atmosphere, warm colors",
    "sad": "dim lighting, melancholic atmosphere, cool colors, rain",
    "angry": "dramatic lighting, intense expression, red tones, fire",
    "fearful": "dark shadows, eerie atmosphere, fog, cold colors",
    "surprised": "dynamic pose, wide eyes, dramatic angle",
    "neutral": "balanced lighting, natural colors",
    "romantic": "soft lighting, warm tones, sunset, intimate atmosphere",
    "tense": "high contrast, dramatic shadows, suspenseful atmosphere",
}

# Шаблоны для типов кадров
SHOT_TYPES = {
    "closeup": "close-up shot, detailed face expression",
    "medium": "medium shot, waist-up view",
    "full": "full body shot, complete character view",
    "wide": "wide shot, establishing scene",
    "extreme_closeup": "extreme close-up, eyes or hands detail",
    "over_shoulder": "over-the-shoulder shot, conversation view",
    "bird_eye": "bird's eye view, top-down perspective",
    "low_angle": "low angle shot, looking up at character",
}


def build_panel_prompt(
    panel: Panel,
    style: str = "marvel",
    shot_type: str = "medium",
    additional_details: Optional[str] = None,
) -> str:
    """
    Строит промпт для генерации изображения панели.

    Args:
        panel: Объект панели
        style: Стиль комикса
        shot_type: Тип кадра
        additional_details: Дополнительные детали

    Returns:
        Готовый промпт для Fooocus
    """
    parts = []

    # Базовый стиль
    style_config = COMIC_STYLES.get(style, COMIC_STYLES["marvel"])
    parts.append(style_config["style_prompt"])

    # Тип кадра
    parts.append(SHOT_TYPES.get(shot_type, SHOT_TYPES["medium"]))

    # Описание сцены
    if panel.description:
        # Очищаем описание от диалогов
        desc = panel.description.strip()
        if len(desc) > 200:
            desc = desc[:200] + "..."
        parts.append(f"scene: {desc}")

    # Персонажи
    if panel.characters:
        chars = ", ".join(panel.characters[:3])
        parts.append(f"characters: {chars}")

    # Локация
    if panel.location:
        parts.append(f"location: {panel.location}")

    # Настроение
    mood_keywords = MOOD_KEYWORDS.get(panel.mood, MOOD_KEYWORDS["neutral"])
    parts.append(mood_keywords)

    # Дополнительные детали
    if additional_details:
        parts.append(additional_details)

    return ", ".join(parts)


def build_negative_prompt(style: str = "marvel") -> str:
    """Строит негативный промпт."""
    style_config = COMIC_STYLES.get(style, COMIC_STYLES["marvel"])
    return style_config.get("negative_prompt", "blurry, low quality")


def detect_mood(text: str) -> str:
    """
    Определяет настроение по тексту.

    Args:
        text: Текст панели

    Returns:
        Строка с настроением
    """
    text_lower = text.lower()

    mood_indicators = {
        "happy": ["рад", "счастлив", "улыбка", "смех", "весело", "joy", "happy", "smile"],
        "sad": ["груст", "печал", "слез", "плач", "горе", "sad", "cry", "tear"],
        "angry": ["зл", "гнев", "ярост", "крик", "angry", "rage", "shout"],
        "fearful": ["страх", "ужас", "испуг", "боюсь", "fear", "terrified", "afraid"],
        "surprised": ["удивлен", "неожидан", "внезап", "surprised", "shocked", "suddenly"],
        "romantic": ["любовь", "нежность", "поцелуй", "love", "kiss", "tender"],
        "tense": ["напряжен", "опасность", "угроза", "tense", "danger", "threat"],
    }

    scores = {}
    for mood, indicators in mood_indicators.items():
        score = sum(1 for word in indicators if word in text_lower)
        if score > 0:
            scores[mood] = score

    if scores:
        return max(scores, key=scores.get)
    return "neutral"


def detect_shot_type(panel: Panel) -> str:
    """
    Определяет тип кадра по содержимому панели.

    Args:
        panel: Объект панели

    Returns:
        Тип кадра
    """
    text = panel.text.lower() + " " + panel.description.lower()

    if any(w in text for w in ["глаза", "eyes", "взгляд", "look"]):
        return "extreme_closeup"
    if any(w in text for w in ["лицо", "face", "выражение", "expression"]):
        return "closeup"
    if any(w in text for w in ["панорама", "panorama", "вид", "view", "город", "city"]):
        return "wide"
    if any(w in text for w in ["сверху", "above", "с высоты", "from above"]):
        return "bird_eye"
    if any(w in text for w in ["снизу", "below", "внизу", "looking up"]):
        return "low_angle"

    return "medium"


def build_batch_prompts(
    panels: List[Panel],
    style: str = "marvel",
) -> List[Dict]:
    """
    Строит промпты для пакета панелей.

    Returns:
        Список словарей с промптами и метаданными
    """
    results = []

    for panel in panels:
        # Автоопределение настроения если не задано
        if panel.mood == "neutral" or not panel.mood:
            panel.mood = detect_mood(panel.text + " " + panel.description)

        # Автоопределение типа кадра
        shot_type = detect_shot_type(panel)

        prompt = build_panel_prompt(panel, style, shot_type)
        negative = build_negative_prompt(style)

        results.append({
            "panel_index": panel.index,
            "prompt": prompt,
            "negative_prompt": negative,
            "shot_type": shot_type,
            "mood": panel.mood,
        })

    return results