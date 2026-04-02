"""
app.py — Точка входа Comics Generator
Запуск: streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="📚 Comics Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

from UI.sidebar import render_sidebar
from UI.import_tab import render_import_tab
from UI.generate_tab import render_generate_tab
from UI.export_tab import render_export_tab

# Инициализация session_state
for key, val in [
    ("book_text", None),
    ("book_name", ""),
    ("chapters", None),
    ("generation_running", False),
    ("generation_stop", False),
]:
    if key not in st.session_state:
        st.session_state[key] = val

# Боковая панель
settings = render_sidebar()

# Вкладки
tab_import, tab_generate, tab_export = st.tabs([
    "📖 Импорт",
    "🎨 Генерация",
    "📦 Экспорт",
])

with tab_import:
    render_import_tab()

with tab_generate:
    render_generate_tab(settings)

with tab_export:
    render_export_tab(settings)