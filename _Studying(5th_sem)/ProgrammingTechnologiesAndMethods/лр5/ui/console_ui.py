# -*- coding: utf-8 -*-
import random
from ciphers import scytale, cardan_grille

class UserExitException(Exception): pass

# ИСПРАВЛЕНИЕ: .strip() УБРАН ИЗ ЭТОЙ ЦЕНТРАЛЬНОЙ ФУНКЦИИ
def _get_robust_input(prompt: str) -> str:
    user_input = input(prompt) # .strip() удален отсюда
    if user_input.strip().lower() in ['выход', 'exit', 'quit']: 
        raise UserExitException()
    return user_input

def _read_from_file(filepath: str):
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return f.read()
    except Exception: print(f"Ошибка: Файл не найден: {filepath}"); return None

def _write_to_file(filepath: str, content: str) -> bool:
    try:
        with open(filepath, 'w', encoding='utf-8') as f: f.write(content); return True
    except Exception as e: print(f"Ошибка записи в файл: {e}"); return False

def _get_user_text(prompt: str) -> str:
    while True:
        # .strip() применяется здесь, к команде
        choice = _get_robust_input("Источник текста (1 - консоль, 2 - файл): ").strip()
        if choice == '1': 
            # Здесь .strip() НЕ применяется, мы получаем "сырой" текст
            return _get_robust_input(prompt)
        if choice == '2':
            filepath = _get_robust_input("Путь к файлу: ").strip()
            content = _read_from_file(filepath)
            if content is not None: return content
        else: print("Неверный выбор. Введите 1 или 2.")

def _output_result(result: str):
    while True:
        choice = _get_robust_input("Вывести результат (1 - консоль, 2 - файл): ").strip()
        if choice == '1': print(f"\n--- Результат ---\n{result}\n-----------------"); return
        if choice == '2':
            filepath = _get_robust_input("Путь для сохранения: ").strip()
            if _write_to_file(filepath, result): print(f"Результат сохранен в {filepath}"); return
        else: print("Неверный выбор. Введите 1 или 2.")

def _handle_scytale():
    try:
        mode = _get_robust_input("Режим (1-шифр, 2-дешифр): ").strip()
        if mode not in ['1', '2']: print("Неверный режим."); return
        text = _get_user_text("Текст: ")
        key = int(_get_robust_input("Ключ: ").strip())
        result = scytale.encrypt(text, key) if mode == '1' else scytale.decrypt(text, key)
        print("Операция выполнена."); _output_result(result)
    except (ValueError, TypeError) as e: print(f"\nОшибка ввода: {e}")

def _handle_cardan_grille():
    try:
        mode = _get_robust_input("Режим (1-шифр, 2-дешифр): ").strip()
        if mode not in ['1', '2']: print("Неверный режим."); return
        key_phrase = _get_robust_input("Ключевое слово/число: ").strip()
        random.seed(key_phrase)
        size = int(_get_robust_input("Размер решётки: ").strip())
        grille = cardan_grille.generate_grille(size)
        print("\n(Решётка сгенерирована)")
        text = _get_user_text("Текст: ")
        if mode == '1':
            padded = text.ljust(size*size, '_')[:size*size]
            result = cardan_grille.encrypt(padded, grille)
        else:
            # Важно: здесь text уже "сырой", без strip()
            if len(text) != size*size: print(f"Ошибка: длина текста ({len(text)}) должна быть {size*size}."); return
            result = cardan_grille.decrypt(text, grille).rstrip('_')
        print("Операция выполнена."); _output_result(result)
    except (ValueError, TypeError) as e: print(f"\nОшибка ввода: {e}")

def start_ui():
    while True:
        try:
            print("\n" + "="*5 + " Меню " + "="*5); print("1. Скитала\n2. Решётка Кардано\n3. Выход")
            choice = _get_robust_input("Выберите алгоритм: ").strip()
            if choice == '1': _handle_scytale()
            elif choice == '2': _handle_cardan_grille()
            elif choice == '3': break
            else: print("Неверный выбор.")
            input("\nНажмите Enter для продолжения...")
        except UserExitException: break
        except KeyboardInterrupt: print("\nВыход по Ctrl+C."); break
    print("Завершение работы.")