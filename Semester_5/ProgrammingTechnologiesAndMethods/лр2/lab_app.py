import os
import sys
import winreg
from datetime import datetime, timedelta

# --- КОНСТАНТЫ И НАСТРОЙКИ ---

# Храним данные в общей папке ProgramData, чтобы они были доступны всем
# пользователям и не удалялись при деинсталляции программы.
APP_DATA_DIR = os.path.join(
    os.environ.get("ALLUSERSPROFILE", "C:\\ProgramData"), "Lab2App"
)
DATA_FILE_NAME = os.path.join(APP_DATA_DIR, "users.txt")

# Параметры пробной версии
MAX_RUNS = 5
TRIAL_MINUTES = 3

# Уникальный путь в реестре для хранения данных о запусках и дате установки.
REG_KEY_PATH = r"Software\Lab2App"


def get_license_data():
    """Читает данные о лицензии (счетчик запусков, дата установки) из реестра."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ)
        run_count, _ = winreg.QueryValueEx(key, "RunCount")
        install_date_str, _ = winreg.QueryValueEx(key, "InstallDate")
        winreg.CloseKey(key)
        return int(run_count), datetime.fromisoformat(install_date_str)
    except FileNotFoundError:
        # Если ключ не найден, значит это первый запуск.
        return 0, None
    except Exception as e:
        # При любой другой ошибке чтения блокируем программу для безопасности.
        print(f"Ошибка чтения данных лицензии: {e}")
        return MAX_RUNS + 1, datetime.now() - timedelta(days=1)


def check_license(run_count, install_date):
    """Проверяет, не истекли ли лимиты по времени или по количеству запусков."""
    if install_date is None:
        print("Это первый запуск программы.")
        return True

    expiry_date = install_date + timedelta(minutes=TRIAL_MINUTES)
    time_limit_exceeded = datetime.now() > expiry_date
    run_limit_exceeded = (run_count + 1) > MAX_RUNS

    if time_limit_exceeded or run_limit_exceeded:
        print("\033[91m" + "!!! СРОК ДЕЙСТВИЯ ПРОБНОЙ ВЕРСИИ ИСТЕК !!!" + "\033[0m")
        if time_limit_exceeded:
            print(
                f"- Причина: Превышен лимит времени использования ({TRIAL_MINUTES} min)."
            )
        if run_limit_exceeded:
            print(f"- Причина: Превышен лимит запусков (>{MAX_RUNS}).")

        print("\nПриобретите полную версию или удалите программу.")
        return False
    else:
        time_left = expiry_date - datetime.now()
        print("\033[96m" + "--- Информация о пробной версии ---")
        print(
            f"Запусков использовано: {run_count} из {MAX_RUNS}. Этот запуск №{run_count + 1}."
        )
        minutes_left = time_left.seconds // 60
        seconds_left = time_left.seconds % 60
        print(f"Времени осталось: {minutes_left} мин {seconds_left} сек.")
        print("-------------------------------------" + "\033[0m")
        return True


def commit_license_use(run_count, install_date):
    """Записывает в реестр обновленный счетчик запусков."""
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH)
        if install_date is None:
            # При первом успешном запуске фиксируем дату установки.
            install_date = datetime.now()
            winreg.SetValueEx(
                key, "InstallDate", 0, winreg.REG_SZ, install_date.isoformat()
            )
        winreg.SetValueEx(key, "RunCount", 0, winreg.REG_DWORD, run_count + 1)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"\033[91mОшибка при обновлении данных лицензии: {e}\033[0m")


def run_core_logic():
    """Основная логика: пошаговый ввод ФИО и запись в общий файл."""
    try:
        print("\n--- Добавление нового пользователя ---")

        # --- Пошаговый ввод и валидация ---
        while True:
            last_name = input("Введите Фамилию: ").strip()
            if last_name and all(part.isalpha() for part in last_name.split("-")):
                break
            print(
                "\033[93mОшибка: Фамилия не может быть пустой и должна содержать только буквы/дефисы.\033[0m"
            )

        while True:
            first_name = input(
                "Введите Имя (можно из нескольких частей, например, Майкл Джордан): "
            ).strip()
            if first_name and all(
                part.isalpha() for part in first_name.replace("-", " ").split()
            ):
                break
            print(
                "\033[93mОшибка: Имя не может быть пустым и должно содержать только буквы/дефисы.\033[0m"
            )

        middle_name = input("Введите Отчество (можно оставить пустым): ").strip()
        if middle_name and not all(part.isalpha() for part in middle_name.split("-")):
            print(
                "\033[93mПредупреждение: Отчество содержит недопустимые символы. Оно будет проигнорировано.\033[0m"
            )
            middle_name = ""

        # Корректная обработка заглавных букв в составных именах ("анна-мария" -> "Анна-Мария").
        last_name_capitalized = "-".join(
            [part.capitalize() for part in last_name.split("-")]
        )
        first_name_capitalized = " ".join(
            [
                "-".join([p.capitalize() for p in part.split("-")])
                for part in first_name.split()
            ]
        )
        middle_name_capitalized = "-".join(
            [part.capitalize() for part in middle_name.split("-")]
        )

        full_name_parts = [last_name_capitalized, first_name_capitalized]
        if middle_name_capitalized:
            full_name_parts.append(middle_name_capitalized)

        full_name = " ".join(full_name_parts)
        print(f"Новое ФИО: {full_name}")

        # --- Работа с файлом данных ---

        # ВАЖНО: Запись в C:\ProgramData требует запуска программы от имени администратора.
        try:
            os.makedirs(APP_DATA_DIR, exist_ok=True)
        except PermissionError:
            print(
                "\033[91mКритическая ошибка: Недостаточно прав для создания директории в C:\\ProgramData."
            )
            print("Запустите программу от имени администратора.\033[0m")
            return False

        if os.path.exists(DATA_FILE_NAME):
            with open(DATA_FILE_NAME, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines()]
            if full_name in lines:
                print(
                    "\033[93m"
                    + f"Пользователь '{full_name}' уже существует в файле."
                    + "\033[0m"
                )
                return True

        with open(DATA_FILE_NAME, "a", encoding="utf-8") as f:
            f.write(full_name + "\n")

        print(
            "\033[92m"
            + f"ФИО '{full_name}' успешно добавлено в файл {DATA_FILE_NAME}."
            + "\033[0m"
        )
        return True

    except Exception as e:
        print("\033[91m" + f"Ошибка при работе с файлом: {e}" + "\033[0m")
        return False


def main():
    """Главная функция, управляющая логикой приложения."""
    run_count, install_date = get_license_data()

    if not check_license(run_count, install_date):
        input("\nНажмите Enter для выхода...")
        sys.exit()

    success = run_core_logic()

    if success:
        # Засчитываем запуск только если основная логика выполнилась успешно.
        commit_license_use(run_count, install_date)
        print("\nРабота программы успешно завершена.")
    else:
        print("\nРабота программы завершилась с ошибкой. Запуск не будет засчитан.")

    input("Нажмите Enter для выхода...")


if __name__ == "__main__":  # pragma: no cover
    main()
