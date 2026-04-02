"""
UI/sidebar.py — Боковая панель: настройки API, стиль, параметры генерации
"""
from __future__ import annotations
import streamlit as st
from API.fooocus_api import FooocusAPI
from Logic.config import COMIC_STYLES, PANEL_LAYOUTS, FOOOCUS_BASE_URL, DEFAULT_GUIDANCE_SCALE, DEFAULT_STEPS


def render_sidebar() -> dict:
    """
    Рисует боковую панель и возвращает словарь настроек.
    """
    with st.sidebar:
        st.title("🎨 Comics Generator")
        st.caption("Fooocus API • Генерация комиксов")

        st.divider()

        # ── Подключение к Fooocus API ─────────────────────────────────────────
        st.subheader("🔌 Fooocus API")
        api_url = st.text_input(
            "URL API",
            value=FOOOCUS_BASE_URL,
            key="api_url",
        )

        api = FooocusAPI(base_url=api_url)
        api_available = api.is_available()

        if api_available:
            st.success("✅ API подключен")
        else:
            st.error("❌ API недоступен")
            st.caption(f"Убедитесь, что Fooocus запущен на {api_url}")

        st.divider()

        # ── Модель (Checkpoint) ───────────────────────────────────────────────
        st.subheader("🤖 Модель")
        if api_available:
            models = api.get_models()
            if models:
                selected_model = st.selectbox(
                    "Checkpoint",
                    models,
                    index=0,
                    key="selected_model",
                )
            else:
                selected_model = "default"
                st.caption("Модели загружаются...")
        else:
            selected_model = "default"
            st.caption("Недоступно без подключения к API")

        st.divider()

        # ── LoRA ──────────────────────────────────────────────────────────────
        st.subheader("🔧 LoRA")
        if api_available:
            loras = api.get_loras()
            if loras:
                selected_lora = st.selectbox(
                    "LoRA модель",
                    ["— Нет —"] + loras,
                    index=0,
                    key="selected_lora",
                )
                if selected_lora != "— Нет —":
                    lora_weight = st.slider(
                        "Вес LoRA",
                        min_value=-1.0, max_value=2.0,
                        value=1.0, step=0.1,
                        key="lora_weight",
                    )
                else:
                    selected_lora = None
                    lora_weight = 0.0
            else:
                selected_lora = None
                lora_weight = 0.0
                st.caption("LoRA не найдены")
        else:
            selected_lora = None
            lora_weight = 0.0
            st.caption("Недоступно без подключения к API")

        st.divider()

        # ── Стиль Fooocus ─────────────────────────────────────────────────────
        st.subheader("🎨 Стиль Fooocus")
        if api_available:
            fooocus_styles = api.get_styles()
            if fooocus_styles:
                selected_fooocus_style = st.selectbox(
                    "Стиль генерации",
                    fooocus_styles,
                    index=0,
                    key="fooocus_style",
                )
            else:
                selected_fooocus_style = "Fooocus V2"
        else:
            selected_fooocus_style = "Fooocus V2"
            st.caption("Недоступно без подключения к API")

        st.divider()

        # ── Стиль комикса ─────────────────────────────────────────────────────
        st.subheader("📚 Стиль комикса")
        style_options = {k: v["name"] for k, v in COMIC_STYLES.items()}
        selected_style = st.selectbox(
            "Стиль контента",
            list(style_options.values()),
            index=0,
            key="comic_style",
        )
        style_key = next(k for k, v in style_options.items() if v == selected_style)

        # Показываем описание стиля
        st.caption(COMIC_STYLES[style_key]["description"])

        st.divider()

        # ── Раскладка страниц ─────────────────────────────────────────────────
        st.subheader("📐 Раскладка")
        layout_options = {k: v["name"] for k, v in PANEL_LAYOUTS.items()}
        selected_layout = st.selectbox(
            "Тип раскладки",
            list(layout_options.values()),
            index=0,
            key="panel_layout",
        )
        layout_key = next(k for k, v in layout_options.items() if v == selected_layout)
        st.caption(f"Панелей на странице: {PANEL_LAYOUTS[layout_key]['panels_per_page']}")

        st.divider()

        # ─── Настройки текста ─────────────────────────────────────────────────
        st.subheader("💬 Текст на панелях")
        add_text_to_panels = st.checkbox(
            "Добавлять текст на панели",
            value=True,
            key="add_text_to_panels",
            help="Речевые пузыри и подписи поверх изображений",
        )
        bubble_type = st.selectbox(
            "Тип пузыря",
            ["speech", "thought", "caption"],
            index=0,
            key="bubble_type",
            help="speech = речь, thought = мысли, caption = подпись",
        )
        add_captions = st.checkbox(
            "Добавлять подписи сцен",
            value=True,
            key="add_captions",
            help="Жёлтые полосы с описанием сцены",
        )

        st.divider()

        # ── Параметры генерации ───────────────────────────────────────────────
        st.subheader("⚙️ Параметры генерации")
        guidance_scale = st.slider(
            "Guidance Scale (CFG)",
            min_value=1.0, max_value=10.0,
            value=DEFAULT_GUIDANCE_SCALE, step=0.5,
            key="guidance_scale",
        )
        steps = st.slider(
            "Количество шагов",
            min_value=10, max_value=50,
            value=DEFAULT_STEPS, step=5,
            key="steps",
        )
        seed = st.number_input(
            "Seed (-1 = случайный)",
            min_value=-1, max_value=999999999,
            value=-1, step=1,
            key="seed",
        )

        st.divider()

        # ── Статус ────────────────────────────────────────────────────────────
        st.subheader("📊 Статус")
        if st.session_state.get("chapters"):
            from Logic.text_processor import get_book_stats
            stats = get_book_stats(st.session_state["chapters"])
            st.metric("Глав", stats["chapters"])
            st.metric("Сцен", stats["scenes"])
            st.metric("Панелей", stats["panels"])
        else:
            st.info("Загрузите книгу для начала работы")

        return {
            "api": api,
            "api_available": api_available,
            "style": style_key,
            "layout": layout_key,
            "guidance_scale": guidance_scale,
            "steps": steps,
            "seed": seed,
            "model": selected_model,
            "lora": selected_lora,
            "lora_weight": lora_weight,
            "fooocus_style": selected_fooocus_style,
            "add_text_to_panels": add_text_to_panels,
            "bubble_type": bubble_type,
            "add_captions": add_captions,
        }
