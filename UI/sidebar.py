"""
UI/sidebar.py — Боковая панель: настройки API, стиль, параметры генерации
"""
from __future__ import annotations
import streamlit as st
from API.fooocus_api import FooocusAPI
from API.google_imagen_api import GoogleImagenAPI
from Logic.config import (
    COMIC_STYLES, PANEL_LAYOUTS, FOOOCUS_BASE_URL, DEFAULT_GUIDANCE_SCALE, 
    DEFAULT_STEPS, ROUTERAI_API_KEY, ROUTERAI_BASE_URL, IMAGEN_MODEL_NAME, GENERATION_MODE
)


def render_sidebar() -> dict:
    """
    Рисует боковую панель и возвращает словарь настроек.
    """
    with st.sidebar:
        st.title("🎨 Comics Generator")
        st.caption("Fooocus / Google Imagen 3 • Генерация комиксов")

        st.divider()

        # ── Выбор режима генерации ─────────────────────────────────────────────
        st.subheader("🔄 Режим генерации")
        generation_mode = st.radio(
            "Выберите API",
            ["fooocus", "imagen"],
            format_func=lambda x: "Fooocus (локально)" if x == "fooocus" else "Google Imagen 3 (облако)",
            index=0 if generation_mode_default() == "fooocus" else 1,
            key="generation_mode_select",
            help="Fooocus требует локальный сервер, Imagen 3 работает через облачный API"
        )

        st.divider()

        # ── Настройки в зависимости от режима ───────────────────────────────────
        api = None
        api_available = False
        
        if generation_mode == "fooocus":
            # Настройки Fooocus
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

            # Модель (Checkpoint)
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

            # LoRA
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

            # Стиль Fooocus
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
            
            # Для Fooocus эти параметры не используются
            selected_imagen_model = IMAGEN_MODEL_NAME
            
        else:  # generation_mode == "imagen"
            # Настройки Google Imagen 3
            st.subheader("☁️ Google Imagen 3 (RouterAI)")
            
            routerai_key = st.text_input(
                "API Key RouterAI",
                value=ROUTERAI_API_KEY or "",
                type="password",
                key="routerai_key",
                help="Получите ключ на routerai.ru"
            )
            
            routerai_url = st.text_input(
                "Base URL",
                value=ROUTERAI_BASE_URL,
                key="routerai_url",
            )
            
            imagen_model = st.text_input(
                "Model Name",
                value=IMAGEN_MODEL_NAME,
                key="imagen_model",
                help="Например: google/imagen-3"
            )
            
            api = GoogleImagenAPI(api_key=routerai_key, base_url=routerai_url)
            api_available = api.is_available()
            
            if api_available:
                st.success("✅ Imagen API подключен")
            else:
                st.error("❌ API недоступен")
                st.caption("Проверьте API ключ и подключение к интернету")
            
            st.divider()
            
            # Информация о возможностях Imagen
            st.info("""
            **Преимущества Imagen 3:**
            - ✅ Консистентность персонажей через референсы
            - ✅ Сцены с несколькими персонажами
            - ✅ Высокое качество генерации
            - ✅ Не требует локального GPU
            """)
            
            selected_model = imagen_model
            selected_lora = None
            lora_weight = 0.0
            selected_fooocus_style = "general"
            selected_imagen_model = imagen_model

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
        
        # Seed общий для обоих режимов
        seed = st.number_input(
            "Seed (-1 = случайный)",
            min_value=-1, max_value=999999999,
            value=-1, step=1,
            key="seed",
        )
        
        # Параметры только для Fooocus
        if generation_mode == "fooocus":
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
        else:
            guidance_scale = DEFAULT_GUIDANCE_SCALE
            steps = DEFAULT_STEPS
            st.caption("Для Imagen параметры CFG и steps управляются автоматически")

        st.divider()

        # ── Референсы персонажей (только для Imagen) ───────────────────────────
        if generation_mode == "imagen":
            st.subheader("👥 Персонажи")
            st.caption("Загрузите изображения персонажей для консистентности")
            
            character_refs = {}
            
            # Простой интерфейс для добавления референсов
            num_characters = st.number_input(
                "Количество персонажей",
                min_value=0, max_value=10,
                value=0, step=1,
                key="num_characters",
            )
            
            for i in range(num_characters):
                col1, col2 = st.columns([2, 1])
                with col1:
                    char_name = st.text_input(
                        "Имя персонажа",
                        placeholder="Например: John Doe",
                        key=f"char_name_{i}",
                    )
                with col2:
                    char_file = st.file_uploader(
                        "Фото",
                        type=["png", "jpg", "jpeg"],
                        key=f"char_file_{i}",
                    )
                
                if char_name and char_file:
                    # Сохраняем временный файл
                    import os
                    from Logic.config import TEMP_DIR
                    temp_path = os.path.join(TEMP_DIR, f"char_{i}_{char_file.name}")
                    with open(temp_path, "wb") as f:
                        f.write(char_file.getvalue())
                    character_refs[char_name] = temp_path
            
            st.session_state["character_references"] = character_refs
            if character_refs:
                st.success(f"✅ Загружено {len(character_refs)} персонажей")
        else:
            st.session_state["character_references"] = {}

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
            "generation_mode": generation_mode,
            "style": style_key,
            "layout": layout_key,
            "guidance_scale": guidance_scale,
            "steps": steps,
            "seed": seed,
            "model": selected_model,
            "lora": selected_lora,
            "lora_weight": lora_weight,
            "fooocus_style": selected_fooocus_style,
            "imagen_model": selected_imagen_model,
            "add_text_to_panels": add_text_to_panels,
            "bubble_type": bubble_type,
            "add_captions": add_captions,
            "character_references": st.session_state.get("character_references", {}),
        }


def generation_mode_default() -> str:
    """Возвращает режим генерации по умолчанию из конфига."""
    import os
    return os.getenv("GENERATION_MODE", "fooocus")
