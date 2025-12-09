# **API новостного портала с фоновыми задачами и мониторингом**

Выполнил:

Суханкулиев Мухаммет,
студент группы N3346

---

### 1. АРХИТЕКТУРА И РЕАЛИЗАЦИЯ

#### 1.1. Проектирование моделей данных

Проект реализует новостной портал с ролевой моделью (`USER`, `VERIFIED_AUTHOR`, `ADMIN`).
Данные хранятся в **PostgreSQL**.
Для управления сессиями (refresh-токены) и кэширования используется **Redis**, что позволило полностью убрать таблицу токенов из основной БД.

![Обновленная схема базы данных](./db_schema.png)

#### 1.2. Основные компоненты системы

*   **API (FastAPI)**: Реализует REST API, аутентификацию (JWT + GitHub OAuth) и бизнес-логику.
*   **Worker (Celery + Redis)**: Обрабатывает фоновые задачи:
    *   Мгновенная рассылка уведомлений о новых статьях.
    *   Еженедельный дайджест новостей (по расписанию).
*   **Cache (Redis)**: Используется паттерн *Cache-aside* для новостей и пользователей (TTL 5 минут).

#### 1.3. Мониторинг и Логирование

В последнем обновлении внедрен полный стек Observability для отслеживания состояния системы:

1.  **Метрики (Prometheus + Grafana)**:
    *   `Prometheus` собирает метрики с FastAPI (статус `UP` подтверждает доступность сервиса).
    *   `Grafana` визуализирует технические метрики (RPS, latency) и бизнес-метрики (регистрации, новости).
2.  **Логирование (ELK Stack)**:
    *   Структурированные JSON-логи пишутся приложением (`structlog`), собираются `Logstash` и хранятся в `Elasticsearch`.
    *   `Kibana` предоставляет интерфейс для поиска и фильтрации логов.
3.  **Трекинг ошибок (Hawk)**:
    *   Критические ошибки перехватываются middleware и отправляются в облачный сервис Hawk.

**Примеры работы мониторинга:**

| Grafana (Дашборды) | Kibana (Логи) |
| :---: | :---: |
| ![Grafana Dashboard](.//screenshots/2_Grafana.png) | ![Kibana Logs](./screenshots/3_elastic.png) |

| Hawk (Ошибки) | Prometheus (Targets UP) |
| :---: | :---: |
| ![Hawk Error](./screenshots/4_Hawk.png) | ![Prometheus Targets](./screenshots/1_Prometheus.png) |

---

### 2. ЗАПУСК ПРОЕКТА

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

2.  Создать и заполнить файл `.env` в корне проекта по шаблону ниже. **Обязательно замените `GITHUB_CLIENT_ID` и `GITHUB_CLIENT_SECRET` на свои ключи и `HAWK_TOKEN` на ваш токен Hawk.**

    > **Примечание по конфигурации:**
    > В файле `.env` указаны адреса `localhost`, чтобы вы могли запускать приложение и тесты локально (вне Docker).
    > В файле `docker-compose.yml` эти настройки **переопределяются** (раздел `environment`), чтобы внутри контейнеров приложение обращалось к сервисам по их сетевым именам (`db`, `redis`), а не по `localhost`. Это позволяет использовать один конфиг и для локальной разработки, и для Docker без ручных правок.

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

    # HAWK
    HAWK_TOKEN="eyJpbnRlZ3JhdGlvblV1..."
    ```

3.  **Запуск:**
    ```bash
    # Очистка (если нужно сбросить базы)
    docker-compose down -v 
    
    # Запуск
    docker-compose up -d --build
    ```

    *Миграции будут применены автоматически при старте контейнера `app`.*

---

### 3. ПРОВЕРКА И ТЕСТИРОВАНИЕ

#### 3.1. Доступ к интерфейсам

*   **API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
*   **Grafana**: [http://127.0.0.1:3000](http://127.0.0.1:3000) (Логин: `admin`, Пароль: `admin`)
*   **Kibana**: [http://127.0.0.1:5601](http://127.0.0.1:5601) (Index pattern: `fastapi-logs-*`)
*   **Prometheus**: [http://127.0.0.1:9090](http://127.0.0.1:9090)

#### 3.2. Сценарии проверки (cURL)

**A. Жизненный цикл пользователя (Регистрация -> Вход -> Комментарий)**

1.  Регистрация:
    ```bash
    curl -X POST "http://127.0.0.1:8000/api/v1/auth/register" -H "Content-Type: application/json" -d "{ \"name\": \"Tester\", \"email\": \"test@example.com\", \"password\": \"pass123\" }"
    ```
2.  Вход (Копируем `access_token` из ответа!):
    ```bash
    curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=test@example.com&password=pass123"
    ```
3.  Просмотр списка новостей (Проверка логирования запроса в Kibana):
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/v1/news/" -H "Authorization: Bearer <YOUR_TOKEN>"
    ```

**B. Проверка Hawk (Генерация ошибки)**

Вызовите специальный эндпоинт, который выбрасывает исключение. После этого зайдите в панель Hawk — там должна появиться новая ошибка.
```bash
curl -X GET "http://127.0.0.1:8000/error_test"
```

**C. Проверка Кэширования (Redis)**

Для верификации кэша выполните один и тот же запрос дважды.
*   Первый запрос: долгий (запрос в БД).
*   Второй запрос: быстрый (ответ из Redis, в логах нет SQL запросов).

Замените `<NEWS_ID>` на ID любой существующей новости.
```powershell
# Windows PowerShell
Measure-Command { curl -X GET "http://127.0.0.1:8000/api/v1/news/<NEWS_ID>" -H "Authorization: Bearer <YOUR_TOKEN>" }
```

#### 3.3. Автоматические тесты

Проект покрыт тестами (pytest). Для запуска локально:
```bash
poetry install
poetry run pytest
```
