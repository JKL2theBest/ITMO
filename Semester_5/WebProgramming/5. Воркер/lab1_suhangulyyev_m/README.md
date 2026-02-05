# **API новостного портала с фоновыми задачами и кэшированием**

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

Проект сохраняет многослойную архитектуру, которая была расширена для поддержки аутентификации, кэширования и фоновых задач:

*   **API / Controllers (`app/api/`)**: Добавлен роутер `auth.py` для аутентификации. В остальные роутеры встроена проверка токенов и прав доступа через систему зависимостей FastAPI.
*   **Services (`app/services/`)**: Реализован `AuthService` для управления сессиями в Redis. Бизнес-логика в `NewsService` и `UserService` дополнена механизмами кэширования. При создании новости сервис теперь ставит в очередь фоновую задачу для рассылки уведомлений.
*   **Core (`app/core/`)**: Модуль `security.py` инкапсулирует логику работы с JWT и хешированием паролей.
*   **Worker (`app/worker/`)**: Новый компонент, отвечающий за фоновые задачи. Использует **Celery** и **Redis** в качестве брокера сообщений. Реализованы задачи для:
    *   Мгновенной рассылки уведомлений о новой статье.
    *   Еженедельной рассылки дайджеста новостей (по расписанию).
    Задачи спроектированы с учетом отказоустойчивости и идемпотентности.

**Подробное описание ролей и прав доступа находится в файле [docs/auth.md](./docs/auth.md).**

#### 1.2.1. Взаимодействие с БД, кэшем и брокером

*   **Сессии пользователей (Redis DB 0)**: Вся информация о сессиях (refresh-токены, user-agent) хранится в Redis, обеспечивая быстрый доступ.
*   **Кэширование данных (Redis DB 0)**: Применяется паттерн *Cache-aside* для новостей и пользователей. При запросе данные сначала ищутся в кэше. При отсутствии — извлекаются из PostgreSQL и кэшируются с TTL (5 минут). Кэш инвалидируется при операциях `PATCH` или `DELETE`.
*   **Очередь задач (Redis DB 1)**: Celery использует Redis как брокер для постановки и получения фоновых задач (например, "отправить email-уведомления").
*   **Результаты задач (Redis DB 2)**: Celery хранит результаты выполнения задач в отдельной базе Redis.

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

    # Celery
    CELERY_BROKER_URL="redis://localhost:6379/1"
    CELERY_RESULT_BACKEND="redis://localhost:6379/2"

    # SQLAlchemy logging (True for dev, False for prod)
    DB_ECHO_LOG=True
    ```

#### (Опционально) Полный сброс окружения для разработки

Если вам нужно полностью очистить и пересоздать окружение с нуля (удалить все данные из PostgreSQL и Redis), используйте следующую команду:

```bash
docker-compose down -v
```
> **Внимание!** Эта команда безвозвратно удалит все данные из вашей локальной базы данных и Redis.

3.  Запустить всю инфраструктуру (PostgreSQL, Redis, Celery worker и beat):
    ```bash
    docker-compose up -d --build
    ```

4.  Установить/обновить локальные зависимости:
    ```bash
    poetry install --with dev
    ```

5.  Применить миграции Alembic для создания схемы БД:
    ```bash
    poetry run alembic upgrade head
    ```

6.  Запустить FastAPI приложение локально:
    ```bash
    poetry run uvicorn app.main:app --reload
    ```
    Приложение будет доступно по `http://127.0.0.1:8000`, документация — по `http://127.0.0.1:8000/docs`.

---

#### 1.4. Тестирование и проверка результата

**Автоматизированное тестирование:**

Проект покрыт набором из **40 интеграционных и юнит-тестов**. Тесты проверяют основной функционал, права доступа, кэширование и постановку задач в очередь.

Для запуска тестов используется команда:
```bash
poetry run pytest
```

**Ручная проверка фоновых задач:**

1.  Откройте терминал и начните отслеживать логи воркера:
    ```bash
    docker-compose logs -f worker
    ```

2.  С помощью `curl` или Postman создайте новую новость (см. Сценарий 2, шаг 2.2).

3.  Сразу после успешного создания новости, в терминале с логами воркера вы увидите, что задача была получена (`Task ... received`), а затем выполнены мок-отправки (`SEND_EMAIL: To: ...`). Логи также дублируются в файл `celery_worker.log` в корне проекта.

**Ручная проверка кэширования:**

Процедура описана в секции `curl`-сценариев ниже. Используйте `Measure-Command` (PowerShell) или `time` (bash) для замера времени ответа до и после первого запроса, а также после инвалидации кэша.

---

**Ручная проверка GitHub OAuth**

Этот процесс требует использования браузера.

1.  **Настройка:** Убедитесь, что в файле `.env` указаны ваши реальные `GITHUB_CLIENT_ID` и `GITHUB_CLIENT_SECRET`. В настройках вашего GitHub OAuth App поле "Authorization callback URL" должно быть `http://127.0.0.1:8000/api/v1/auth/github/callback`.

2.  **Запуск:** Откройте в браузере следующую ссылку:
    ```
    http://127.0.0.1:8000/api/v1/auth/github/login
    ```

3.  **Авторизация:** Вас перенаправит на сайт GitHub. Войдите в свой аккаунт и авторизуйте приложение.

4.  **Результат:** После успешной авторизации GitHub вернет вас обратно на ваше приложение, и **в окне браузера отобразится JSON-ответ** с вашими `access_token` и `refresh_token`.

    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "a1b2c3d4e5f6...",
      "token_type": "bearer"
    }
    ```
    Получение этого ответа означает, что аутентификация через GitHub работает корректно.

---

### Сценарии взаимодействия с API через `curl`

Ниже приведен полный сценарий взаимодействия с API через `curl` в командной строке Windows. Сценарии самодостаточны и не зависят друг от друга.

**ВАЖНОЕ ПРАВИЛО:** После выполнения команды, которая возвращает `access_token` или `id`, вам нужно будет **вручную скопировать** это значение (без кавычек) и **вставить** его в следующую команду, где есть соответствующий placeholder.

---

#### Сценарий 1: Обычный Пользователь (`USER`)

```bash
:: 1.1. Регистрация нового пользователя 'testuser-curl@example.com'
curl -X POST "http://127.0.0.1:8000/api/v1/auth/register" -H "Content-Type: application/json" -d "{ \"name\": \"CURL Test User\", \"email\": \"testuser-curl@example.com\", \"password\": \"strongpassword123\" }"
```

```bash
:: 1.2. Вход в систему. ВАЖНО: Скопируйте "access_token" и "refresh_token" из ответа для следующих шагов.
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=testuser-curl@example.com&password=strongpassword123"``````bash
:: 1.3. Попытка создать новость (ожидается ошибка 403 Forbidden). Замените <USER_TOKEN> на скопированный 'access_token'.
curl -X POST "http://127.0.0.1:8000/api/v1/news/" -H "Authorization: Bearer <USER_TOKEN>" -H "Content-Type: application/json" -d "{ \"title\": \"My First News\", \"content\": {\"text\": \"some text\"} }"
```

```bash
:: 1.4. Получение списка новостей. ВАЖНО: Скопируйте 'id' первой новости из списка (например, "409a1ca6-e94a-4605-9fe9-20937bb68b62").
curl -X GET "http://127.0.0.1:8000/api/v1/news/" -H "Authorization: Bearer <USER_TOKEN>"``````bash
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

#### Сценарий 2: Верифицированный Автор (`VERIFIED_AUTHOR`)

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
curl -X DELETE "http://127.0.0.1:8000/api/v1/news/<NEWS_ID_FROM_2.2>" -H "Authorization: Bearer <AUTHOR_TOKEN>"
```

---


#### Сценарий 3: Администратор (`ADMIN`)

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

#### Ручная проверка кэширования

Для проверки работы кэша можно использовать встроенные утилиты командной строки для замера времени выполнения запроса.

1.  **Сначала получите токен и ID новости**, выполнив шаги `2.1` и `2.2` из сценариев `curl` выше, чтобы у вас были `<AUTHOR_TOKEN>` и `<NEWS_ID>`.

2.  **Запрос №1 (Промах кэша):** Выполните GET-запрос к новости. В логах сервера (`poetry run uvicorn...`) вы увидите SQL-запросы к базе данных.

    *   **В Windows (PowerShell):**
        ```powershell
        Measure-Command { curl -X GET "http://127.0.0.1:8000/api/v1/news/<NEWS_ID>" -H "Authorization: Bearer <AUTHOR_TOKEN>" }
        ```
        Обратите внимание на значение `TotalMilliseconds`. Оно будет относительно большим (например, > 50 мс).

3.  **Запрос №2 (Попадание в кэш):** Сразу же выполните ту же команду еще раз. В логах сервера SQL-запросов на этот раз не будет.

    *   **В Windows (PowerShell):**
        ```powershell
        Measure-Command { curl -X GET "http://127.0.0.1:8000/api/v1/news/<NEWS_ID>" -H "Authorization: Bearer <AUTHOR_TOKEN>" }
        ```
        Значение `TotalMilliseconds` будет **значительно меньше** (например, < 20 мс).

4.  **Инвалидация кэша:** Обновите новость, выполнив `PATCH`-запрос.
    ```bash
    curl -X PATCH "http://127.0.0.1:8000/api/v1/news/<NEWS_ID>" -H "Authorization: Bearer <AUTHOR_TOKEN>" -H "Content-Type: application/json" -d "{ \"title\": \"Updated Title to Invalidate Cache\" }"
    ```

5.  **Запрос №3 (Снова промах):** Повторите GET-запрос. Время выполнения снова станет большим, а в логах сервера снова появится SQL-запрос `SELECT`, подтверждая, что кэш был сброшен и данные снова взяты из БД.
