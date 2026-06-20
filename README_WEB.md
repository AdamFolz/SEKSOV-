# SEKSOV Web Application

🚀 Веб-версия приложения для отслеживания введения препаратов.

## Структура проекта

```
SEKSOV-/
├── backend/                 # FastAPI backend
│   ├── main.py             # Точка входа
│   ├── database.py         # Конфигурация БД
│   ├── requirements.txt    # Зависимости Python
│   ├── .env.example        # Пример переменных окружения
│   ├── api/                # API endpoints
│   │   ├── users.py
│   │   ├── batches.py
│   │   └── injections.py
│   ├── models/             # SQLAlchemy models
│   │   ├── user.py
│   │   ├── batch.py
│   │   └── injection.py
│   └── schemas/            # Pydantic schemas
│       ├── user.py
│       ├── batch.py
│       └── injection.py
└── frontend/               # React frontend
    ├── src/
    │   ├── main.jsx        # Точка входа
    │   ├── App.jsx         # Главный компонент
    │   ├── App.css         # Стили
    │   └── index.css       # Глобальные стили
    ├── package.json        # NPM зависимости
    ├── vite.config.js      # Конфигурация Vite
    ├── .env.example        # Пример переменных окружения
    └── index.html          # HTML шаблон
```

## Установка и запуск

### Backend (FastAPI)

```bash
cd backend

# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Скопировать .env.example в .env
cp .env.example .env

# Запустить сервер
python main.py
```

API будет доступно на `http://localhost:8000`
API документация: `http://localhost:8000/docs`

### Frontend (React + Vite)

```bash
cd frontend

# Установить зависимости
npm install

# Скопировать .env.example в .env
cp .env.example .env

# Запустить dev сервер
npm run dev
```

Приложение будет доступно на `http://localhost:3000`

## Технологии

### Backend
- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **Uvicorn** - ASGI сервер
- **Pydantic** - валидация данных
- **Python-dotenv** - управление переменными окружения

### Frontend
- **React 18** - UI библиотека
- **Vite** - быстрый сборщик
- **Axios** - HTTP клиент

## API Endpoints (планы)

### Users
- `GET /api/users/` - список пользователей
- `POST /api/users/` - создание пользователя
- `GET /api/users/{id}` - получить пользователя
- `PUT /api/users/{id}` - обновить пользователя
- `DELETE /api/users/{id}` - удалить пользователя

### Batches
- `GET /api/batches/` - список партий
- `POST /api/batches/` - создать партию
- `GET /api/batches/{id}` - получить партию
- `PUT /api/batches/{id}` - обновить партию
- `DELETE /api/batches/{id}` - удалить партию

### Injections
- `GET /api/injections/` - список введений
- `POST /api/injections/` - записать введение
- `GET /api/injections/{id}` - получить введение
- `DELETE /api/injections/{id}` - удалить введение

## Следующие шаги

1. ✅ Создана базовая структура
2. ⏳ Реализовать CRUD операции в API
3. ⏳ Создать компоненты React
4. ⏳ Реализовать аутентификацию
5. ⏳ Добавить тесты
6. ⏳ Развернуть на сервер

## Разработка

Ветка для разработки: `web-app-dev`

Для внесения изменений:
```bash
git checkout web-app-dev
# Ваши изменения
git add .
git commit -m "Описание изменений"
git push origin web-app-dev
```

## Лицензия

MIT
