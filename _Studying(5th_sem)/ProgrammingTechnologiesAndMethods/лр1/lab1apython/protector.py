# file_protector.py (v6.1 - The Final UX Polish)

import os
import sys
import glob
import time
import hashlib
import ctypes
import base64
import subprocess
from threading import Thread
from ctypes import wintypes

# --- Весь код до функции main() остается БЕЗ ИЗМЕНЕНИЙ ---
# ... (Копируем все классы и функции из предыдущей версии) ...
# --- Константы ---
APP_NAME = "Файловый Протектор"
APP_VERSION = "6.1"
TEMPLATE_FILE = "template.tbl"
UAC_ERROR_CODE_CANCELLED = 1223 # Пользователь отказался от UAC

# --- Отложенные импорты (Lazy Imports) для оптимизации ---
# Эти модули будут импортированы только при необходимости.
_pywintypes = None
_win32security = None
_win32con = None
_getpass = None
_argparse = None
_Observer = None
_FileSystemEventHandler = None
_tk = None
_simpledialog = None
_scrolledtext = None
_messagebox = None

def _import_win_deps():
    global _pywintypes, _win32security, _win32con
    if _win32security is None:
        import pywintypes as _pywintypes
        import win32security as _win32security
        import win32con as _win32con

def _import_cli_deps():
    global _getpass, _argparse
    if _argparse is None:
        import getpass as _getpass
        import argparse as _argparse

def _import_watcher_deps():
    global _Observer, _FileSystemEventHandler
    if _Observer is None:
        from watchdog.observers import Observer as _Observer
        from watchdog.events import FileSystemEventHandler as _FileSystemEventHandler

def _import_gui_deps():
    global _tk, _simpledialog, _scrolledtext, _messagebox
    if _tk is None:
        import tkinter as _tk
        from tkinter import simpledialog as _simpledialog
        from tkinter import scrolledtext as _scrolledtext
        from tkinter import messagebox as _messagebox

# --- Основные функции и классы ---

def configure_utf8_stdout():
    """Настраивает stdout/stderr на использование UTF-8, если это возможно."""
    if sys.stdout and sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

class ConfigManager:
    """Управляет чтением, записью и проверкой файла конфигурации."""
    def __init__(self, file_path):
        self.path = os.path.abspath(file_path)
        self.salt, self.password_hash, self.patterns = None, None, []
    def exists(self): return os.path.exists(self.path)
    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                header = f.readline().strip()
                if ":" in header: self.salt, self.password_hash = header.split(":", 1)
                self.patterns = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
            return True
        except (IOError, ValueError): return False
    def create(self, password):
        salt_bytes = os.urandom(16)
        self.salt = base64.b64encode(salt_bytes).decode("utf-8")
        self.password_hash = self._hash_password(password, self.salt)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(f"{self.salt}:{self.password_hash}\n\n")
            f.write("# --- Шаблоны защищаемых файлов ---\n")
            f.write("# Каждая строка - это маска файла (например, *.docx, report_?.doc, secret.txt)\n")
            f.write("# Пустые строки и строки, начинающиеся с #, игнорируются.\n")
            f.write("secret_document.txt\nreport_*.docx\n*.log\n")
    def verify_password(self, password):
        if not self.salt or not self.password_hash: return False
        return self._hash_password(password, self.salt) == self.password_hash
    @staticmethod
    def _hash_password(password, salt):
        return hashlib.sha256(salt.encode("utf-8") + password.encode("utf-8")).hexdigest()

class SecurityManager:
    """Управляет правами доступа к файлам через Windows DACL."""
    def __init__(self):
        _import_win_deps()
        self.everyone_sid = _win32security.CreateWellKnownSid(_win32security.WinWorldSid)
    def set_deny_all(self, file_path, enable):
        if not os.path.exists(file_path): return False, f"Файл не найден: {file_path}"
        try:
            sd = _win32security.GetNamedSecurityInfo(file_path, _win32security.SE_FILE_OBJECT, _win32security.DACL_SECURITY_INFORMATION)
            dacl = sd.GetSecurityDescriptorDacl() or _win32security.ACL()
            aces_to_remove = [i for i in range(dacl.GetAceCount()) if dacl.GetAce(i)[2] == self.everyone_sid and dacl.GetAce(i)[0][0] == _win32security.ACCESS_DENIED_ACE_TYPE]
            for i in sorted(aces_to_remove, reverse=True): dacl.DeleteAce(i)
            if enable: dacl.AddAccessDeniedAceEx(_win32security.ACL_REVISION, 0, _win32con.GENERIC_ALL, self.everyone_sid)
            _win32security.SetNamedSecurityInfo(file_path, _win32security.SE_FILE_OBJECT, _win32security.DACL_SECURITY_INFORMATION, None, None, dacl, None)
            return True, f"Права для {os.path.basename(file_path)} успешно изменены."
        except _pywintypes.error as e: return False, f"Ошибка изменения прав для {os.path.basename(file_path)}: {e}"
    def check_protection_status(self, file_path):
        if not os.path.exists(file_path): return "Не настроено"
        try:
            with open(file_path, "r", encoding="utf-8"): pass
            return "OFF"
        except IOError: return "ON"

class FileWatcher:
    """Организует слежение за файловой системой в отдельном потоке."""
    def __init__(self, patterns, security_manager, logger_callback):
        _import_watcher_deps()
        self.patterns, self.security_manager, self.logger = patterns, security_manager, logger_callback
        self.observer, self.handler, self._is_running = _Observer(), self._create_handler(), False
    def _create_handler(self):
        class WatcherHandler(_FileSystemEventHandler):
            def __init__(self, patterns, sec_manager, logger): self.patterns, self.sec_manager, self.logger = patterns, sec_manager, logger
            def process(self, event):
                if event.is_directory: return
                path = getattr(event, "dest_path", event.src_path); filename = os.path.basename(path)
                if any(glob.fnmatch.fnmatch(filename, p) for p in self.patterns):
                    self.logger(f"Обнаружено событие '{event.event_type}' для файла: {filename}")
                    time.sleep(0.5); success, msg = self.sec_manager.set_deny_all(path, enable=True)
                    self.logger(f"-> {'Успех' if success else 'Ошибка'}: {msg}")
            def on_created(self, event): self.process(event)
            def on_moved(self, event): self.process(event)
        return WatcherHandler(self.patterns, self.security_manager, self.logger)
    def start(self):
        self._is_running = True; self.observer.schedule(self.handler, path=".", recursive=True); self.observer.start()
        self.logger("--- РЕЖИМ СЛЕЖЕНИЯ АКТИВИРОВАН ---")
    def stop(self):
        if self._is_running:
            self.observer.stop(); self.observer.join(); self._is_running = False
            self.logger("--- РЕЖИМ СЛЕЖЕНИЯ ОСТАНОВЛЕН ---")

def log_cli(message): print(message, flush=True)

def find_target_files(patterns, include_config_path):
    target_files = {os.path.abspath(f) for p in patterns for f in glob.glob(f"**/{p}", recursive=True) if os.path.isfile(f)}
    target_files.add(include_config_path)
    self_executable_path = os.path.abspath(sys.executable)
    target_files.discard(self_executable_path)
    return sorted(list(target_files))

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception: return False

class SHELLEXECUTEINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("fMask", ctypes.c_ulong), ("hwnd", wintypes.HWND), ("lpVerb", wintypes.LPCWSTR), ("lpFile", wintypes.LPCWSTR), ("lpParameters", wintypes.LPCWSTR), ("lpDirectory", wintypes.LPCWSTR), ("nShow", ctypes.c_int), ("hInstApp", wintypes.HINSTANCE), ("lpIDList", ctypes.c_void_p), ("lpClass", wintypes.LPCWSTR), ("hkeyClass", wintypes.HKEY), ("dwHotKey", wintypes.DWORD), ("hIcon", wintypes.HANDLE), ("hProcess", wintypes.HANDLE)]

def elevate_privileges_cli():
    SEE_MASK_NOCLOSEPROCESS = 0x00000040
    info = SHELLEXECUTEINFO(cbSize=ctypes.sizeof(SHELLEXECUTEINFO), fMask=SEE_MASK_NOCLOSEPROCESS, lpVerb="runas", lpFile=sys.executable, lpParameters=' '.join(f'"{arg}"' for arg in sys.argv[1:]), nShow=1)
    try:
        if not ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(info)): raise ctypes.WinError()
        hProcess = info.hProcess; ctypes.windll.kernel32.WaitForSingleObject(hProcess, -1); ctypes.windll.kernel32.CloseHandle(hProcess)
    except Exception as e:
        print(f"Ошибка при запросе прав администратора: {e}")
    sys.exit(0)

class AppController:
    """Координирует работу всех модулей. Является 'мозгом' приложения."""
    def __init__(self, logger_callback=log_cli):
        self.config, self.security, self.watcher, self.log = ConfigManager(TEMPLATE_FILE), SecurityManager(), None, logger_callback
    def setup(self):
        _import_cli_deps()
        self.log("--- Первоначальная настройка ---");
        if self.config.exists():
            if self.log == log_cli:
                confirm = input(f"'{TEMPLATE_FILE}' уже существует. Перезаписать? (y/n): ").lower()
                if confirm != "y": self.log("Отмена."); return False
        if self.log == log_cli:
            while True:
                password = _getpass.getpass("Введите новый пароль: ")
                if not password: self.log("Пароль не может быть пустым."); continue
                if password == _getpass.getpass("Подтвердите пароль: "): break
                self.log("Пароли не совпадают.")
            self.config.create(password); self.log(f"Файл '{TEMPLATE_FILE}' успешно создан с инструкциями внутри."); return True
    def get_status(self): return self.security.check_protection_status(self.config.path)
    def protect_on(self):
        if self.get_status() == "ON": self.log("Защита уже включена."); return False, []
        if not self.config.load(): self.log("Не удалось загрузить конфигурацию."); return False, []
        patterns_to_watch = self.config.patterns; target_files = find_target_files(self.config.patterns, self.config.path)
        self.log("Включение защиты для файлов:")
        for f in target_files:
            success, _ = self.security.set_deny_all(f, enable=True); self.log(f" - {f} ... {'OK' if success else 'ОШИБКА'}")
        self.log("\nЗащита включена."); return True, patterns_to_watch
    def protect_off(self, password=None):
        if self.get_status() == "OFF": self.log("Защита уже выключена."); return {"status": "no_change"}
        if password is None: _import_cli_deps(); password = _getpass.getpass("Введите пароль: ")
        self.security.set_deny_all(self.config.path, enable=False)
        if not self.config.load() or not self.config.verify_password(password):
            self.security.set_deny_all(self.config.path, enable=True)
            self.log("Неверный пароль! Защита восстановлена."); return {"status": "error", "message": "Неверный пароль"}
        target_files = find_target_files(self.config.patterns, self.config.path)
        self.log("Отключение защиты для файлов:")
        for f in target_files:
            success, _ = self.security.set_deny_all(f, enable=False); self.log(f" - {f} ... {'OK' if success else 'ОШИБКА'}")
        self.log("\nЗащита отключена."); return {"status": "success"}
    def start_watch(self, patterns):
        if self.watcher and self.watcher._is_running: self.log("Слежение уже запущено."); return
        if not patterns: self.log("Ошибка: нет шаблонов для слежения."); return
        self.watcher = FileWatcher(patterns, self.security, self.log); self.watcher.start()
    def stop_watch(self):
        if self.watcher and self.watcher._is_running: self.watcher.stop()
        else: self.log("Слежение не было запущено.")

class ProtectorGUI(Thread):
    """Главный класс GUI, работающий в отдельном потоке."""
    def __init__(self):
        _import_gui_deps(); super().__init__(); self.daemon = True
        self.root = None; self.controller = AppController(logger_callback=self.log)
    def run(self):
        self.root = _tk.Tk(); self.root.title(f"{APP_NAME} (v{APP_VERSION})"); self.root.geometry("500x250"); self.root.minsize(500, 250)
        if not self.controller.config.exists():
            _messagebox.showerror("Программа не настроена", f"Файл '{TEMPLATE_FILE}' не найден."); self.root.destroy(); return
        self._create_widgets(); self.update_all_statuses(); self.root.protocol("WM_DELETE_WINDOW", self.on_closing); self.root.mainloop()
    def _create_widgets(self):
        main_frame = _tk.Frame(self.root, padx=10, pady=10); main_frame.pack(fill="both", expand=True)
        status_frame = _tk.LabelFrame(main_frame, text="Текущее состояние", padx=10, pady=10); status_frame.pack(fill="x", expand=True)
        _tk.Label(status_frame, text="Защита файлов:", font=("Arial", 10)).grid(row=0, column=0, sticky="w")
        self.status_value = _tk.Label(status_frame, text="...", font=("Arial", 10, "bold")); self.status_value.grid(row=0, column=1, sticky="w", padx=5)
        _tk.Label(status_frame, text="Режим слежения:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=(5,0))
        self.watch_status_value = _tk.Label(status_frame, text="...", font=("Arial", 10, "bold")); self.watch_status_value.grid(row=1, column=1, sticky="w", padx=5, pady=(5,0))
        button_frame = _tk.Frame(main_frame, pady=10); button_frame.pack(fill="x", expand=True)
        self.on_button = _tk.Button(button_frame, text="ВКЛЮЧИТЬ ЗАЩИТУ И СЛЕЖЕНИЕ", command=self.enable_all, bg="#D4EDDA", height=2); self.on_button.pack(side="left", expand=True, fill="x", padx=5)
        self.off_button = _tk.Button(button_frame, text="ВЫКЛЮЧИТЬ ВСЁ", command=self.disable_all, bg="#F8D7DA", height=2); self.off_button.pack(side="left", expand=True, fill="x", padx=5)
        log_frame = _tk.Frame(main_frame); log_frame.pack(fill="both", expand=True, pady=(5,0))
        self.log_button = _tk.Button(log_frame, text="Показать лог ▼", command=self.toggle_logs); self.log_button.pack(anchor="w")
        self.log_box = _scrolledtext.ScrolledText(log_frame, height=10, state="disabled", font=("Consolas", 9), wrap=_tk.WORD)
    def log(self, message):
        def _log_thread_safe():
            if self.log_box.winfo_exists():
                self.log_box.config(state="normal"); timestamp = time.strftime("%H:%M:%S")
                self.log_box.insert(_tk.END, f"[{timestamp}] {message.strip()}\n"); self.log_box.see(_tk.END); self.log_box.config(state="disabled")
        if self.root and self.log_box.winfo_exists(): self.root.after(0, _log_thread_safe)
    def update_all_statuses(self):
        file_status = self.controller.get_status(); watch_status = "ВКЛЮЧЕНО" if self.controller.watcher and self.controller.watcher._is_running else "ВЫКЛЮЧЕНО"
        colors = {"ON": "green", "OFF": "red", "Не настроено": "orange"}; watch_colors = {"ВКЛЮЧЕНО": "green", "ВЫКЛЮЧЕНО": "red"}
        self.status_value.config(text=file_status, fg=colors.get(file_status, "black")); self.watch_status_value.config(text=watch_status, fg=watch_colors.get(watch_status, "black"))
        is_active = file_status == "ON" or watch_status == "ВКЛЮЧЕНО"
        self.on_button.config(state="disabled" if is_active else "normal"); self.off_button.config(state="normal" if is_active else "disabled")
    def enable_all(self):
        self.log("Команда: ВКЛЮЧИТЬ ВСЕ"); Thread(target=self._enable_all_task, daemon=True).start()
    def _enable_all_task(self):
        success, patterns = self.controller.protect_on()
        if success: self.controller.start_watch(patterns)
        self.root.after(100, self.update_all_statuses)
    def disable_all(self):
        self.log("Команда: ВЫКЛЮЧИТЬ ВСЕ"); password = _simpledialog.askstring("Пароль", "Введите пароль:", show="*", parent=self.root)
        if password is not None: Thread(target=self._disable_all_task, args=(password,), daemon=True).start()
        else: self.log("Отключение отменено.")
    def _disable_all_task(self, password):
        result = self.controller.protect_off(password)
        if result.get("status") == "success": self.controller.stop_watch()
        self.root.after(100, self.update_all_statuses)
    def toggle_logs(self):
        if self.log_box.winfo_viewable():
            self.log_box.pack_forget(); self.root.geometry("500x250"); self.log_button.config(text="Показать лог ▼")
        else: self.root.geometry("500x450"); self.log_box.pack(fill="both", expand=True, pady=(5,0)); self.log_button.config(text="Скрыть лог ▲")
    def on_closing(self):
        self.log("Завершение работы, остановка слежения...")
        self.root.withdraw() # Прячем окно немедленно
        self.controller.stop_watch() # Синхронно ждем завершения
        self.root.destroy()

def hide_console_window():
    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0: ctypes.windll.user32.ShowWindow(whnd, 0)

# --- ТОЧКА ВХОДА И РАЗДЕЛИТЕЛЬ ЛОГИКИ ---
def main():
    """Главная функция, определяющая режим работы приложения."""
    if getattr(sys, "frozen", False): os.chdir(os.path.dirname(sys.executable))
    
    # ИСПРАВЛЕНИЕ 1: Проверяем на --help до проверки на админа
    if '--help' in sys.argv or '-h' in sys.argv:
        _import_cli_deps(); configure_utf8_stdout()
        # Создаем парсер только для вывода справки
        parser = _argparse.ArgumentParser(prog=os.path.basename(sys.executable), description=f"{APP_NAME} (v{APP_VERSION}) - Утилита для защиты файлов.")
        subparsers = parser.add_subparsers(dest="command", required=True, title="Доступные команды")
        subparsers.add_parser("setup", help="Первоначальная настройка и создание " + TEMPLATE_FILE)
        subparsers.add_parser("status", help="Проверить текущий статус защиты.")
        subparsers.add_parser("on", help="Включить защиту для файлов из " + TEMPLATE_FILE)
        subparsers.add_parser("off", help="Отключить защиту (требуется пароль).")
        subparsers.add_parser("watch", help="Включить режим постоянного слежения и защиты.")
        parser.print_help()
        input("\nНажмите Enter для выхода...")
        return

    is_cli_mode = len(sys.argv) > 1 and '--run-gui' not in sys.argv
    if is_cli_mode:
        _import_cli_deps(); configure_utf8_stdout()
        if not is_admin(): elevate_privileges_cli()
        
        parser = _argparse.ArgumentParser(prog=os.path.basename(sys.executable))
        subparsers = parser.add_subparsers(dest="command", required=True)
        #... (остальные команды как были)
        subparsers.add_parser("setup")
        subparsers.add_parser("status")
        subparsers.add_parser("on")
        subparsers.add_parser("off")
        subparsers.add_parser("watch")
        
        # Парсим аргументы без вывода справки по-умолчанию
        try:
            args = parser.parse_args()
        except SystemExit:
            # Эта ветка больше не должна вызываться, но оставим на всякий случай
            input("\nНажмите Enter для выхода...")
            return

        controller = AppController()
        if args.command != "setup" and not controller.config.exists():
            print(f"Ошибка: Программа не настроена. Сначала выполните команду 'setup'.");
        else:
            if args.command == "setup": controller.setup()
            elif args.command == "status": print(f"Статус защиты: {controller.get_status()}")
            elif args.command == "on": controller.protect_on()
            elif args.command == "off": controller.protect_off()
            elif args.command == "watch":
                if controller.config.load():
                    controller.start_watch(controller.config.patterns)
                    try:
                        while True: time.sleep(1)
                    except KeyboardInterrupt:
                        controller.stop_watch(); print("\nРежим слежения остановлен.")
                else: print("Ошибка: Не удалось загрузить конфигурацию для слежения.")
        
        # ИСПРАВЛЕНИЕ 2: Пауза после выполнения любой CLI команды
        input("\nНажмите Enter для завершения...")

    else: # GUI Mode
        if '--run-gui' not in sys.argv:
            subprocess.Popen([sys.executable, '--run-gui'], close_fds=True, creationflags=subprocess.DETACHED_PROCESS)
            return
        if not is_admin():
            try:
                result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, "--run-gui", None, 1)
                if result <= 32:
                    _import_gui_deps(); _tk.Tk().withdraw()
                    _messagebox.showerror("Ошибка прав", "Для работы программы требуются права администратора.")
            except Exception: pass
            return
        
        hide_console_window()
        gui_app = ProtectorGUI()
        gui_app.start()
        gui_app.join()

if __name__ == "__main__":
    main()