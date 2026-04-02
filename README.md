# 📚 Comics Generator

Приложение для создания комиксов из книг с использованием Fooocus API для генерации изображений.

## 🚀 Установка

```bash
pip install -r requirements.txt
```

## 📋 Требования

- **Fooocus API** — запущенный сервер Fooocus с API (обычно на `http://localhost:7865`)
- **Python 3.10+**

## 🎯 Возможности

- 📖 Импорт книг из TXT и DOCX файлов
- ✂️ Автоматическое разбиение текста на сцены/панели
- 🎨 Генерация промптов для каждой панели
- 🖼️ Генерация изображений через Fooocus API
- 💬 **Рендеринг текста поверх панелей** (речевые пузыри, подписи)
- 📑 Сборка комикса в PDF
- 💾 Экспорт отдельных изображений

## ⚙️ Настройка Fooocus API

1. Запустите Fooocus с включенным API:
```bash
python entry_with_update.py --listen --port 7865
```

2. Убедитесь, что API доступен по адресу `http://localhost:7865`

## 📁 Структура проекта

```
comics/
├── app.py                 # Точка входа
├── requirements.txt       # Зависимости
├── API/
│   └── fooocus_api.py     # Обертка для Fooocus API
├── Logic/
│   ├── config.py          # Конфигурация
│   ├── text_processor.py  # Обработка текста
│   ├── prompt_builder.py  # Построение промптов
│   ├── panel_generator.py # Генерация панелей
│   ├── comic_builder.py   # Сборка комикса
│   └── text_renderer.py   # Рендеринг текста на панелях
└── UI/
    ├── sidebar.py         # Боковая панель
    ├── import_tab.py      # Вкладка импорта
    ├── generate_tab.py    # Вкладка генерации
    └── export_tab.py      # Вкладка экспорта
```

## 🎨 Стили комиксов

- Marvel/DC стиль
- Манга
- Европейский комикс
- Вебтун
- Минимализм

## 📝 Лицензия

MIT