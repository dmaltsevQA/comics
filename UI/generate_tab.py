"""
UI/generate_tab.py — Вкладка генерации изображений для панелей
"""
from __future__ import annotations
import streamlit as st
from Logic.text_processor import get_book_stats
from Logic.panel_generator import generate_panel_image, generate_all_images, get_panel_preview
from Logic.comic_builder import get_comic_stats
from Logic.text_renderer import render_panel_with_text
from API.fooocus_api import FooocusAPI


def render_generate_tab(settings: dict) -> None:
    """
    Вкладка «🎨 Генерация»:
    - Запуск генерации изображений
    - Прогресс-бар
    - Предпросмотр панелей
    - Перегенерация отдельных панелей
    """
    st.header("🎨 Генерация изображений")

    chapters = st.session_state.get("chapters")

    # ── Проверки ──────────────────────────────────────────────────────────────
    if not chapters:
        st.info("📖 Сначала импортируйте книгу во вкладке «📖 Импорт»")
        return

    if not settings.get("api_available"):
        st.warning("⚠️ Fooocus API недоступен. Проверьте подключение в боковой панели.")
        return

    # ── Статистика ────────────────────────────────────────────────────────────
    stats = get_book_stats(chapters)
    comic_stats = get_comic_stats(chapters)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Панелей", stats["panels"])
    col2.metric("С изображениями", comic_stats["panels_with_images"])
    col3.metric("С текстом", comic_stats["panels_with_text"])
    col4.metric("Готово", f"{comic_stats['completion_percent']}%")
    col5.metric("Глав", stats["chapters"])

    st.divider()

    # ── Выбор диапазона ──────────────────────────────────────────────────────
    st.subheader("📌 Диапазон генерации")
    chapter_names = [ch.title for ch in chapters]
    selected_chapter = st.selectbox(
        "Выберите главу",
        ["— Все главы —"] + chapter_names,
        key="gen_chapter_select",
    )

    # ── Управление генерацией ─────────────────────────────────────────────────
    col_start, col_stop = st.columns(2)

    if "generation_running" not in st.session_state:
        st.session_state["generation_running"] = False
    if "generation_stop" not in st.session_state:
        st.session_state["generation_stop"] = False

    with col_start:
        start_btn = st.button(
            "▶️ Начать генерацию",
            key="start_generation",
            type="primary",
            disabled=st.session_state["generation_running"],
        )

    with col_stop:
        stop_btn = st.button(
            "⏹ Остановить",
            key="stop_generation",
            disabled=not st.session_state["generation_running"],
        )

    if stop_btn:
        st.session_state["generation_stop"] = True

    # ── Генерация ─────────────────────────────────────────────────────────────
    if start_btn:
        st.session_state["generation_running"] = True
        st.session_state["generation_stop"] = False

        progress_bar = st.progress(0, text="Начинаем генерацию...")
        status_text = st.empty()

        api: FooocusAPI = settings["api"]

        def _progress(current: int, total: int, text: str):
            pct = current / total if total > 0 else 0
            progress_bar.progress(pct, text=f"Панель {current}/{total}")
            status_text.caption(f"🖼️ Генерация: {text[:60]}...")

        def _stop() -> bool:
            return st.session_state.get("generation_stop", False)

        # Определяем какие главы генерировать
        if selected_chapter == "— Все главы —":
            chapters_to_gen = chapters
        else:
            ch_idx = chapter_names.index(selected_chapter)
            chapters_to_gen = [chapters[ch_idx]]

        try:
            success, total = generate_all_images(
                api=api,
                chapters=chapters_to_gen,
                style=settings["style"],
                seed=settings["seed"],
                progress_callback=_progress,
                stop_flag=_stop,
                model_name=settings.get("model", ""),
                lora_name=settings.get("lora", ""),
                lora_weight=settings.get("lora_weight", 1.0),
                fooocus_style=settings.get("fooocus_style", "Fooocus V2"),
            )
            st.session_state["chapters"] = chapters  # Обновляем с путями к изображениям

            if success == total:
                st.success(f"✅ Генерация завершена! {success}/{total} панелей")
            elif success > 0:
                st.warning(f"⚠️ Сгенерировано {success}/{total} панелей")
            else:
                st.error("❌ Ошибка генерации")
        except Exception as e:
            st.error(f"❌ Ошибка: {e}")
        finally:
            st.session_state["generation_running"] = False
            st.rerun()

    # ── Предпросмотр панелей ──────────────────────────────────────────────────
    st.divider()
    st.subheader("🖼️ Предпросмотр панелей")

    # Выбор панели для просмотра
    all_panels = []
    for ch in chapters:
        for scene in ch.scenes:
            for panel in scene.panels:
                all_panels.append((ch, scene, panel))

    if all_panels:
        panel_options = [f"#{p.index} - {p.text[:50]}..." for _, _, p in all_panels]
        selected_idx = st.selectbox(
            "Выберите панель",
            range(len(all_panels)),
            format_func=lambda i: panel_options[i],
            key="panel_preview_select",
        )

        ch, scene, panel = all_panels[selected_idx]

        col_info, col_image = st.columns([1, 2])

        with col_info:
            st.markdown(f"**Панель #{panel.index}**")
            st.markdown(f"**Глава:** {ch.title}")
            st.markdown(f"**Сцена:** {scene.title}")
            st.markdown("**Текст:**")
            st.text(panel.text)
            st.markdown("**Настроение:**")
            st.caption(panel.mood)

            # Кнопка перегенерации
            if st.button("🔄 Перегенерировать", key=f"regen_{panel.index}"):
                with st.spinner("Перегенерация..."):
                    result = generate_panel_image(
                        api=settings["api"],
                        panel=panel,
                        style=settings["style"],
                        seed=settings["seed"],
                        model_name=settings.get("model", ""),
                        lora_name=settings.get("lora", ""),
                        lora_weight=settings.get("lora_weight", 1.0),
                        fooocus_style=settings.get("fooocus_style", "Fooocus V2"),
                    )
                    if result:
                        st.success("✅ Перегенерировано!")
                        st.rerun()
                    else:
                        st.error("❌ Ошибка перегенерации")

        with col_image:
            if panel.image_path:
                try:
                    img = get_panel_preview(panel)
                    if img:
                        st.image(img, use_container_width=True, caption="Без текста")

                        # Предпросмотр с текстом
                        if settings.get("add_text_to_panels", True):
                            st.markdown("**С текстом:**")
                            text_img = render_panel_with_text(
                                img,
                                panel.text,
                                description=panel.description[:80] if settings.get("add_captions", True) else "",
                                bubble_type=settings.get("bubble_type", "speech"),
                            )
                            st.image(text_img, use_container_width=True)
                    else:
                        st.warning("Не удалось загрузить изображение")
                except Exception as e:
                    st.warning(f"Ошибка загрузки: {e}")
            else:
                st.info("🔇 Изображение ещё не сгенерировано")
