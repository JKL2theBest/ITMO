# installer.py
import os
import sys
import platform
import socket
import base64
import time
import shutil
import winreg
import ctypes
import datetime  # <--- Новый импорт
import subprocess  # <--- Новый импорт
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import psutil
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

# --- Константы (ОБЯЗАТЕЛЬНО ВВЕДИТЕ СВОЮ ФАМИЛИЮ) ---
STUDENT_LASTNAME = "Ischenko"
# --------------------------------------------------

TARGET_DATA_FILENAME = "sys.tat"
PROTECTOR_EXE_NAME = "secur.exe"
PUBLIC_KEY_FILENAME = "public_key.pem"
REGISTRY_SUBKEY_PREFIX = "Software"

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Установка обновления для {STUDENT_LASTNAME}")
        self.root.geometry("550x250")

        local_appdata = os.environ.get('LOCALAPPDATA', os.path.join(os.environ.get('USERPROFILE', 'C:\\'), 'AppData', 'Local'))
        default_path = os.path.join(local_appdata, STUDENT_LASTNAME + "_SecInfo")

        self.main_frame = tk.Frame(root, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(self.main_frame, text="Выберите папку для установки «Системной информации»:").pack(anchor=tk.W)
        self.path_frame = tk.Frame(self.main_frame)
        self.path_frame.pack(fill=tk.X, expand=True, pady=5)
        self.path_entry = tk.Entry(self.path_frame)
        self.path_entry.insert(0, default_path)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.browse_button = tk.Button(self.path_frame, text="Обзор...", command=self.browse_folder)
        self.browse_button.pack(side=tk.RIGHT, padx=(5, 0))
        self.progress = ttk.Progressbar(self.main_frame, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill=tk.X, pady=15)
        self.status_label = tk.Label(self.main_frame, text="Готов к установке.", wraplength=500)
        self.status_label.pack(anchor=tk.W)
        self.install_button = tk.Button(self.main_frame, text="Установить", command=self.start_installation, bg='#e6ffe6')
        self.install_button.pack(pady=10, fill=tk.X)

    def browse_folder(self):
        folder_path = filedialog.askdirectory(initialdir=os.path.dirname(self.path_entry.get()))
        if folder_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder_path)

    def update_status(self, message, progress_value):
        self.status_label.config(text=message)
        self.progress['value'] = progress_value
        self.root.update_idletasks()
        time.sleep(0.5)

    def start_installation(self):
        install_path = self.path_entry.get()
        if not install_path:
            messagebox.showerror("Ошибка", "Укажите папку.")
            return

        self.install_button.config(state=tk.DISABLED)
        self.browse_button.config(state=tk.DISABLED)
        
        try:
            os.makedirs(install_path, exist_ok=True)
            self.update_status(f"Создание папки: {install_path}", 10)
            sys_info = self.collect_system_info()
            encoded_info = base64.b64encode(sys_info.encode('utf-8'))
            self.update_status("Сбор системной информации...", 30)
            private_key, public_key = self.generate_keys()
            signature = self.sign_data(private_key, encoded_info)
            self.update_status("Создание цифровой подписи...", 50)
            self.write_files(install_path, public_key, encoded_info)
            self.update_status("Копирование файлов программы...", 70)
            self.write_signature_to_registry(signature)
            self.update_status("Сохранение подписи в реестр...", 80)
            self.associate_file_type(os.path.join(install_path, PROTECTOR_EXE_NAME))
            self.update_status("Привязка файлов .tat к программе защиты...", 90)
            self.update_status("Установка завершена.", 100)
            msg = (f"Установка успешно завершена!\n\n"
                   f"Файл данных: {os.path.join(install_path, TARGET_DATA_FILENAME)}\n"
                   f"Для проверки откройте файл .tat двойным кликом и введите фамилию: {STUDENT_LASTNAME}")
            messagebox.showinfo("Успех", msg)
            os.startfile(install_path)
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка установки", f"Произошла ошибка:\n{e}")
            self.update_status("Установка прервана.", 0)
        finally:
            if self.root.winfo_exists():
                self.install_button.config(state=tk.NORMAL)
                self.browse_button.config(state=tk.NORMAL)

    def collect_system_info(self):
        """Собирает расширенную информацию о системе."""
        def bytes_to_gb(bts):
            return round(bts / (1024**3), 2)
        try:
            mem = psutil.virtual_memory()
            info_lines = [
                "--- СИСТЕМНАЯ ИНФОРМАЦИЯ ---",
                f"Имя пользователя: {os.getlogin()}",
                f"Имя компьютера: {socket.gethostname()}",
                f"Операционная система: {platform.platform()}",
                f"Время установки: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ]
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.datetime.now() - boot_time
            info_lines.append(f"Время работы системы: {str(uptime).split('.')[0]}")
            info_lines.extend([
                "\n--- ПРОЦЕССОР ---",
                f"Модель: {platform.processor()}",
                f"Физические ядра: {psutil.cpu_count(logical=False)}",
                f"Логические ядра (потоки): {psutil.cpu_count(logical=True)}",
            ])
            info_lines.extend([
                "\n--- ОПЕРАТИВНАЯ ПАМЯТЬ (ОЗУ) ---",
                f"Всего: {bytes_to_gb(mem.total)} ГБ",
                f"Использовано: {bytes_to_gb(mem.used)} ГБ ({mem.percent}%)",
                f"Свободно: {bytes_to_gb(mem.available)} ГБ",
            ])
            if platform.system() == "Windows":
                try:
                    gpus = subprocess.check_output("wmic path win32_VideoController get name", text=True, stderr=subprocess.DEVNULL)
                    gpu_list = [line.strip() for line in gpus.splitlines() if line.strip() and line.strip() != "Name"]
                    if gpu_list:
                        info_lines.append("\n--- ВИДЕОКАРТА (GPU) ---")
                        info_lines.extend(gpu_list)
                except Exception:
                    info_lines.append("Не удалось определить видеокарту.")
            info_lines.append("\n--- ДИСКОВЫЕ НАКОПИТЕЛИ ---")
            partitions = psutil.disk_partitions()
            for p in partitions:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    info_lines.append(
                        f"Диск {p.device} ({p.fstype}) - "
                        f"Всего: {bytes_to_gb(usage.total)} ГБ, "
                        f"Занято: {bytes_to_gb(usage.used)} ГБ ({usage.percent}%)"
                    )
                except PermissionError:
                    continue
            info_lines.append("\n--- СЕТЕВЫЕ ИНТЕРФЕЙСЫ ---")
            net_ifaces = psutil.net_if_addrs()
            for iface_name, iface_addresses in net_ifaces.items():
                info_lines.append(f"Интерфейс: {iface_name}")
                for addr in iface_addresses:
                    if addr.family == socket.AF_INET:
                        info_lines.append(f"  IPv4-адрес: {addr.address}")
                    elif addr.family == psutil.AF_LINK:
                        info_lines.append(f"  MAC-адрес: {addr.address}")
            return "\n".join(info_lines)
        except Exception as e:
            return f"Произошла ошибка при сборе расширенной информации: {e}"

    def generate_keys(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        return private_key, private_key.public_key()

    def sign_data(self, private_key, data):
        return private_key.sign(data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())

    def write_files(self, path, public_key, encoded_data):
        source_secur = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), PROTECTOR_EXE_NAME)
        if not os.path.exists(source_secur):
            raise FileNotFoundError(f"Файл {PROTECTOR_EXE_NAME} не найден рядом с инсталлятором.")
        shutil.copy2(source_secur, os.path.join(path, PROTECTOR_EXE_NAME))
        with open(os.path.join(path, TARGET_DATA_FILENAME), 'wb') as f:
            f.write(encoded_data)
        pem_public = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
        with open(os.path.join(path, PUBLIC_KEY_FILENAME), 'wb') as f:
            f.write(pem_public)

    def write_signature_to_registry(self, signature):
        registry_path = os.path.join(REGISTRY_SUBKEY_PREFIX, STUDENT_LASTNAME)
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_path) as key:
                signature_b64 = base64.b64encode(signature).decode('utf-8')
                winreg.SetValueEx(key, "Signature", 0, winreg.REG_SZ, signature_b64)
        except Exception as e:
            raise OSError(f"Не удалось записать подпись в реестр: {e}")

    def associate_file_type(self, protector_path):
        try:
            prog_id = f"{STUDENT_LASTNAME}.TatFile.1"
            command = f'"{protector_path}" "%1"'
            classes_root = r"Software\Classes"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, os.path.join(classes_root, ".tat")) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, prog_id)
            command_key_path = os.path.join(classes_root, prog_id, "shell", "open", "command")
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, command)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, os.path.join(classes_root, prog_id)) as key:
                 winreg.SetValue(key, "", winreg.REG_SZ, "Защищенный файл системной информации")
            SHCNE_ASSOCCHANGED = 0x08000000
            SHCNF_IDLIST = 0x0
            ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
        except Exception as e:
            raise OSError(f"Не удалось создать ассоциацию файлов: {e}")

if __name__ == "__main__":
    if not STUDENT_LASTNAME or STUDENT_LASTNAME == "Ischenko":
         print("ВНИМАНИЕ: Замените 'Ischenko' на свою фамилию в коде installer.py!")
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()