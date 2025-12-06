# ITMO News Client 📰

Фронтенд-приложение для новостного API, разработанное на **React 19 + Vite**.
Реализован полный цикл взаимодействия с API, ролевая модель (RBAC), автоматическое обновление токенов (Refresh Token) и дизайн в стиле Windows 11.

---

### Особенность взаимодействия с API

Текущий Бэкенд требует авторизацию для получения списка новостей (возвращает 401). 
Чтобы избежать бесконечного редиректа, на главной странице для гостей реализован вывод сообщения с просьбой авторизоваться.

---

## 🚀 1. Запуск Бэкенда (Важно!)

Фронтенд требует запущенного API.
**Важно:** Убедитесь, что в `app/main.py` настроен **CORS** для `http://localhost:5173`.

**1. Клонирование или обновление репозитория:**

Если проекта нет локально:
```bash
git clone https://github.com/itmo-webdev/lab1_Suhangulyyev_M.git
cd lab1_Suhangulyyev_M
```

Если проект уже есть (**обязательно обновите**, чтобы получить настройки CORS):
```bash
cd lab1_Suhangulyyev_M
git pull origin main
```

**2. Настройка окружения:**
Создайте файл `.env` в корне бэкенда и вставьте туда этот конфиг:
```env
# DB & Async
DATABASE_URL="postgresql+asyncpg://news_muhammet:news_password@localhost:5432/news_db"
SYNC_DATABASE_URL="postgresql+psycopg2://news_muhammet:news_password@localhost:5432/news_db"

# Security
SECRET_KEY="super_secret_key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# GitHub OAuth (Mock keys)
GITHUB_CLIENT_ID="Ov23liU1PV7DZor3kZdN"
GITHUB_CLIENT_SECRET="d3eb7023ec32b7a31413b741e93232e2409fb6d1"
GITHUB_CALLBACK_URL="http://127.0.0.1:8000/api/v1/auth/github/callback"

# Infrastructure
REDIS_HOST=localhost
REDIS_PORT=6379
CELERY_BROKER_URL="redis://localhost:6379/1"
CELERY_RESULT_BACKEND="redis://localhost:6379/2"
DB_ECHO_LOG=True
```

**3. Запуск инфраструктуры и сервера:**
```bash
# 1. Запуск БД и Redis
docker-compose up -d --build

# 2. Применение миграций (создаст таблицы и тестовых юзеров)
poetry install --with dev
poetry run alembic upgrade head

# 3. Запуск API
poetry run uvicorn app.main:app --reload
```
*API доступно по адресу: `http://127.0.0.1:8000`*

---

## ⚡ 2. Запуск Фронтенда

**1. Клонирование репозитория:**
```bash
git clone https://github.com/itmo-webdev/lab6_Suhangulyyev_M.git
cd lab6_Suhangulyyev_M
```

**2. Установка зависимостей:**
```bash
npm install
```

**3. Запуск сервера разработки:**
```bash
npm run dev
```
Откройте приложение: [http://localhost:5173](http://localhost:5173)

---

## 🔑 Тестовые данные (Mock Data)

При применении миграций в БД автоматически создаются следующие пользователи:

| Роль | Email | Пароль | Возможности |
| :--- | :--- | :--- | :--- |
| **ADMIN** | `admin@example.com` | `admin_password` | Полный доступ, Админка, Удаление любых данных |
| **AUTHOR** | `author@example.com` | `dummy_password` | Создание новостей, Редактирование своих новостей |
| **USER** | `user@example.com` | `dummy_password` | Просмотр, Комментарии, Редактирование профиля |

---

## 🧪 Сценарии тестирования

### 1. Гость
*   Открытие главной -> Заглушка "Доступ ограничен".
*   Попытка открыть `/profile` или `/create` -> Редирект на вход.

### 2. Пользователь (User)
*   Зарегистрироваться или войти как `user@example.com`.
*   Просмотреть ленту новостей.
*   Оставить комментарий.
*   В профиле: изменить имя и загрузить аватарку с ПК.

### 3. Автор (Verified Author)
*   Войти как `author@example.com`.
*   Нажать кнопку **"+ Создать"** в шапке -> Создать новость.
*   Зайти в свою новость -> Отредактировать её.

### 4. Администратор (Admin)
*   Войти как `admin@example.com`.
*   Нажать ссылку **"Админка"** в шапке -> Удалить любого пользователя.
*   Зайти в любую новость -> Удалить чужой комментарий или саму новость.

### 5. Технический (Refresh Token)
*   Войти в систему.
*   В DevTools (Application -> Local Storage) удалить `access_token` (оставив `refresh_token`).
*   Обновить страницу или выполнить действие.
*   **Результат:** Сессия не прерывается, токен обновляется автоматически.
