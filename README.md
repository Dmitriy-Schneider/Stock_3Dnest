# Stock-3DNest — Система управления складом и интеллектуальный 3D-раскрой

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightblue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Production-success.svg)

**Интегрированная система управления складом металлопроката с интеллектуальным 3D-раскроем**

[Демонстрация](#демонстрация) • [Установка](#установка) • [API](#api) • [Архитектура](#архитектура)

</div>

---

## О проекте

**Stock-3DNest** — производственная система для металлообрабатывающих предприятий, объединяющая управление складом с интеллектуальными алгоритмами 3D-раскроя.

### Решаемые задачи

- **Поиск материала**: оператор ленточнопильного станка быстро находит подходящую заготовку на складе
- **Оптимальный раскрой**: алгоритм рассчитывает оптимальную схему резки с минимизацией отходов
- **Визуализация**: 3D-модель схемы раскроя для наглядного понимания последовательности резов
- **Мобильность**: доступ через Telegram-бота прямо из цеха

### Ключевые преимущества

| Функция | Описание |
|---------|----------|
| Автоматический парсинг | Импорт остатков из 1С (Excel) в SQLite при запуске |
| Умный поиск | Фильтрация по профилю, марке стали, размерам |
| 3D-визуализация | Интерактивная схема раскроя (Three.js) |
| REST API | Интеграция с внешними системами |
| Docker-ready | Развёртывание одной командой |

---

## Демонстрация

### Веб-интерфейс склада

Адаптивный интерфейс для поиска и фильтрации остатков металлопроката:

![Warehouse Interface](docs/images/warehouse_main.png)

### 3D-визуализация раскроя

Интерактивная 3D-модель с возможностью вращения и масштабирования:

![3D Cutting](docs/images/cutting_3d.png)

### Telegram-бот

Доступ к функционалу системы через мессенджер:

![Telegram Bot](docs/images/telegram_bot.png)

---

## Архитектура

Система состоит из трёх модулей:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Stock-3DNest                              │
├─────────────────┬─────────────────────┬─────────────────────────┤
│   Модуль 1      │      Модуль 2       │       Модуль 3          │
│   СКЛАД         │   3D-РАСКРОЙ        │    TELEGRAM-БОТ         │
│   (Open Source) │   (Интеллект.       │   (Интеллект.           │
│                 │    собственность)   │    собственность)       │
├─────────────────┼─────────────────────┼─────────────────────────┤
│ • Excel парсер  │ • Guillotine Bin    │ • aiogram 3             │
│ • SQLite база   │   Packing алгоритм  │ • PDF отчёты            │
│ • REST API      │ • Three.js          │ • GPT интеграция        │
│ • Web UI        │   визуализация      │ • FSM диалоги           │
└─────────────────┴─────────────────────┴─────────────────────────┘
```

### Модуль 1 — Склад (Open Source)

Веб-интерфейс для управления и поиска остатков:

- **Excel парсинг** — автоматический импорт из выгрузок 1С (.xlsx)
- **Умный поиск** — фильтрация по типу профиля, марке стали, размерам
- **Авто-определение** — автоматический выбор актуального файла по дате
- **REST API** — эндпоинты для интеграции с внешними системами
- **Адаптивный UI** — работает на любых устройствах

### Модуль 2 — 3D-раскрой (Интеллектуальная собственность)

> Исходный код не публикуется. Описание принципов работы ниже.

Интеллектуальный алгоритм оптимального раскроя металлических блоков:

- **3D Guillotine Bin Packing** — алгоритм гильотинного раскроя
- **Автоподбор заготовки** — выбор оптимального блока со склада
- **3D-визуализация** — интерактивная модель на Three.js
- **Последовательность резов** — пошаговая инструкция для оператора

### Модуль 3 — Telegram-бот (Интеллектуальная собственность)

> Исходный код не публикуется. Описание принципов работы ниже.

Telegram-бот, дублирующий функционал Модулей 1 и 2:

- **aiogram 3** — асинхронный фреймворк
- **PDF-отчёты** — генерация отчётов со схемой раскроя
- **OpenAI GPT** — интеллектуальная обработка запросов
- **FSM** — конечный автомат для управления диалогами

---

## Технологии

| Технология | Назначение |
|------------|------------|
| **Python 3.11+** | Основной язык |
| **FastAPI** | REST API сервер |
| **SQLite** | База данных |
| **openpyxl** | Парсинг Excel |
| **Docker** | Контейнеризация |
| **Three.js** | 3D-визуализация (Модуль 2) |
| **aiogram 3** | Telegram-бот (Модуль 3) |
| **OpenAI API** | GPT интеграция (Модуль 3) |

---

## Установка

### Docker (рекомендуется)

```bash
# Клонирование репозитория
git clone https://github.com/Dmitriy-Schneider/Stock_3Dnest.git
cd Stock_3Dnest

# Создание директории для данных
mkdir -p data/warehouse

# Копирование Excel-файла с остатками из 1С
cp /путь/к/Склад.xlsx data/warehouse/

# Запуск
docker-compose up -d

# Открыть в браузере: http://localhost:3001/warehouse
```

### Локальная установка

```bash
# Клонирование
git clone https://github.com/Dmitriy-Schneider/Stock_3Dnest.git
cd Stock_3Dnest

# Виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Зависимости
pip install -r requirements-web.txt

# Данные
mkdir -p data/warehouse
cp /путь/к/Склад.xlsx data/warehouse/

# Запуск
uvicorn server_fastapi:app --host 0.0.0.0 --port 3001

# Открыть: http://localhost:3001/warehouse
```

---

## API

### Эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/warehouse` | Веб-интерфейс склада |
| GET | `/api/warehouse/items` | Список всех позиций |
| GET | `/api/warehouse/items?profile=круг` | Поиск по профилю |
| GET | `/api/warehouse/items?steel_grade=09Г2С` | Поиск по марке стали |
| POST | `/api/warehouse/sync` | Синхронизация с Excel |
| GET | `/docs` | Swagger UI документация |

### Пример запроса

```bash
# Получить все круги из стали 09Г2С
curl "http://localhost:3001/api/warehouse/items?profile=круг&steel_grade=09Г2С"
```

### Пример ответа

```json
{
  "items": [
    {
      "id": 1,
      "profile": "Круг",
      "steel_grade": "09Г2С",
      "diameter": 150,
      "length": 3000,
      "quantity": 5,
      "weight": 412.5
    }
  ],
  "total": 1
}
```

---

## Структура проекта

```
Stock_3Dnest/
├── server_fastapi.py         # FastAPI REST API сервер
├── warehouse_parser.py       # Парсер Excel (выгрузки 1С)
├── database.py               # Слой работы с SQLite
├── requirements-web.txt      # Python зависимости
│
├── static/
│   ├── warehouse.html        # UI склада (Модуль 1)
│   ├── warehouse.js          # Логика UI склада
│   ├── warehouse.css         # Стили склада
│   ├── index.html            # UI 3D-раскроя (Модуль 2, ИС)
│   └── app.js                # 3D визуализация (Модуль 2, ИС)
│
├── data/
│   └── warehouse/            # Excel файлы (не в репозитории)
│
├── BotCut/                   # Telegram-бот (Модуль 3, ИС)
│   ├── EnvExample.txt        # Пример переменных окружения
│   └── requirements.txt      # Зависимости бота
│
├── docker-compose.yml        # Docker Compose конфигурация
├── Dockerfile.web            # Dockerfile веб-сервера
├── Dockerfile.bot            # Dockerfile бота
└── LICENSE                   # Лицензия MIT + ИС
```

---

## Лицензирование

### Открытые компоненты (MIT License)

| Компонент | Статус |
|-----------|--------|
| warehouse_parser.py | Open Source |
| database.py | Open Source |
| server_fastapi.py | Open Source |
| static/warehouse.* | Open Source |
| Docker конфигурация | Open Source |

### Интеллектуальная собственность

| Компонент | Статус |
|-----------|--------|
| server.py (алгоритм раскроя) | Закрытый код |
| static/app.js (3D визуализация) | Закрытый код |
| BotCut/*.py (Telegram-бот) | Закрытый код |
| data/warehouse/*.xlsx | Приватные данные |

Подробности в файле [LICENSE](LICENSE).

---

## Автор

**Дмитрий Шнайдер** — [@Dmitriy-Schneider](https://github.com/Dmitriy-Schneider)

### Контакты

- GitHub: [Dmitriy-Schneider](https://github.com/Dmitriy-Schneider)
- Telegram: по запросу

---

## Благодарности

- [FastAPI](https://fastapi.tiangolo.com/) — современный веб-фреймворк
- [Three.js](https://threejs.org/) — 3D-графика в браузере
- [aiogram](https://aiogram.dev/) — асинхронный Telegram-бот

---

<div align="center">

**Stock-3DNest** — От выгрузки 1С до оптимального раскроя за секунды

Если проект был полезен, поставьте звезду!

⭐ Star this repo ⭐

</div>
