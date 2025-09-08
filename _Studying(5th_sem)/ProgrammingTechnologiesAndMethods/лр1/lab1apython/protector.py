# protector.py
# -*- coding: utf-8 -*-
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

# --- Блок 1: Настройка и проверка прав ---
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

TEMPLATE_FILE = "template.tbl"


class Protector:
    def __init__(self):
        self.template_path = os.path.abspath(TEMPLATE_FILE)
        self.everyone_sid = win32security.CreateWellKnownSid(win32security.WinWorldSid)

    def set_file_deny_full_control(self, file_path, enable):
        if not os.path.exists(file_path):
            return
        try:
            sd = win32security.GetNamedSecurityInfo(
                file_path,
                win32security.SE_FILE_OBJECT,
                win32security.DACL_SECURITY_INFORMATION,
            )
            dacl = sd.GetSecurityDescriptorDacl() or win32security.ACL()

            # ИСПРАВЛЕНИЕ: Возвращаем надежный цикл for i in range(...)
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
            print(
                f"  [Ошибка] Не удалось изменить права для {os.path.basename(file_path)}: {e}",
                flush=True,
            )

    def get_status(self):
        if not os.path.exists(self.template_path):
            return "Не настроено"
        try:
            with open(self.template_path, "r", encoding="utf-8") as f:
                f.readline()
            return "OFF"
        except IOError:
            return "ON"

    def get_target_files(self, patterns):
        target_files = set()
        for pattern in patterns:
            for f_path in glob.glob(f"**/{pattern}", recursive=True):
                if os.path.isfile(f_path):
                    target_files.add(os.path.abspath(f_path))

        target_files.add(self.template_path)
        gui_exe_path = os.path.join(
            os.path.dirname(os.path.abspath(sys.executable)), "ProtectorGUI.exe"
        )
        if os.path.exists(gui_exe_path):
            target_files.add(gui_exe_path)

        return sorted(list(target_files))

    def _command_setup(self):
        print("--- Первоначальная настройка ---", flush=True)
        if os.path.exists(self.template_path):
            confirm = input(
                f"'{self.template_path}' уже существует. Перезаписать? (y/n): "
            ).lower()
            if confirm != "y":
                print("Отмена.", flush=True)
                return
        while True:
            password = getpass.getpass("Введите новый пароль: ")
            if not password:
                print("Пароль не может быть пустым.", flush=True)
                continue
            password_confirm = getpass.getpass("Подтвердите пароль: ")
            if password == password_confirm:
                break
            print("Пароли не совпадают.", flush=True)

        salt_bytes = os.urandom(16)
        salt_b64 = base64.b64encode(salt_bytes).decode("utf-8")
        password_hash = hashlib.sha256(
            salt_b64.encode("utf-8") + password.encode("utf-8")
        ).hexdigest()

        with open(self.template_path, "w", encoding="utf-8") as f:
            f.write(f"{salt_b64}:{password_hash}\n")
            f.write("secret_document.txt\nreport_*.docx\n*.log\n")
        print(f"'{self.template_path}' успешно создан/обновлен.", flush=True)

    def _command_status(self):
        print(f"Статус защиты: {self.get_status()}", flush=True)

    def _command_on(self):
        print("Включение защиты...", flush=True)
        if self.get_status() == "ON":
            print("Защита уже включена.", flush=True)
            return
        with open(self.template_path, "r", encoding="utf-8") as f:
            patterns = [line.strip() for line in f.readlines()[1:]]
        target_files = self.get_target_files(patterns)
        print("Применяется защита к следующим файлам:", flush=True)
        for f in target_files:
            print(f" - {f}", flush=True)
            self.set_file_deny_full_control(f, enable=True)
        print("\nЗащита включена.", flush=True)

    def _command_off(self, password_from_gui=None):
        print("Отключение защиты...", flush=True)
        if self.get_status() == "OFF":
            print("Защита уже выключена.", flush=True)
            return

        self.set_file_deny_full_control(self.template_path, enable=False)
        with open(self.template_path, "r", encoding="utf-8") as f:
            salt_b64, stored_hash = f.readline().strip().split(":", 1)
            patterns = [line.strip() for line in f.readlines()]

        password = (
            password_from_gui
            if password_from_gui is not None
            else getpass.getpass("Введите пароль: ")
        )
        password_hash = hashlib.sha256(
            salt_b64.encode("utf-8") + password.encode("utf-8")
        ).hexdigest()

        if password_hash != stored_hash:
            print("Неверный пароль! Возвращаем защиту обратно.", flush=True)
            self.set_file_deny_full_control(self.template_path, enable=True)
            return

        print("Пароль верный. Отключаем защиту...", flush=True)
        target_files = self.get_target_files(patterns)
        print("Снимается защита со следующих файлов:", flush=True)
        for f in target_files:
            print(f" - {f}", flush=True)
            self.set_file_deny_full_control(f, enable=False)
        print("\nЗащита отключена.", flush=True)

    def _command_watch(self):
        print("--- РЕЖИМ СЛЕЖЕНИЯ АКТИВИРОВАН ---", flush=True)
        if not os.path.exists(self.template_path):
            print(f"Ошибка: '{TEMPLATE_FILE}' не найден.", flush=True)
            return

        with open(self.template_path, "r", encoding="utf-8") as f:
            patterns = [line.strip() for line in f.readlines()[1:]]

        class WatcherHandler(FileSystemEventHandler):
            def process(self, event):
                if event.is_directory:
                    return
                path = (
                    event.dest_path if hasattr(event, "dest_path") else event.src_path
                )
                for pattern in patterns:
                    if glob.fnmatch.fnmatch(os.path.basename(path), pattern):
                        print(
                            f"Событие '{event.event_type}': {os.path.basename(path)}",
                            flush=True,
                        )
                        time.sleep(0.5)
                        Protector().set_file_deny_full_control(path, enable=True)
                        print(f"{path} -> Файл защищен", flush=True)
                        break

            def on_created(self, event):
                self.process(event)

            def on_moved(self, event):
                self.process(event)

        observer = Observer()
        observer.schedule(WatcherHandler(), path=".", recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def run(self, mode, args=None):
        commands = {
            "setup": self._command_setup,
            "on": self._command_on,
            "off": self._command_off,
            "status": self._command_status,
            "watch": self._command_watch,
        }
        action = commands.get(mode)
        if mode == "off_gui":
            self._command_off(password_from_gui=args[0] if args else "")
        elif action:
            action()
        else:
            print(f"Ошибка: Неизвестная команда '{mode}'", flush=True)


# --- Блок 4: Точка входа ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


if __name__ == "__main__":
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
        params = " ".join(sys.argv[1:])
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, None, 1
            )
        except Exception as e:
            print(f"Ошибка при запросе прав: {e}", flush=True)
        sys.exit(0)

    mode = sys.argv[1]
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
