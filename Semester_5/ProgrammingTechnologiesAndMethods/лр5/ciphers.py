"""
Модуль, содержащий бизнес-логику алгоритмов шифрования.
"""

import math
import random
from typing import List, Tuple

# --- Шифр Скитала ---


def scytale_encrypt(text: str, key: int) -> str:
    """Шифрование текста методом Скиталы."""
    if not isinstance(key, int) or key <= 0:
        raise ValueError("Ключ должен быть положительным целым числом.")
    if not text:
        return ""
    num_cols = math.ceil(len(text) / key)
    padded_text = text.ljust(key * num_cols)
    matrix = [[""] * num_cols for _ in range(key)]
    char_index = 0
    for row in range(key):
        for col in range(num_cols):
            matrix[row][col] = padded_text[char_index]
            char_index += 1
    ciphertext_parts = [matrix[r][c] for c in range(num_cols) for r in range(key)]
    return "".join(ciphertext_parts)


def scytale_decrypt(ciphertext: str, key: int) -> str:
    """Дешифрование текста, зашифрованного методом Скиталы."""
    if not isinstance(key, int) or key <= 0:
        raise ValueError("Ключ должен быть положительным целым числом.")
    if not ciphertext:
        return ""
    num_cols = math.ceil(len(ciphertext) / key)
    num_rows = key
    matrix = [[""] * num_cols for _ in range(num_rows)]
    char_index = 0
    for col in range(num_cols):
        for row in range(num_rows):
            if char_index < len(ciphertext):
                matrix[row][col] = ciphertext[char_index]
                char_index += 1
    plaintext_parts = [matrix[r][c] for r in range(num_rows) for c in range(num_cols)]
    return "".join(plaintext_parts).rstrip()


# --- Решётка Кардано ---


def _rotate_grille_90_clockwise(grille: List[List[bool]]) -> List[List[bool]]:
    """Вспомогательная функция для поворота решётки на 90 градусов."""
    size = len(grille)
    new_grille = [[False] * size for _ in range(size)]
    for r in range(size):
        for c in range(size):
            new_grille[c][size - 1 - r] = grille[r][c]
    return new_grille


def cardan_generate_grille(size: int) -> List[List[bool]]:
    """Генерирует валидную решётку Кардано заданного размера."""
    if not isinstance(size, int) or size <= 0 or size % 2 != 0:
        raise ValueError("Размер решётки должен быть чётным положительным числом.")
    grille = [[False] * size for _ in range(size)]
    temp_matrix = [[False] * size for _ in range(size)]
    holes_to_make = (size * size) // 4
    hole_count = 0
    all_coords = [(r, c) for r in range(size) for c in range(size)]
    random.shuffle(all_coords)
    for r, c in all_coords:
        coords: List[Tuple[int, int]] = [
            (r, c),
            (c, size - 1 - r),
            (size - 1 - r, size - 1 - c),
            (size - 1 - c, r),
        ]
        if all(not temp_matrix[row][col] for row, col in coords):
            grille[r][c] = True
            hole_count += 1
            for row, col in coords:
                temp_matrix[row][col] = True
        if hole_count == holes_to_make:
            break
    return grille


def cardan_encrypt(text: str, grille: List[List[bool]]) -> str:
    """Шифрование текста с использованием решётки Кардано."""
    size = len(grille)
    if not all(len(row) == size for row in grille):
        raise ValueError("Решётка должна быть квадратной.")
    if len(text) != size * size:
        raise ValueError(f"Длина текста ({len(text)}) должна быть равна {size*size}.")
    current_grille = grille
    result_matrix = [[""] * size for _ in range(size)]
    text_idx = 0
    for _ in range(4):
        for r in range(size):
            for c in range(size):
                if current_grille[r][c]:
                    result_matrix[r][c] = text[text_idx]
                    text_idx += 1
        current_grille = _rotate_grille_90_clockwise(current_grille)
    return "".join("".join(row) for row in result_matrix)


def cardan_decrypt(ciphertext: str, grille: List[List[bool]]) -> str:
    """Дешифрование текста, зашифрованного решёткой Кардано."""
    size = len(grille)
    if not all(len(row) == size for row in grille):
        raise ValueError("Решётка должна быть квадратной.")
    if len(ciphertext) != size * size:
        raise ValueError(
            f"Длина шифротекста ({len(ciphertext)}) должна быть равна {size*size}."
        )
    cipher_matrix = [[""] * size for _ in range(size)]
    char_idx = 0
    for r in range(size):
        for c in range(size):
            cipher_matrix[r][c] = ciphertext[char_idx]
            char_idx += 1
    current_grille = grille
    plaintext_parts = []
    for _ in range(4):
        for r in range(size):
            for c in range(size):
                if current_grille[r][c]:
                    plaintext_parts.append(cipher_matrix[r][c])
        current_grille = _rotate_grille_90_clockwise(current_grille)
    return "".join(plaintext_parts)
