import os
import sys
import winreg # !!! Ключевой модуль для работы с реестром Windows
from datetime import datetime, timedelta

# --- КОНСТАНТЫ И НАСТРОЙКИ ---

# Имя файла для хранения ФИО. Будет создан в папке с программой.
DATA_FILE_NAME = "users.txt"

# Лимиты для триальной версии
MAX_RUNS = 5  # Максимальное количество запусков
TRIAL_MINUTES = 3  # Максимальное время использования в минутах

# Уникальный путь в реестре для хранения данных о лицензии.
# HKEY_CURRENT_USER -> Software -> Lab2ProtectionApp_PY
# Добавим "_PY", чтобы не пересекаться с версией на C#
REG_KEY_PATH = r"Software\Lab2ProtectionApp_PY"


def check_license():
    """
    Проверяет статус лицензии (лимиты по времени и запускам), читая/записывая данные в реестр.
    Возвращает True, если лимиты не превышены, False - в противном случае.
    """
    try:
        # Открываем или создаем наш ключ в реестре
        # winreg.HKEY_CURRENT_USER - корневая ветка для текущего пользователя
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH)

        # Пытаемся прочитать текущее количество запусков и дату первого запуска
        try:
            run_count_str, _ = winreg.QueryValueEx(key, "RunCount")
            install_date_str, _ = winreg.QueryValueEx(key, "InstallDate")
            
            current_run_count = int(run_count_str)
            install_date = datetime.fromisoformat(install_date_str)

        except FileNotFoundError:
            # Если значения не найдены - это ПЕРВЫЙ ЗАПУСК!
            print("Добро пожаловать! Это первый запуск программы.")
            current_run_count = 0
            install_date = datetime.now()
            # Записываем начальные значения. Дату сохраняем в виде строки формата ISO.
            winreg.SetValueEx(key, "InstallDate", 0, winreg.REG_SZ, install_date.isoformat())
        
        # Увеличиваем счетчик запусков и сохраняем его
        current_run_count += 1
        winreg.SetValueEx(key, "RunCount", 0, winreg.REG_SZ, str(current_run_count))
        
        # Закрываем ключ реестра
        winreg.CloseKey(key)

        # --- ПРОВЕРКА ЛИМИТОВ ---
        expiry_date = install_date + timedelta(minutes=TRIAL_MINUTES)
        time_limit_exceeded = datetime.now() > expiry_date
        run_limit_exceeded = current_run_count > MAX_RUNS

        if time_limit_exceeded or run_limit_exceeded:
            print("\033[91m" + "!!! СРОК ДЕЙСТВИЯ ПРОБНОЙ ВЕРСИИ ИСТЕК !!!" + "\033[0m")
            if time_limit_exceeded:
                print(f"- Причина: Прошло более {TRIAL_MINUTES} минут с момента первого запуска.")
            if run_limit_exceeded:
                print(f"- Причина: Превышен лимит запусков (>{MAX_RUNS}).")
            
            print("\nПожалуйста, приобретите полную версию или удалите программу.")
            return False
        else:
            # Лимиты не превышены, сообщаем пользователю остаток
            time_left = expiry_date - datetime.now()
            print("\033[96m" + "--- Информация о пробной версии ---")
            print(f"Запусков использовано: {current_run_count} из {MAX_RUNS}.")
            # timedelta не всегда красиво форматируется, сделаем вручную
            minutes_left = time_left.seconds // 60
            seconds_left = time_left.seconds % 60
            print(f"Времени осталось: {minutes_left} мин {seconds_left} сек.")
            print("-------------------------------------" + "\033[0m")
            return True

    except Exception as e:
        print("\033[91m" + f"Критическая ошибка при проверке лицензии: {e}" + "\033[0m")
        print("Программа не может продолжить работу.")
        return False


def run_core_logic():
    """
    Основная логика программы: запрос ФИО и запись в файл.
    """
    try:
        print("\n--- Основная программа ---")
        full_name = input("Введите ваше ФИО: ")

        if not full_name.strip():
            print("Ошибка: ФИО не может быть пустым.")
            return

        # Проверяем, существует ли уже такое ФИО в файле
        # Используем кодировку utf-8 для корректной работы с кириллицей
        if os.path.exists(DATA_FILE_NAME):
            with open(DATA_FILE_NAME, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()]
            if full_name in lines:
                print("\033[93m" + f"Пользователь с ФИО '{full_name}' уже существует в файле." + "\033[0m")
                return

        # Дописываем новое ФИО в конец файла.
        with open(DATA_FILE_NAME, 'a', encoding='utf-8') as f:
            f.write(full_name + '\n')
        
        print("\033[92m" + f"ФИО '{full_name}' успешно добавлено в файл {DATA_FILE_NAME}." + "\033[0m")

    except Exception as e:
        print("\033[91m" + f"Произошла ошибка при работе с файлом: {e}" + "\033[0m")


def main():
    """
    Главная функция программы.
    """
    # Шаг 1: Проверка лицензии
    if not check_license():
        input("\nНажмите Enter для выхода...")
        sys.exit() # Завершаем программу

    # Шаг 2: Если лицензия в порядке, выполняем основную логику
    run_core_logic()
    
    print("\nРабота программы успешно завершена.")
    input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()