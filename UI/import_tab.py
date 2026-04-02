"""
UI/import_tab.py — Вкладка загрузки и предпросмотра книги
"""
from __future__ import annotations
import os
import streamlit as st
from Logic.text_processor import load_book, process_book, get_book_stats, clean_text
from Logic.config import UPLOAD_DIR


def render_import_tab() -> None:
    """
    Вкладка «📖 Импорт книги»:
    - Загрузка TXT / DOCX
    - Предпросмотр текста
    - Настройки разбиения
    - Предпросмотр панелей
    """
    st.header("📖 Импорт книги")

    # ── Загрузка файла ────────────────────────────────────────────────────────
    col_up, col_paste = st.columns([1, 1])

    with col_up:
        uploaded = st.file_uploader(
            "Загрузить файл книги",
            type=["txt", "docx"],
            key="book_uploader",
            help="TXT (UTF-8/CP1251) или DOCX",
        )
        if uploaded:
            save_path = os.path.join(UPLOAD_DIR, uploaded.name)
            with open(save_path, "wb") as f:
                f.write(uploaded.getbuffer())
            try:
                text = load_book(save_path)
                st.session_state["book_text"] = text
                st.session_state["book_name"] = uploaded.name
                st.session_state["chapters"] = None
                st.success(f"✅ Загружено: {uploaded.name} ({len(text):,} символов)")
            except Exception as e:
                st.error(f"❌ Ошибка загрузки: {e}")

    with col_paste:
        pasted = st.text_area(
            "Или вставьте текст напрямую",
            height=150,
            key="book_paste",
            placeholder="Вставьте текст книги здесь...",
        )
        if st.button("📥 Использовать вставленный текст", key="use_paste"):
            if pasted.strip():
                st.session_state["book_text"] = pasted
                st.session_state["book_name"] = "вставленный текст"
                st.session_state["chapters"] = None
                st.success(f"✅ Текст принят ({len(pasted):,} символов)")
            else:
                st.warning("⚠️ Поле пустое")

    # ── Предпросмотр текста ───────────────────────────────────────────────────
    if st.session_state.get("book_text"):
        st.divider()
        st.subheader("📝 Предпросмотр текста")

        with st.expander("Показать первые 500 символов"):
            st.text(st.session_state["book_text"][:500])

        # ── Настройки обработки ───────────────────────────────────────────────
        st.subheader("⚙️ Настройки разбиения")
        col1, col2 = st.columns(2)
        with col1:
            max_scenes = st.slider(
                "Максимум сцен на главу",
                min_value=1, max_value=15,
                value=5, step=1,
                key="max_scenes",
            )
        with col2:
            max_chars = st.slider(
                "Максимум символов на панель",
                min_value=50, max_value=500,
                value=200, step=10,
                key="max_chars",
            )

        if st.button("✂️ Разбить на главы и панели", key="do_process", type="primary"):
            with st.spinner("Обрабатываем книгу..."):
                chapters = process_book(
                    st.session_state["book_text"],
                    max_scenes_per_chapter=max_scenes,
                    max_chars_per_panel=max_chars,
                )
                st.session_state["chapters"] = chapters
                stats = get_book_stats(chapters)
                st.success(
                    f"✅ Обработано: {stats['chapters']} глав, "
                    f"{stats['scenes']} сцен, {stats['panels']} панелей"
                )

    # ── Предпросмотр панелей ──────────────────────────────────────────────────
    if st.session_state.get("chapters"):
        chapters = st.session_state["chapters"]
        st.divider()
        st.subheader("📋 Структура комикса")

        # Выбор главы
        chapter_names = [ch.title for ch in chapters]
        selected_chapter = st.selectbox(
            "Выберите главу",
            chapter_names,
            key="chapter_select",
        )
        chapter_idx = chapter_names.index(selected_chapter)
        chapter = chapters[chapter_idx]

        # Показываем сцены и панели
        for scene in chapter.scenes:
            with st.expander(f"🎬 {scene.title} ({len(scene.panels)} панелей)"):
                st.caption(scene.summary[:200] + "..." if len(scene.summary) > 200 else scene.summary)

                for panel in scene.panels:
                    col_text, col_desc = st.columns([1, 1])
                    with col_text:
                        st.markdown(f"**💬 Панель #{panel.index}**")
                        st.text(panel.text[:100])
                    with col_desc:
                        st.markdown("**🖼️ Описание для генерации:**")
                        st.caption(panel.description[:150] + "...")

        # Статистика
        stats = get_book_stats(chapters)
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("Глав", stats["chapters"])
        col2.metric("Сцен", stats["scenes"])
        col3.metric("Панелей", stats["panels"])