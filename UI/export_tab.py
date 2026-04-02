"""
UI/export_tab.py — Вкладка экспорта комикса
"""
from __future__ import annotations
import os
import streamlit as st
from Logic.text_processor import get_book_stats
from Logic.comic_builder import (
    export_pages_as_images,
    export_pages_with_text,
    export_as_pdf,
    export_all_panels_as_individual_images,
    export_all_panels_with_text,
    get_comic_stats,
)
from Logic.config import OUTPUT_DIR


def render_export_tab(settings: dict) -> None:
    """
    Вкладка «📦 Экспорт»:
    - Экспорт страниц как изображений
    - Экспорт в PDF
    - Экспорт отдельных панелей
    - Предпросмотр готового комикса
    """
    st.header("📦 Экспорт комикса")

    chapters = st.session_state.get("chapters")

    # ── Проверки ──────────────────────────────────────────────────────────────
    if not chapters:
        st.info("📖 Сначала импортируйте книгу и сгенерируйте изображения")
        return

    # ── Статистика ────────────────────────────────────────────────────────────
    comic_stats = get_comic_stats(chapters)

    col1, col2, col3 = st.columns(3)
    col1.metric("Всего панелей", comic_stats["total_panels"])
    col2.metric("С изображениями", comic_stats["panels_with_images"])
    col3.metric("Готово", f"{comic_stats['completion_percent']}%")

    if comic_stats["panels_with_images"] == 0:
        st.warning("⚠️ Нет сгенерированных изображений. Сначала запустите генерацию.")
        return

    st.divider()

    # ── Настройки экспорта ────────────────────────────────────────────────────
    st.subheader("⚙️ Настройки экспорта")
    layout = settings.get("layout", "standard")
    layout_names = {
        "standard": "Стандартная сетка",
        "cinematic": "Кинематографичная",
        "manga": "Манга",
        "dynamic": "Динамичная",
    }
    st.caption(f"Раскладка: {layout_names.get(layout, layout)}")

    st.divider()

    # ── Настройки текста ──────────────────────────────────────────────────────
    add_text = settings.get("add_text_to_panels", True)
    bubble_type = settings.get("bubble_type", "speech")
    add_captions = settings.get("add_captions", True)

    if add_text:
        st.info(f"💬 Текст будет добавлен: тип пузыря = {bubble_type}, подписи = {add_captions}")

    # ── Варианты экспорта ─────────────────────────────────────────────────────
    st.subheader("💾 Варианты экспорта")

    col1, col2, col3 = st.columns(3)

    # Экспорт страниц как PNG
    with col1:
        st.markdown("### 🖼️ Страницы (PNG)")
        st.caption("Каждая страница комикса как отдельное изображение")
        if st.button("📥 Экспорт страниц", key="export_pages", use_container_width=True):
            with st.spinner("Экспорт страниц..."):
                files = export_pages_as_images(
                    chapters=chapters,
                    output_dir=os.path.join(OUTPUT_DIR, "pages"),
                    layout=layout,
                )
                if files:
                    st.success(f"✅ Экспортировано {len(files)} страниц")
                    # Показываем первые несколько страниц
                    for f in files[:3]:
                        st.image(f, use_container_width=True)
                    if len(files) > 3:
                        st.caption(f"... и ещё {len(files) - 3} страниц")
                else:
                    st.error("❌ Ошибка экспорта")

    # Экспорт в PDF
    with col2:
        st.markdown("### 📄 PDF файл")
        st.caption("Полный комикс в одном PDF файле")
        if st.button("📥 Экспорт в PDF", key="export_pdf", use_container_width=True):
            book_name = st.session_state.get("book_name", "comic")
            safe_name = "".join(c for c in book_name if c.isalnum() or c in " _-")[:30]
            pdf_path = os.path.join(OUTPUT_DIR, f"{safe_name}.pdf")

            with st.spinner("Создание PDF..."):
                success = export_as_pdf(
                    chapters=chapters,
                    output_path=pdf_path,
                    layout=layout,
                )
                if success:
                    st.success(f"✅ PDF сохранён: {pdf_path}")
                    # Предлагаем скачать
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "⬇️ Скачать PDF",
                            data=f,
                            file_name=f"{safe_name}.pdf",
                            mime="application/pdf",
                            key="download_pdf",
                        )
                else:
                    st.error("❌ Ошибка создания PDF")

    # Экспорт отдельных панелей
    with col3:
        st.markdown("### 🎨 Отдельные панели")
        st.caption("Каждая панель как отдельное изображение")
        if st.button("📥 Экспорт панелей", key="export_panels", use_container_width=True):
            with st.spinner("Экспорт панелей..."):
                files = export_all_panels_as_individual_images(
                    chapters=chapters,
                    output_dir=os.path.join(OUTPUT_DIR, "panels"),
                )
                if files:
                    st.success(f"✅ Экспортировано {len(files)} панелей")
                else:
                    st.error("❌ Ошибка экспорта")

    # Экспорт отдельных панелей с текстом
    st.subheader("💬 Отдельные панели с текстом")
    st.caption("Каждая панель с речевыми пузырями")
    if st.button("📥 Экспорт панелей с текстом", key="export_panels_text", use_container_width=True):
        with st.spinner("Экспорт панелей с текстом..."):
            files = export_all_panels_with_text(
                chapters=chapters,
                output_dir=os.path.join(OUTPUT_DIR, "panels_with_text"),
                bubble_type=bubble_type,
                add_captions=add_captions,
            )
            if files:
                st.success(f"✅ Экспортировано {len(files)} панелей с текстом")
            else:
                st.error("❌ Ошибка экспорта")

    # Экспорт страниц с текстом (речевые пузыри)
    st.divider()
    st.subheader("💬 Экспорт с текстом")
    st.caption("Добавляет речевые пузыри и подписи поверх изображений")
    if st.button("📥 Экспорт страниц с текстом", key="export_pages_text", use_container_width=True):
        with st.spinner("Экспорт страниц с текстом..."):
            files = export_pages_with_text(
                chapters=chapters,
                output_dir=os.path.join(OUTPUT_DIR, "pages_with_text"),
                layout=layout,
                bubble_type=bubble_type,
                add_captions=add_captions,
            )
            if files:
                st.success(f"✅ Экспортировано {len(files)} страниц с текстом")
                for f in files[:3]:
                    st.image(f, use_container_width=True)
                if len(files) > 3:
                    st.caption(f"... и ещё {len(files) - 3} страниц")
            else:
                st.error("❌ Ошибка экспорта")

    st.divider()

    # ── Предпросмотр ──────────────────────────────────────────────────────────
    st.subheader("👁️ Предпросмотр комикса")

    # Показываем сгенерированные страницы
    pages_dir = os.path.join(OUTPUT_DIR, "pages")
    if os.path.exists(pages_dir):
        page_files = sorted([
            os.path.join(pages_dir, f)
            for f in os.listdir(pages_dir)
            if f.endswith(".png")
        ])

        if page_files:
            selected_page = st.selectbox(
                "Выберите страницу",
                range(len(page_files)),
                format_func=lambda i: f"Страница {i + 1}",
                key="preview_page",
            )
            st.image(page_files[selected_page], use_container_width=True)
        else:
            st.info("Сначала экспортируйте страницы")
    else:
        st.info("Сначала экспортируйте страницы")

    st.divider()

    # ── Очистка ───────────────────────────────────────────────────────────────
    st.subheader("🗑️ Очистка")
    if st.button("🗑️ Удалить все сгенерированные файлы", key="cleanup"):
        import shutil
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            st.success("✅ Файлы удалены")
            st.rerun()