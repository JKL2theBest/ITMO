# Этап 1: Базовый образ
# Используем официальный slim-образ Python. Он содержит минимально необходимый набор пакетов.
FROM python:3.12.4-slim-bookworm

# Устанавливаем рабочую директорию внутри контейнера.
WORKDIR /app

# Устанавливаем переменные окружения для Python.
# PYTHONDONTWRITEBYTECODE: отключает создание .pyc файлов.
# PYTHONUNBUFFERED: обеспечивает немедленный вывод логов в stdout/stderr.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Этап 2: Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Этап 3: Установка Python-зависимостей
# Этот слой будет пересобираться только при изменении requirements.txt.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Этап 4: Копирование кода приложения
COPY . .

# Этап 5: Настройка и запуск
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]