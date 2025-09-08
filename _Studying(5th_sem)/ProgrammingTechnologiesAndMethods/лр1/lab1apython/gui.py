# gui.py
# -*- coding: utf-8 -*-
import os
import sys
import ctypes
import subprocess
import time
from threading import Thread
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox

# --- Блок 1: Определение путей и проверка прав ---
if getattr(sys, "frozen", False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(application_path)


# --- Класс приложения ---
class ProtectorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Файловый Протектор (1а)")
        self.geometry("450x200")
        self.minsize(450, 200)
        self.protector_exe = os.path.join(application_path, "Protector.exe")
        self.watch_process = None

        if not os.path.exists("template.tbl"):
            messagebox.showerror(
                "Программа не настроена",
                "Файл 'template.tbl' не найден.\nСначала запустите Protector.exe setup.",
            )
            self.destroy()
            return

        self._create_widgets()
        self.update_all_statuses()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        # ... (код виджетов без изменений)
        frame_status = tk.Frame(self)
        frame_status.pack(pady=10, padx=20, fill="x")
        tk.Label(frame_status, text="Защита файлов:", font=("Arial", 10)).pack(
            side="left"
        )
        self.status_value = tk.Label(
            frame_status, text="...", font=("Arial", 10, "bold")
        )
        self.status_value.pack(side="left", padx=5)
        tk.Label(frame_status, text="Слежение:", font=("Arial", 10)).pack(
            side="left", padx=20
        )
        self.watch_status_value = tk.Label(
            frame_status, text="...", font=("Arial", 10, "bold")
        )
        self.watch_status_value.pack(side="left", padx=5)
        frame_buttons = tk.Frame(self)
        frame_buttons.pack(pady=10, padx=20, fill="x")
        self.on_button = tk.Button(
            frame_buttons,
            text="ВКЛЮЧИТЬ ВСЕ",
            command=self.enable_all,
            bg="#D4EDDA",
            height=2,
        )
        self.on_button.pack(side="left", expand=True, fill="x", padx=5)
        self.off_button = tk.Button(
            frame_buttons,
            text="ВЫКЛЮЧИТЬ ВСЕ",
            command=self.disable_all,
            bg="#F8D7DA",
            height=2,
        )
        self.off_button.pack(side="left", expand=True, fill="x", padx=5)
        self.log_button = tk.Button(
            self, text="Показать логи ▼", command=self.toggle_logs
        )
        self.log_button.pack(pady=5, anchor="w", padx=20)
        self.log_box = scrolledtext.ScrolledText(
            self, height=10, state="disabled", font=("Consolas", 9), wrap=tk.WORD
        )

    def run_command(self, mode, args=None, log_output=True):
        if not os.path.exists(self.protector_exe):
            self._write_log(
                f"[Ошибка] Исполняемый файл '{self.protector_exe}' не найден."
            )
            return

        command = [self.protector_exe, mode]
        if args:
            command.extend(args)

        # ИСПРАВЛЕНИЕ: Добавляем creationflags, чтобы скрыть консольное окно
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        output = proc.stdout
        if log_output and output:
            self._write_log(output)
        return output

    def _read_watch_logs(self):
        for line_bytes in iter(self.watch_process.stdout.readline, b""):
            if not line_bytes:
                break
            line = line_bytes.decode("utf-8", errors="replace")
            self.after(0, self._write_log, f"Слежение: {line.strip()}")
        self.watch_process = None
        self.after(0, self.update_all_statuses)

    def _write_log(self, message):
        if self.log_box.winfo_exists():
            self.log_box.config(state="normal")
            timestamp = time.strftime("%H:%M:%S")
            clean_message = "\n".join(
                line for line in message.strip().split("\n") if line.strip()
            )
            if clean_message:
                self.log_box.insert(tk.END, f"[{timestamp}] {clean_message}\n")
            self.log_box.see(tk.END)
            self.log_box.config(state="disabled")

    def update_all_statuses(self):
        def task():
            output = self.run_command("status", log_output=False)

            def update_gui():
                status = (
                    output.strip().split(":")[-1].strip()
                    if output and ":" in output
                    else "Неизвестно"
                )
                self.status_value.config(
                    text=status, fg="red" if status == "ON" else "green"
                )
                watch_status = (
                    "ВКЛЮЧЕНО"
                    if self.watch_process and self.watch_process.poll() is None
                    else "ВЫКЛЮЧЕНО"
                )
                self.watch_status_value.config(
                    text=watch_status,
                    fg="red" if watch_status == "ВКЛЮЧЕНО" else "green",
                )
                is_active = status == "ON" or watch_status == "ВКЛЮЧЕНО"
                self.on_button.config(state="disabled" if is_active else "normal")
                self.off_button.config(state="normal" if is_active else "disabled")

            self.after(0, update_gui)

        Thread(target=task, daemon=True).start()

    def enable_all(self):
        self._write_log("Команда: ВКЛЮЧИТЬ ВСЕ")
        # ИСПРАВЛЕНИЕ: Добавляем creationflags, чтобы скрыть консольное окно
        self.watch_process = subprocess.Popen(
            [self.protector_exe, "watch"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self._write_log(f"Запуск слежения (PID: {self.watch_process.pid}).")
        Thread(target=self._read_watch_logs, daemon=True).start()
        self.after(500, lambda: self.run_command("on"))
        self.after(1000, self.update_all_statuses)

    def disable_all(self):
        self._write_log("Команда: ВЫКЛЮЧИТЬ ВСЕ")
        password = simpledialog.askstring(
            "Пароль", "Введите пароль для отключения:", show="*"
        )
        if password is not None:
            output = self.run_command("off_gui", args=[password])
            if "Пароль верный" in output:
                if self.watch_process and self.watch_process.poll() is None:
                    self._write_log("Остановка слежения...")
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(self.watch_process.pid)],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                    self._write_log("Слежение остановлено.")
        else:
            self._write_log("Отключение отменено.")
        self.after(100, self.update_all_statuses)

    def toggle_logs(self):
        if self.log_box.winfo_viewable():
            self.log_box.pack_forget()
            self.geometry("450x200")
            self.log_button.config(text="Показать логи ▼")
        else:
            self.geometry("450x430")
            self.log_box.pack(pady=5, padx=20, fill="both", expand=True)
            self.log_button.config(text="Скрыть логи ▲")

    def on_closing(self):
        if self.watch_process and self.watch_process.poll() is None:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(self.watch_process.pid)],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        self.destroy()


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
    else:
        app = ProtectorGUI()
        app.mainloop()
