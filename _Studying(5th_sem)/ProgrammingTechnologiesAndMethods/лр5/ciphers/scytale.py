# -*- coding: utf-8 -*-

"""
Модуль реализации алгоритма шифрования "Скитала".

Содержит функции для шифрования и дешифрования текста методом
простой табличной перестановки, имитирующей древнегреческую скиталу.
"""

import math
from typing import List

def encrypt(text: str, key: int) -> str:
    """
    Выполняет шифрование текста с использованием алгоритма "Скитала".

    Данный метод имитирует запись сообщения на пергаментную ленту,
    намотанную на цилиндр. Ключ `key` соответствует количеству строк
    в результирующей матрице (диаметру скиталы).

    Args:
        text (str): Исходный текст для шифрования.
        key (int): Целочисленный ключ (диаметр), должен быть > 0.

    Returns:
        str: Зашифрованный текст.

    Raises:
        ValueError: Если ключ не является положительным целым числом.
    """
    if not isinstance(key, int) or key <= 0:
        raise ValueError("Ключ должен быть положительным целым числом.")

    if not text:
        return ""

    num_cols = math.ceil(len(text) / key)
    padded_text = text.ljust(key * num_cols)
    
    matrix: List[List[str]] = [
        [''] * num_cols for _ in range(key)
    ]

    char_index = 0
    for row in range(key):
        for col in range(num_cols):
            matrix[row][col] = padded_text[char_index]
            char_index += 1

    ciphertext_parts = []
    for col in range(num_cols):
        for row in range(key):
            ciphertext_parts.append(matrix[row][col])
            
    return "".join(ciphertext_parts)


def decrypt(ciphertext: str, key: int) -> str:
    """
    Выполняет дешифрование текста, зашифрованного алгоритмом "Скитала".

    Процесс дешифрования является обратным шифрованию: символы
    шифротекста записываются в матрицу по столбцам, а исходный текст
    считывается по строкам.

    Args:
        ciphertext (str): Зашифрованный текст.
        key (int): Целочисленный ключ (диаметр), который использовался
                   при шифровании.

    Returns:
        str: Расшифрованный исходный текст.

    Raises:
        ValueError: Если ключ не является положительным целым числом.
    """
    if not isinstance(key, int) or key <= 0:
        raise ValueError("Ключ должен быть положительным целым числом.")
    
    if not ciphertext:
        return ""

    num_cols = math.ceil(len(ciphertext) / key)
    num_rows = key
    
    matrix: List[List[str]] = [
        [''] * num_cols for _ in range(num_rows)
    ]

    char_index = 0
    for col in range(num_cols):
        for row in range(num_rows):
            if char_index < len(ciphertext):
                matrix[row][col] = ciphertext[char_index]
                char_index += 1

    plaintext_parts = []
    for row in range(num_rows):
        for col in range(num_cols):
            plaintext_parts.append(matrix[row][col])
            
    return "".join(plaintext_parts).rstrip()