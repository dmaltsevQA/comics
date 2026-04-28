"""
UI/sidebar.py — Боковая панель: настройки API, стиль, параметры генерации
"""
from __future__ import annotations
import streamlit as st
from API.google_imagen_api import GoogleImagenAPI
from Logic.config import (
    COMIC_STYLES, PANEL_LAYOUTS, DEFAULT_GUIDANCE_SCALE, 
    DEFAULT_STEPS, ROUTERAI_API_KEY, ROUTERAI_BASE_URL, IMAGEN_MODEL_NAME
)


def render_sidebar() -> dict:
    """
    Рисует боковую панель и возвращает словарь настроек.
    """
    with st.sidebar:
        st.title("🎨 Comics Generator")
        st.caption("Google Imagen 3 • Генерация комиксов с консистентными персонажами")

        st.divider()

        # ── Настройки Google Imagen 3 ──────────────────────────────────────────
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
        
        # Seed
        seed = st.number_input(
            "Seed (-1 = случайный)",
            min_value=-1, max_value=999999999,
            value=-1, step=1,
            key="seed",
        )
        
        st.caption("Для Imagen параметры CFG и steps управляются автоматически")

        st.divider()

        # ── Референсы персонажей и локаций ───────────────────────────────────────────────
        st.subheader("👥 Персонажи и локации")
        st.caption("Загрузите изображения с подписями для консистентности")
        
        character_refs = {}
        location_refs = {}
        
        # Выбор типа референса
        ref_type = st.radio(
            "Тип референса",
            ["Персонаж", "Локация"],
            key="ref_type_selector",
            horizontal=True
        )
        
        num_references = st.number_input(
            f"Количество {'персонажей' if ref_type == 'Персонаж' else 'локаций'}",
            min_value=0, max_value=10,
            value=0, step=1,
            key=f"num_{ref_type.lower()}_refs",
        )
        
        for i in range(num_references):
            st.markdown(f"**{'Персонаж' if ref_type == 'Персонаж' else 'Локация'} #{i+1}**")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                ref_name = st.text_input(
                    "Название/Имя",
                    placeholder="Например: John Doe / Замок дракона",
                    key=f"{ref_type.lower()}_name_{i}",
                    help="Используйте это имя в промптах для идентификации"
                )
            with col2:
                ref_file = st.file_uploader(
                    "Изображение",
                    type=["png", "jpg", "jpeg"],
                    key=f"{ref_type.lower()}_file_{i}",
                )
            
            if ref_name and ref_file:
                # Сохраняем временный файл
                import os
                from Logic.config import TEMP_DIR
                temp_path = os.path.join(TEMP_DIR, f"{ref_type.lower()}_{i}_{ref_file.name}")
                with open(temp_path, "wb") as f:
                    f.write(ref_file.getvalue())
                
                if ref_type == "Персонаж":
                    character_refs[ref_name] = temp_path
                else:
                    location_refs[ref_name] = temp_path
            
            st.divider()
        
        # Объединяем все референсы
        all_references = {**character_refs, **location_refs}
        st.session_state["character_references"] = all_references
        st.session_state["location_references"] = location_refs
        
        if all_references:
            st.success(f"✅ Загружено {len(all_references)} референсов")
            if character_refs:
                st.info(f"👤 Персонажи: {', '.join(character_refs.keys())}")
            if location_refs:
                st.info(f"🏰 Локации: {', '.join(location_refs.keys())}")

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

        # Параметры всегда фиксированы для Imagen
        guidance_scale = DEFAULT_GUIDANCE_SCALE
        steps = DEFAULT_STEPS
        
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
            "imagen_model": selected_imagen_model,
            "add_text_to_panels": add_text_to_panels,
            "bubble_type": bubble_type,
            "add_captions": add_captions,
            "character_references": st.session_state.get("character_references", {}),
        }
