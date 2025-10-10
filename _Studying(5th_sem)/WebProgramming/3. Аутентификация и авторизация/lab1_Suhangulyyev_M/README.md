# **API новостного портала с авторизацией через GitHub**

Выполнил:

Суханкулиев Мухаммет,
студент группы N3346

### 1. РАЗРАБОТКА И МОДЕРНИЗАЦИЯ API

#### 1.1. Проектирование моделей данных

Исходная модель данных была расширена для поддержки новых требований:

*   **User**: В модель добавлено поле `role` (enum: `USER`, `VERIFIED_AUTHOR`, `ADMIN`) и `hashed_password`. Поле `is_verified_author` было заменено на более гибкую систему ролей.
*   **RefreshToken**: Добавлена новая модель для хранения refresh-токенов. Она связана с пользователем и содержит информацию о сессии, включая `user_agent` и срок действия.

Связи между сущностями (`User`, `News`, `Comment`) остались прежними (один-ко-многим), включая каскадное удаление.

![Схема базы данных](./db_schema.png)

#### 1.2. Описание архитектуры и реализации

Проект сохраняет многослойную архитектуру (Controller-Service-Repository), которая была расширена для поддержки аутентификации:

*   **API / Controllers (`app/api/`)**: Добавлен новый роутер `auth.py` для всех эндпоинтов, связанных с аутентификацией. В остальные роутеры добавлена логика проверки токенов и прав доступа с помощью системы зависимостей FastAPI (`Depends`).
*   **Services (`app/services/`)**: В сервисы добавлена бизнес-логика, связанная с правами доступа (проверка роли пользователя перед созданием новости и т.п.).
*   **Core (`app/core/`)**: Создан новый модуль `security.py`, инкапсулирующий всю логику работы с JWT, хешированием паролей (Argon2) и генерацией токенов.
*   **Dependencies (`app/api/dependencies.py`)**: Этот модуль стал центральным элементом системы безопасности. В нем реализованы зависимости для:
    *   Получения текущего пользователя из JWT (`get_current_user`).
    *   Проверки ролей (`require_role`).
    *   "Резолверы" — зависимости, которые не только получают объект из БД, но и сразу проверяют права текущего пользователя на доступ к нему (`get_news_for_update`, `get_comment_for_update`).

**Подробное описание ролей и сводная таблица прав доступа находятся в файле [docs/auth.md](./docs/auth.md).**

#### 1.3. Порядок запуска

**Требования:**
-   Python 3.10+
-   Poetry (менеджер зависимостей)
-   Docker и Docker Compose

**Шаги для запуска:**
1.  Клонировать репозиторий:
    ```bash
    git clone https://github.com/itmo-webdev/lab1_Suhangulyyev_M.git
    cd lab1_Suhangulyyev_M
    ```
2.  Создать и заполнить файл `.env` в корне проекта, используя предоставленный шаблон. **Обязательно замените `github_client_id` и `github_client_secret` на свои ключи**, полученные при регистрации OAuth-приложения в GitHub.
    ```env
    # Асинхронный URL для FastAPI
    DATABASE_URL="postgresql+asyncpg://news_muhammet:news_password@localhost:5432/news_db"

    # Синхронный URL для Alembic
    SYNC_DATABASE_URL="postgresql+psycopg2://news_muhammet:news_password@localhost:5432/news_db"

    # JWT
    SECRET_KEY="a_very_secret_key_that_is_long_and_secure"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    REFRESH_TOKEN_EXPIRE_DAYS=30

    # GitHub OAuth
    GITHUB_CLIENT_ID="your_github_client_id"
    GITHUB_CLIENT_SECRET="your_github_client_secret"
    GITHUB_CALLBACK_URL="http://127.0.0.1:8000/api/v1/auth/github/callback"

    # Test Databases (для pytest)
    TEST_DATABASE_URL="postgresql+asyncpg://news_muhammet:news_password@localhost:5432/news_db_test"
    SYNC_TEST_DATABASE_URL="postgresql+psycopg2://news_muhammet:news_password@localhost:5432/news_db_test"
    ```

3.  Запустить базу данных PostgreSQL с помощью Docker:
    ```bash
    docker-compose up -d
    ```

4.  Установить все зависимости:
    ```bash
    poetry install --with dev
    ```
    (dev - для автотестирования)

5.  Применить миграции Alembic для создания схемы БД и наполнения ее моковыми данными:
    ```bash
    poetry run alembic upgrade head
    ```

6.  Запустить FastAPI приложение:
    ```bash
    poetry run uvicorn app.main:app --reload
    ```
    Приложение будет доступно по адресу `http://127.0.0.1:8000`, а интерактивная документация (Swagger UI) — по `http://127.0.0.1:8000/docs`.

#### 1.4. Тестирование и проверка результата

**Автоматизированное тестирование:**

Проект покрыт набором из **36 интеграционных тестов** с использованием `pytest`, `httpx` и `pytest-mock`. Тесты проверяют не только успешные сценарии, но и обработку ошибок, права доступа для разных ролей и логику OAuth с помощью моков.

Для запуска тестов используется команда:
```bash
poetry run pytest
```

**Ручная проверка (Примеры `curl`):**

Ниже приведен полный сценарий взаимодействия с API через `curl`. Команды демонстрируют основной функционал, включая регистрацию, аутентификацию и управление контентом.

**1. Сценарий Обычного Пользователя (`USER`)**

```bash
# 1.1. Регистрация нового пользователя
curl -X 'POST' 'http://127.0.0.1:8000/api/v1/auth/register' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Regular User",
  "email": "user@example.com",
  "password": "strongpassword"
}'

# 1.2. Логин для получения токенов
# В ответе скопируйте значения "access_token" и "refresh_token".
curl -X 'POST' 'http://127.0.0.1:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=user@example.com&password=strongpassword'

# 1.3. Попытка создать новость (неуспешно)
# Ожидаемый результат: ошибка 403 Forbidden, т.к. роль 'USER'.
curl -X 'POST' 'http://127.0.0.1:8000/api/v1/news/' \
  -H "Authorization: Bearer <PASTE_USER_ACCESS_TOKEN_HERE>" \
  -H 'Content-Type: application/json' \
  -d '{"title": "My First News", "content": {}}'
```

**2. Сценарий Верифицированного Автора (`VERIFIED_AUTHOR`)**

*Миграции уже создают пользователя `author@example.com` с ролью `VERIFIED_AUTHOR` и паролем `dummy_password`. Используйте эти данные для входа.*

```bash
# 2.1. Логин от имени автора для получения токенов.
# Скопируйте "access_token" из ответа для последующих команд.
curl -X 'POST' 'http://127.0.0.1:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=author@example.com&password=dummy_password'

# 2.2. Создание новости от имени автора
# Скопируйте "id" созданной новости из JSON-ответа.
curl -X 'POST' 'http://127.0.0.1:8000/api/v1/news/' \
  -H "Authorization: Bearer <PASTE_AUTHOR_ACCESS_TOKEN_HERE>" \
  -H 'Content-Type: application/json' \
  -d '{"title": "An Authoritative Article", "content": {"text": "Content by a verified author."}}'

# 2.3. Редактирование своей новости
# Вставьте ID новости в URL.
curl -X 'PATCH' 'http://127.0.0.1:8000/api/v1/news/<PASTE_NEWS_ID_HERE>' \
  -H "Authorization: Bearer <PASTE_AUTHOR_ACCESS_TOKEN_HERE>" \
  -H 'Content-Type: application/json' \
  -d '{"title": "An Updated Title"}'

# 2.4. Создание комментария к новости
# Скопируйте "id" созданного комментария.
curl -X 'POST' 'http://127.0.0.1:8000/api/v1/comments/' \
  -H "Authorization: Bearer <PASTE_AUTHOR_ACCESS_TOKEN_HERE>" \
  -H 'Content-Type: application/json' \
  -d '{"text": "My first comment!", "news_id": "<PASTE_NEWS_ID_HERE>"}'

# 2.5. Удаление своей новости (вместе с комментарием, благодаря cascade)
curl -X 'DELETE' 'http://127.0.0.1:8000/api/v1/news/<PASTE_NEWS_ID_HERE>' \
  -H "Authorization: Bearer <PASTE_AUTHOR_ACCESS_TOKEN_HERE>"
```

**3. Сценарий Администратора (`ADMIN`)**

*Этот сценарий демонстрирует права админа на управление **чужим** контентом, созданным автором на шаге 2.2.*

```bash
# 3.1. Логин от имени администратора
curl -X 'POST' 'http://127.0.0.1:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=admin_password'
# Скопируйте "access_token" администратора.

# 3.2. Администратор редактирует чужую новость
# Вставьте ID новости, созданной автором на шаге 2.2.
curl -X 'PATCH' 'http://127.0.0.1:8000/api/v1/news/<PASTE_NEWS_ID>' \
  -H "Authorization: Bearer <PASTE_ADMIN_ACCESS_TOKEN_HERE>" \
  -H 'Content-Type: application/json' \
  -d '{"title": "Title Edited by Admin"}'

# 3.3. Администратор удаляет чужую новость
curl -X 'DELETE' 'http://127.0.0.1:8000/api/v1/news/<PASTE_NEWS_ID>' \
  -H "Authorization: Bearer <PASTE_ADMIN_ACCESS_TOKEN_HERE>"

# 3.4. Администратор удаляет другого пользователя (например, user@example.com)
# Сначала нужно получить ID пользователя. Сделайте GET /api/v1/users/, найдите ID и вставьте его.
curl -X 'DELETE' 'http://127.0.0.1:8000/api/v1/users/<PASTE_USER_ID_TO_DELETE>' \
  -H "Authorization: Bearer <PASTE_ADMIN_ACCESS_TOKEN_HERE>"
```

**4. Управление сессиями и GitHub**

```bash
# 4.1. Просмотр своих активных сессий
curl -X 'GET' 'http://127.0.0.1:8000/api/v1/auth/sessions/me' \
  -H "Authorization: Bearer <PASTE_YOUR_ACCESS_TOKEN_HERE>"

# 4.2. Обновление токенов
# Скопируйте новый "refresh_token" из ответа для следующего шага.
curl -X 'POST' 'http://127.0.0.1:8000/api/v1/auth/refresh' \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token": "<PASTE_YOUR_REFRESH_TOKEN_HERE>"}'

# 4.3. Выход из системы (удаление сессии по refresh-токену)
curl -X 'POST' 'http://127.0.0.1:8000/api/v1/auth/logout' \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token": "<PASTE_THE_NEW_REFRESH_TOKEN_HERE>"}'

# 4.4. Авторизация через GitHub
# Этот процесс требует браузера. Откройте в браузере следующую ссылку:
# http://127.0.0.1:8000/api/v1/auth/github/login
# После успешной аутентификации на GitHub, вас перенаправит на callback URL,
# а в теле страницы будет JSON с вашими access и refresh токенами.
```
