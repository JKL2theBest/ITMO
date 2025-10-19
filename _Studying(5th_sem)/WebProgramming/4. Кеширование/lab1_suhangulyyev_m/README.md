# **API новостного портала с кэшированием на Redis**

Выполнил:

Суханкулиев Мухаммет,
студент группы N3346

### 1. РАЗРАБОТКА И МОДЕРНИЗАЦИЯ API

#### 1.1. Проектирование моделей данных

Исходная модель данных была расширена для поддержки аутентификации и ролевой модели:

*   **User**: В модель добавлено поле `role` (enum: `USER`, `VERIFIED_AUTHOR`, `ADMIN`) и `hashed_password`. Поле `is_verified_author` было заменено на более гибкую систему ролей.
*   **RefreshToken (Удалено)**: Модель для хранения refresh-токенов была **полностью удалена из PostgreSQL**. Вся логика управления сессиями перенесена в **Redis** для повышения производительности.

Связи между основными сущностями (`User`, `News`, `Comment`) остались прежними (один-ко-многим), включая каскадное удаление.

![Обновленная схема базы данных](./db_schema.png)

#### 1.2. Описание архитектуры и реализации

Проект сохраняет многослойную архитектуру (Controller-Service-Repository), которая была расширена для поддержки аутентификации и кэширования:

*   **API / Controllers (`app/api/`)**: Добавлен роутер `auth.py` для аутентификации. В остальные роутеры встроена проверка токенов и прав доступа через систему зависимостей FastAPI.
*   **Services (`app/services/`)**: Реализован `AuthService` для управления сессиями в Redis. Бизнес-логика в `NewsService` и `UserService` дополнена механизмами кэширования.
*   **Core (`app/core/`)**: Модуль `security.py` инкапсулирует логику работы с JWT и хешированием паролей.
*   **Dependencies (`app/api/dependencies.py`)**: Центральный элемент системы безопасности, реализующий зависимости для получения текущего пользователя, проверки ролей и прав доступа к конкретным объектам.

**Подробное описание ролей и прав доступа находится в файле [docs/auth.md](./docs/auth.md).**

#### 1.2.1. Взаимодействие с БД и кэшем (Redis)

С внедрением Redis архитектура обработки запросов была оптимизирована:

*   **Сессии пользователей**: Таблица `refresh_tokens` была полностью удалена из PostgreSQL. Вся информация о сессиях (refresh-токены, user-agent) теперь хранится в Redis. Это обеспечивает максимально быстрый доступ при операциях `login`, `refresh` и `logout`.
*   **Кэширование "теплых" данных**: Для часто запрашиваемых, но редко изменяемых данных (новости и информация о пользователях), применяется паттерн *Cache-aside (lazy loading)*.
    *   При запросе объекта (например, новости по ID) приложение сначала проверяет его наличие в кэше Redis.
    *   Если данные найдены, они возвращаются немедленно, минуя запрос к БД.
    *   Если в кэше данных нет, приложение обращается к PostgreSQL, получает данные, сохраняет их в Redis с TTL (5 минут) и после этого возвращает клиенту.
*   **Инвалидация кэша**: При любой операции изменения или удаления сущности (`PATCH /news/{id}`), соответствующая запись в кэше Redis немедленно удаляется (инвалидируется).

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
2.  Создать и заполнить файл `.env` в корне проекта по шаблону ниже. **Обязательно замените `GITHUB_CLIENT_ID` и `GITHUB_CLIENT_SECRET` на свои ключи.**
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

    # Redis
    REDIS_HOST=localhost
    REDIS_PORT=6379
    ```

3.  Запустить базу данных PostgreSQL и кэш Redis с помощью Docker:
    ```bash
    docker-compose up -d
    ```

4.  Установить все зависимости:
    ```bash
    poetry install --with dev
    ```

5.  Применить миграции Alembic для создания/обновления схемы БД:
    ```bash
    poetry run alembic upgrade head
    ```

6.  Запустить FastAPI приложение:
    ```bash
    poetry run uvicorn app.main:app --reload
    ```
    Приложение будет доступно по `http://127.0.0.1:8000`, документация — по `http://127.0.0.1:8000/docs`.

---

#### 1.4. Тестирование и проверка результата

**Автоматизированное тестирование:**

Проект покрыт набором из **39 интеграционных и юнит-тестов**. Тесты проверяют основной функционал, права доступа, логику OAuth, а также корректность работы кэширования (попадания, промахи, инвалидация).

Для запуска тестов используется команда:
```bash
poetry run pytest
```

**Ручная проверка (Однострочные `curl`):**

Ниже приведен полный сценарий взаимодействия с API через `curl` в командной строке Windows. Сценарии самодостаточны и не зависят друг от друга.

**ВАЖНОЕ ПРАВИЛО:** После выполнения команды, которая возвращает `access_token` или `id`, вам нужно будет **вручную скопировать** это значение (без кавычек) и **вставить** его в следующую команду, где есть соответствующий placeholder.

---

### Сценарий 1: Обычный Пользователь (`USER`)

```bash
:: 1.1. Регистрация нового пользователя 'testuser-curl@example.com'
curl -X POST "http://127.0.0.1:8000/api/v1/auth/register" -H "Content-Type: application/json" -d "{ \"name\": \"CURL Test User\", \"email\": \"testuser-curl@example.com\", \"password\": \"strongpassword123\" }"
```
```bash
:: 1.2. Вход в систему. ВАЖНО: Скопируйте "access_token" и "refresh_token" из ответа для следующих шагов.
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=testuser-curl@example.com&password=strongpassword123"
```
```bash
:: 1.3. Попытка создать новость (ожидается ошибка 403 Forbidden). Замените <USER_TOKEN> на скопированный 'access_token'.
curl -X POST "http://127.0.0.1:8000/api/v1/news/" -H "Authorization: Bearer <USER_TOKEN>" -H "Content-Type: application/json" -d "{ \"title\": \"My First News\", \"content\": {\"text\": \"some text\"} }"
```
```bash
:: 1.4. Получение списка новостей. ВАЖНО: Скопируйте 'id' первой новости из списка (например, "409a1ca6-e94a-4605-9fe9-20937bb68b62").
curl -X GET "http://127.0.0.1:8000/api/v1/news/" -H "Authorization: Bearer <USER_TOKEN>"
```
```bash
:: 1.5. Создание комментария. ВАЖНО: Замените <NEWS_ID> и скопируйте 'id' созданного комментария.
curl -X POST "http://127.0.0.1:8000/api/v1/comments/" -H "Authorization: Bearer <USER_TOKEN>" -H "Content-Type: application/json" -d "{ \"text\": \"This is my first comment!\", \"news_id\": \"<NEWS_ID>\" }"
```
```bash
:: 1.6. Обновление своего комментария. Замените <COMMENT_ID> на ID из шага 1.5.
curl -X PATCH "http://127.0.0.1:8000/api/v1/comments/<COMMENT_ID>" -H "Authorization: Bearer <USER_TOKEN>" -H "Content-Type: application/json" -d "{ \"text\": \"I have updated my comment.\" }"
```
```bash
:: 1.7. Удаление своего комментария.
curl -X DELETE "http://127.0.0.1:8000/api/v1/comments/<COMMENT_ID>" -H "Authorization: Bearer <USER_TOKEN>"
```
```bash
:: 1.8. Обновление токенов. ВАЖНО: Замените <USER_REFRESH_TOKEN> и скопируйте новый 'refresh_token' из ответа.
curl -X POST "http://127.0.0.1:8000/api/v1/auth/refresh" -H "Content-Type: application/json" -d "{ \"refresh_token\": \"<USER_REFRESH_TOKEN>\" }"
```
```bash
:: 1.9. Выход из системы. Замените <NEW_REFRESH_TOKEN> на токен из шага 1.8.
curl -X POST "http://127.0.0.1:8000/api/v1/auth/logout" -H "Content-Type: application/json" -d "{ \"refresh_token\": \"<NEW_REFRESH_TOKEN>\" }"
```

---

### Сценарий 2: Верифицированный Автор (`VERIFIED_AUTHOR`)

```bash
:: 2.1. Вход в систему от имени автора ('author@example.com', пароль 'dummy_password'). ВАЖНО: Скопируйте 'access_token' автора.
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=author@example.com&password=dummy_password"
```
```bash
:: 2.2. Создание новой новости. ВАЖНО: Скопируйте 'id' созданной новости (например, "f8d6a4c2-...").
curl -X POST "http://127.0.0.1:8000/api/v1/news/" -H "Authorization: Bearer <AUTHOR_TOKEN>" -H "Content-Type: application/json" -d "{ \"title\": \"Article by Author\", \"content\": {\"body\": \"This is a protected article.\"} }"
```
```bash
:: 2.3. Обновление своей новости. Замените <NEWS_ID_FROM_2.2> на ID из шага 2.2.
curl -X PATCH "http://127.0.0.1:8000/api/v1/news/<NEWS_ID_FROM_2.2>" -H "Authorization: Bearer <AUTHOR_TOKEN>" -H "Content-Type: application/json" -d "{ \"title\": \"Updated Title by Author\" }"
```
```bash
:: 2.4. Удаление своей новости. Замените <NEWS_ID_FROM_2.2> на ID из шага 2.2.
curl -X DELETE "http://127.0.0.1:8000/api/v1/news/<NEWS_ID_FROM_2.2>" -H "Authorization: Bearer <AUTHOR_TOKEN>"```
```

---


### Сценарий 3: Администратор (`ADMIN`)

```bash
:: -- ШАГ 1: Подготовка контента от имени АВТОРА --
:: 3.1. Войдите как автор (см. 2.1) и скопируйте 'access_token' автора.
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=author@example.com&password=dummy_password"
```
```bash
:: 3.2. АВТОР создает новость. ВАЖНО: Скопируйте 'id' этой новости (назовем его NEWS_ID_FOR_ADMIN).
curl -X POST "http://127.0.0.1:8000/api/v1/news/" -H "Authorization: Bearer <AUTHOR_TOKEN>" -H "Content-Type: application/json" -d "{ \"title\": \"Content for Admin Test\", \"content\": {} }"
```
```bash
:: 3.3. АВТОР создает комментарий. ВАЖНО: Скопируйте 'id' этого комментария (назовем его COMMENT_ID_FOR_ADMIN).
curl -X POST "http://127.0.0.1:8000/api/v1/comments/" -H "Authorization: Bearer <AUTHOR_TOKEN>" -H "Content-Type: application/json" -d "{ \"text\": \"A comment to be managed by admin\", \"news_id\": \"<NEWS_ID_FOR_ADMIN>\" }"
```
```bash
:: -- ШАГ 2: Вход и действия от имени АДМИНА --
:: 3.4. Вход в систему как администратор ('admin@example.com', пароль 'admin_password'). ВАЖНО: Скопируйте 'access_token' админа.
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin@example.com&password=admin_password"
```
```bash
:: 3.5. Админ редактирует ЧУЖУЮ новость. Замените <NEWS_ID_FOR_ADMIN>.
curl -X PATCH "http://127.0.0.1:8000/api/v1/news/<NEWS_ID_FOR_ADMIN>" -H "Authorization: Bearer <ADMIN_TOKEN>" -H "Content-Type: application/json" -d "{ \"title\": \"Forcefully Updated by Admin\" }"
```
```bash
:: 3.6. Админ удаляет ЧУЖОЙ комментарий. Замените <COMMENT_ID_FOR_ADMIN>.
curl -X DELETE "http://127.0.0.1:8000/api/v1/comments/<COMMENT_ID_FOR_ADMIN>" -H "Authorization: Bearer <ADMIN_TOKEN>"
```
```bash
:: 3.7. Админ удаляет ЧУЖУЮ новость. Замените <NEWS_ID_FOR_ADMIN>.
curl -X DELETE "http://127.0.0.1:8000/api/v1/news/<NEWS_ID_FOR_ADMIN>" -H "Authorization: Bearer <ADMIN_TOKEN>"
```
```bash
:: 3.8. Админ удаляет другого пользователя. Сначала найдите ID пользователя 'testuser-curl@example.com'.
curl -X GET "http://127.0.0.1:8000/api/v1/users/" -H "Authorization: Bearer <ADMIN_TOKEN>"
```
```bash
:: 3.9. Теперь удаляем пользователя, подставив его ID из списка выше.
curl -X DELETE "http://127.0.0.1:8000/api/v1/users/<USER_ID_TO_DELETE>" -H "Authorization: Bearer <ADMIN_TOKEN>"
```

---

#### 1.5. Ручная проверка кэширования

Для проверки работы кэша можно использовать встроенные утилиты командной строки для замера времени выполнения запроса.

1.  **Сначала получите токен и ID новости**, выполнив шаги `2.1` и `2.2` из сценариев `curl` выше, чтобы у вас были `<AUTHOR_TOKEN>` и `<NEWS_ID>`.

2.  **Запрос №1 (Промах кэша):** Выполните GET-запрос к новости. В логах сервера вы увидите SQL-запросы к базе данных.

    *   **В Windows (PowerShell):**
        ```powershell
        Measure-Command { curl -X GET "http://127.0.0.1:8000/api/v1/news/<NEWS_ID>" -H "Authorization: Bearer <AUTHOR_TOKEN>" }
        ```
        Обратите внимание на значение `TotalMilliseconds`. Оно будет относительно большим (например, > 50 мс).

    *   **В Linux/macOS (bash):**
        ```bash
        time curl -s -X GET "http://127.0.0.1:8000/api/v1/news/<NEWS_ID>" -H "Authorization: Bearer <AUTHOR_TOKEN>"
        ```
        Обратите внимание на значение `real` в выводе. Оно будет относительно большим (например, `0m0.085s`). Флаг `-s` убирает лишний вывод `curl`.

3.  **Запрос №2 (Попадание в кэш):** Сразу же выполните ту же команду еще раз. В логах сервера SQL-запросов на этот раз не будет.

    *   **В Windows (PowerShell):**
        ```powershell
        Measure-Command { curl -X GET "http://127.0.0.1:8000/api/v1/news/<NEWS_ID>" -H "Authorization: Bearer <AUTHOR_TOKEN>" }
        ```
        Значение `TotalMilliseconds` будет **значительно меньше** (например, < 20 мс).

    *   **В Linux/macOS (bash):**
        ```bash
        time curl -s -X GET "http://127.0.0.1:8000/api/v1/news/<NEWS_ID>" -H "Authorization: Bearer <AUTHOR_TOKEN>"
        ```
        Значение `real` будет **значительно меньше** (например, `0m0.015s`).

4.  **Инвалидация кэша:** Обновите новость, выполнив `PATCH`-запрос из шага `2.3`. В логах сервера вы увидите SQL-запрос `UPDATE`.
    ```bash
    :: Этот curl-запрос одинаков для всех систем
    curl -X PATCH "http://127.0.0.1:8000/api/v1/news/<NEWS_ID>" -H "Authorization: Bearer <AUTHOR_TOKEN>" -H "Content-Type: application/json" -d "{ \"title\": \"Updated Title to Invalidate Cache\" }"
    ```

5.  **Запрос №3 (Снова промах):** Повторите GET-запрос из пункта 2 (или 3). Время выполнения снова станет большим, а в логах сервера снова появится SQL-запрос `SELECT`, подтверждая, что кэш был сброшен и данные снова взяты из БД.
