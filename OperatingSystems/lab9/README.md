# 🧪 Проект: Тестирование TCP Socket Options и RPC-сервис с Аутентификацией

## 🔍 Описание

Проект включает две части:

1. **Анализ TCP сокетов с разными опциями**  
   Python-скрипты (`server.py`, `client.py`) тестируют влияние настроек `setsockopt` на производительность и поведение TCP-соединений.

2. **RPC-сервис на C с поддержкой аутентификации**  
   Программа реализует удалённые арифметические операции через RPC с использованием XDR и IDL-описания, включая базовые механизмы аутентификации.

---

## 📦 Часть 1: Тестирование опций TCP-сокетов

### 🎯 Цель

Измерить влияние сетевых опций на производительность TCP и определить оптимальные конфигурации для различных сценариев.

### 🧩 Компоненты

- `server.py` — TCP-сервер, работающий на `127.0.0.1:8080`, обрабатывает входящие соединения.
- `client.py` — TCP-клиент, отправляет данные и измеряет скорость/задержки при разных настройках сокетов.

### ⚙️ Тестируемые опции

| Опция         | Назначение                                                                 |
|---------------|----------------------------------------------------------------------------|
| `SO_REUSEADDR`| Повторное использование адреса, ускоряет повторный запуск сервера         |
| `SO_KEEPALIVE`| Отправка keep-alive пакетов для поддержания соединения                    |
| `TCP_NODELAY` | Отключение алгоритма Нейгла для минимизации задержек                      |

### 🧪 Логика работы

1. Клиент перебирает все возможные комбинации опций.
2. Выполняется серия сообщений (request-response) для каждой конфигурации.
3. Среднее время измеряется, визуализируется через `matplotlib`.

### 📊 Особенности реализации

- Измерение времени на уровне микросекунд
- Использование `socket` и `time` в Python
- Визуализация данных в графиках

---

## 🖧 Часть 2: RPC-программа с аутентификацией

### 🎯 Цель

Создать RPC-сервис, выполняющий арифметические операции (`add`, `sub`, `mul`, `div`) над числами с плавающей точкой, с поддержкой авторизации клиента.

### ⚙️ Технические детали

- Протокол: **ONC RPC**, сериализация через **XDR**
- Сервис регистрируется через `rpcbind`
- Используется `rpcgen` для генерации клиентских/серверных стабов
- Подключение библиотек: `libtirpc`, `libnsl`
- Простая аутентификация встроена в протокол обмена

### 📁 Основные файлы

| Файл              | Назначение                                   |
|-------------------|----------------------------------------------|
| `IDL.x`           | IDL-файл с описанием интерфейса и структур   |
| `IDL_server.c`    | Реализация RPC-сервера                       |
| `IDL_client.c`    | CLI-клиент для вызова RPC-функций            |
| `IDL_xdr.c`       | XDR-сериализация (автогенерация)             |
| `IDL_clnt.c`      | Клиентские RPC-стабы                         |
| `IDL_svc.c`       | Серверные RPC-стабы                          |

### 🛠️ Запуск

```bash
sudo systemctl start rpcbind
gcc IDL_server.c IDL_xdr.c IDL_svc.c -ltirpc -lnsl -o server
gcc IDL_client.c IDL_xdr.c IDL_clnt.c -ltirpc -lnsl -o client
./server &
./client
```

---

## 📌 Требования

- **Python 3.x** с установленными библиотеками:
  - `numpy`
  - `matplotlib`
- **ОС Linux** с активной службой `rpcbind`
- Установленные утилиты и библиотеки:
  - `rpcgen`
  - `libtirpc-dev`
  - `libnsl-dev`
  - `gcc`

---

## ✅ Результаты

Проект демонстрирует:

- 📶 Влияние TCP-настроек на поведение сокета и сетевую задержку  
- 🤝 Реализацию клиент-серверной архитектуры с измерением производительности  
- 🔐 Разработку RPC-сервиса с базовой аутентификацией  
- 📦 Применение XDR для сериализации данных и RPC для удалённого взаимодействия  
- 🛠️ Навыки низкоуровневой работы с системными и сетевыми компонентами

---

## 🗂️ Структура репозитория

```bash
tcp_socket_test/
├── server.py          # TCP-сервер
├── client.py          # TCP-клиент с тестами и визуализацией

rpc_compute/
├── IDL.x              # Описание интерфейса
├── IDL_server.c       # Серверная реализация
├── IDL_client.c       # Клиент RPC
├── IDL_xdr.c          # Сериализация XDR
├── IDL_svc.c          # Серверные стабы (rpcgen)
├── IDL_clnt.c         # Клиентские стабы (rpcgen)
```

*📌 Проект разработан в рамках учебной практики по системному и сетевому программированию. Предназначен для демонстрации принципов настройки сетевых соединений и реализации RPC-сервисов.*
