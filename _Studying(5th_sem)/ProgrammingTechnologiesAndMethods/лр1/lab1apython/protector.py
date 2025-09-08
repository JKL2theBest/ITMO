import os
import sys
import glob
import time
import hashlib
import ctypes
import getpass
import win32security
import win32con
import pywintypes
import base64
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Проблемы с кириллицей
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

TEMPLATE_FILE = "template.tbl"


class Protector:
    def __init__(self):
        self.template_path = os.path.abspath(TEMPLATE_FILE)
        # SID для группы "Все"
        self.everyone_sid = win32security.CreateWellKnownSid(win32security.WinWorldSid)
        self._is_frozen = getattr(sys, "frozen", False)
        self._executable_path = sys.executable if self._is_frozen else __file__

    def _log(self, message: str):
        """Метод для вывода с принудительной очисткой буфера."""
        print(message, flush=True)

    def set_file_deny_full_control(self, file_path, enable):
        """
        FullControl через Discretionary Access Control List (DACL).
        """
        if not os.path.exists(file_path):
            return
        try:
            sd = win32security.GetNamedSecurityInfo(
                file_path,
                win32security.SE_FILE_OBJECT,
                win32security.DACL_SECURITY_INFORMATION,
            )
            dacl = sd.GetSecurityDescriptorDacl() or win32security.ACL()

            # Очистка старых правил
            aces_to_remove = []
            for i in range(dacl.GetAceCount()):
                ace = dacl.GetAce(i)
                if (
                    ace[2] == self.everyone_sid
                    and ace[0][0] == win32security.ACCESS_DENIED_ACE_TYPE
                ):
                    aces_to_remove.append(i)
            for i in sorted(aces_to_remove, reverse=True):
                dacl.DeleteAce(i)

            if enable:
                dacl.AddAccessDeniedAceEx(
                    win32security.ACL_REVISION,
                    0,
                    win32con.GENERIC_ALL,
                    self.everyone_sid,
                )

            win32security.SetNamedSecurityInfo(
                file_path,
                win32security.SE_FILE_OBJECT,
                win32security.DACL_SECURITY_INFORMATION,
                None,
                None,
                dacl,
                None,
            )
        except pywintypes.error as e:
            self._log(
                f"  [Ошибка] Не удалось изменить права для {os.path.basename(file_path)}: {e}"
            )

    def get_status(self):
        """
        Попытка прочитать конфигурационный файл
        """
        if not os.path.exists(self.template_path):
            return "Не настроено"
        try:
            with open(self.template_path, "r", encoding="utf-8") as f:
                f.readline()
            return "OFF"
        except IOError:  # Deny Read.
            return "ON"

    def _get_gui_path(self):
        """Путь к GUI-файлу."""
        exe_name = "GUI.exe" if self._is_frozen else "gui.py"
        base_path = (
            os.path.dirname(sys.executable)
            if self._is_frozen
            else os.path.dirname(__file__)
        )
        return os.path.join(base_path, exe_name)

    def get_target_files(self, patterns):
        """Поиск файлов, соответствующих шаблонам (list comprehension)."""
        target_files = {
            os.path.abspath(f)
            for p in patterns
            for f in glob.glob(f"**/{p}", recursive=True)
            if os.path.isfile(f)
        }
        target_files.add(self.template_path)
        gui_path = self._get_gui_path()
        if os.path.exists(gui_path):
            target_files.add(gui_path)
        return sorted(target_files)

    def _verify_password(self, password: str) -> bool:
        """Проверка пароля с солью из файла."""
        try:
            with open(self.template_path, "r", encoding="utf-8") as f:
                salt_b64, stored_hash = f.readline().strip().split(":", 1)
            # Хэшируем введенный пароль с той же солью, что и при создании.
            password_hash = hashlib.sha256(
                salt_b64.encode("utf-8") + password.encode("utf-8")
            ).hexdigest()
            return password_hash == stored_hash
        except (IOError, ValueError):
            return False

    # --- Методы для каждой команды ---

    def _command_setup(self):
        self._log("--- Первоначальная настройка ---")
        if os.path.exists(self.template_path):
            confirm = input(
                f"'{self.template_path}' уже существует. Перезаписать? (y/n): "
            ).lower()
            if confirm != "y":
                self._log("Отмена.")
                return
        while True:
            password = getpass.getpass("Введите новый пароль: ")
            if not password:
                self._log("Пароль не может быть пустым.")
                continue
            password_confirm = getpass.getpass("Подтвердите пароль: ")
            if password == password_confirm:
                break
            self._log("Пароли не совпадают.")

        # Генерация соли
        salt_bytes = os.urandom(16)
        salt_b64 = base64.b64encode(salt_bytes).decode("utf-8")
        password_hash = hashlib.sha256(
            salt_b64.encode("utf-8") + password.encode("utf-8")
        ).hexdigest()
        with open(self.template_path, "w", encoding="utf-8") as f:
            f.write(f"{salt_b64}:{password_hash}\n")
            f.write("secret_document.txt\nreport_*.docx\n*.log\n")
        self._log(f"'{self.template_path}' успешно создан/обновлен.")

    def _command_status(self):
        self._log(f"Статус защиты: {self.get_status()}")

    def _command_on(self):
        self._log("Включение защиты...")
        if self.get_status() == "ON":
            self._log("Защита уже включена.")
            return
        with open(self.template_path, "r", encoding="utf-8") as f:
            patterns = [line.strip() for line in f.readlines()[1:]]
        target_files = self.get_target_files(patterns)
        self._log("Применяется защита к следующим файлам:")
        for f in target_files:
            self._log(f" - {f}")
            self.set_file_deny_full_control(f, enable=True)
        self._log("\nЗащита включена.")

    def _command_off(self, password_from_gui=None):
        self._log("Отключение защиты...")
        if self.get_status() == "OFF":
            self._log("Защита уже выключена.")
            return

        # Сначала снимаем защиту, чтобы можно было прочитать.
        self.set_file_deny_full_control(self.template_path, enable=False)
        password = (
            password_from_gui
            if password_from_gui is not None
            else getpass.getpass("Введите пароль: ")
        )

        if not self._verify_password(password):
            self._log("Неверный пароль! Возвращаем защиту обратно.")
            self.set_file_deny_full_control(self.template_path, enable=True)
            return

        self._log("Пароль верный. Отключаем защиту...")
        with open(self.template_path, "r", encoding="utf-8") as f:
            patterns = [line.strip() for line in f.readlines()[1:]]
        target_files = self.get_target_files(patterns)
        self._log("Снимается защита со следующих файлов:")
        for f in target_files:
            self._log(f" - {f}")
            self.set_file_deny_full_control(f, enable=False)
        self._log("\nЗащита отключена.")

    def _command_watch(self):
        self._log("--- РЕЖИМ СЛЕЖЕНИЯ АКТИВИРОВАН ---")
        if not os.path.exists(self.template_path):
            self._log(f"Ошибка: '{TEMPLATE_FILE}' не найден.")
            return

        with open(self.template_path, "r", encoding="utf-8") as f:
            patterns = [line.strip() for line in f.readlines()[1:]]

        # Внутренний класс-обработчик для watchdog.
        class WatcherHandler(FileSystemEventHandler):
            def __init__(self, protector, patterns):
                self.protector = protector
                self.patterns = patterns

            def process(self, event):
                if event.is_directory:
                    return
                path = getattr(event, "dest_path", event.src_path)
                for pattern in self.patterns:
                    if glob.fnmatch.fnmatch(os.path.basename(path), pattern):
                        self.protector._log(
                            f"Событие '{event.event_type}': {os.path.basename(path)}"
                        )
                        # Задержка, чтобы ОС успела завершить операцию с файлом.
                        time.sleep(0.5)
                        self.protector.set_file_deny_full_control(path, enable=True)
                        self.protector._log(f"{path} -> Файл защищен")
                        break

            def on_created(self, event):
                self.process(event)

            def on_moved(self, event):
                self.process(event)

        observer = Observer()
        observer.schedule(WatcherHandler(self, patterns), path=".", recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(5)  # "Вечный" цикл, чтобы скрипт не завершался
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def run(self, mode, args=None):
        """Словарь для вызова нужного метода."""
        commands = {
            "setup": self._command_setup,
            "on": self._command_on,
            "off": self._command_off,
            "status": self._command_status,
            "watch": self._command_watch,
        }
        if mode == "off_gui":
            self._command_off(password_from_gui=args[0] if args else "")
        elif action := commands.get(mode):  # Моржовый оператор для краткости
            action()
        else:
            self._log(f"Ошибка: Неизвестная команда '{mode}'")


# --- Точка входа ---
def is_admin():
    """Админ или нет."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


if __name__ == "__main__":
    # Определяем рабочий каталог (для PyInstaller).
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(application_path)

    valid_modes = ["setup", "on", "off", "status", "watch", "off_gui"]
    if len(sys.argv) < 2 or sys.argv[1] not in valid_modes:
        message = "Неверная или отсутствующая команда.\nИспользуйте: setup, on, off, status, watch"
        if getattr(sys, "frozen", False):
            ctypes.windll.user32.MessageBoxW(0, message, "Ошибка", 0x10)
        else:
            print(f"Ошибка: {message}", flush=True)
        sys.exit(1)

    if not is_admin():
        # Перезапускаем себя с правами администратора и немедленно выходим.
        params = " ".join(sys.argv[1:])
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, None, 1
            )
        except Exception as e:
            print(f"Ошибка при запросе прав: {e}", flush=True)
        sys.exit(0)

    mode = sys.argv[1]
    # Настроена ли программа.
    if mode != "setup" and not os.path.exists(TEMPLATE_FILE):
        message = "Программа не настроена. Сначала запустите команду 'setup'."
        if getattr(sys, "frozen", False) and "gui" not in sys.executable.lower():
            ctypes.windll.user32.MessageBoxW(0, message, "Ошибка", 0x10)
        else:
            print(f"Ошибка: {message}", flush=True)
        sys.exit(1)

    protector = Protector()
    main_args = sys.argv[2:]
    protector.run(mode, args=main_args)