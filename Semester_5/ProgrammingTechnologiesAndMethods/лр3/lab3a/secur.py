import os
import sys
import base64
import winreg
import tkinter as tk
from tkinter import simpledialog, messagebox
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

# --- Константы ---
PUBLIC_KEY_FILE = "public_key.pem"
REGISTRY_SUBKEY_PREFIX = "Software"


def show_message(title, message, is_error=False):
    """Для отображения GUI-сообщений."""
    root = tk.Tk()
    root.withdraw()
    if is_error:
        messagebox.showerror(title, message)
    else:
        messagebox.showinfo(title, message)
    root.destroy()


def get_signature_from_registry(student_lastname):
    """Считывает подпись из реестра HKCU по указанному пути."""
    registry_path = os.path.join(REGISTRY_SUBKEY_PREFIX, student_lastname)
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_READ
        ) as key:
            # Подпись хранится как строка в формате Base64, декодируем ее обратно в байты.
            signature_b64, _ = winreg.QueryValueEx(key, "Signature")
            return base64.b64decode(signature_b64)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Раздел реестра HKEY_CURRENT_USER\\{registry_path} не найден."
        )
    except Exception as e:
        raise Exception(f"Ошибка при чтении из реестра: {e}")


def main():
    if len(sys.argv) < 2:
        show_message(
            "Ошибка запуска",
            "Программа запущена неправильно.\n\nПожалуйста, откройте файл .tat.",
            is_error=True,
        )
        return

    target_file_path = sys.argv[1]
    if target_file_path.startswith('"') and target_file_path.endswith('"'):
        target_file_path = target_file_path[1:-1]

    if not os.path.exists(target_file_path):
        show_message("Ошибка", f"Файл не найден: {target_file_path}", is_error=True)
        return

    base_dir = os.path.dirname(
        os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__)
    )
    public_key_path = os.path.join(base_dir, PUBLIC_KEY_FILE)
    if not os.path.exists(public_key_path):
        show_message(
            "Ошибка конфигурации",
            f"Открытый ключ не найден: {public_key_path}",
            is_error=True,
        )
        return

    # Запрос у пользователя идентификатора (фамилии) для поиска подписи в реестре.
    root = tk.Tk()
    root.withdraw()
    student_lastname = simpledialog.askstring(
        "Проверка доступа",
        "Введите фамилию (имя раздела реестра) для проверки подписи:",
        parent=root,
    )
    root.destroy()

    if not student_lastname:
        return

    try:
        signature = get_signature_from_registry(student_lastname)
        with open(target_file_path, "rb") as f:
            encoded_data = f.read()
        with open(public_key_path, "rb") as key_file:
            public_key = serialization.load_pem_public_key(key_file.read())
        # Проверка, что подпись соответствует данным и открытому ключу.
        public_key.verify(
            signature,
            encoded_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        decoded_data = base64.b64decode(encoded_data).decode("utf-8")
        show_message("Доступ разрешен", f"Подпись корректна.\n\n{decoded_data}")
    except FileNotFoundError as e:
        show_message("Ошибка реестра", str(e), is_error=True)
    except InvalidSignature:
        show_message(
            "Доступ запрещен",
            "Неверная подпись или данные были изменены.\nРабота программы прекращена.",
            is_error=True,
        )
    except Exception as e:
        show_message("Критическая ошибка", f"Произошла ошибка:\n{e}", is_error=True)


if __name__ == "__main__":
    main()
