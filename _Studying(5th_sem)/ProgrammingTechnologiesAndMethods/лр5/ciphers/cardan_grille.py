# -*- coding: utf-8 -*-

"""
Модуль реализации алгоритма шифрования "Решётка Кардано".

Содержит функции для генерации решётки, шифрования и дешифрования
текста методом перестановок с использованием поворачиваемого трафарета.
"""

import random
from typing import List, Tuple

def _rotate_grille_90_clockwise(grille: List[List[bool]]) -> List[List[bool]]:
    """Вспомогательная функция для поворота решётки на 90 градусов."""
    size = len(grille)
    new_grille = [[False] * size for _ in range(size)]
    for r in range(size):
        for c in range(size):
            new_grille[c][size - 1 - r] = grille[r][c]
    return new_grille

def generate_grille(size: int) -> List[List[bool]]:
    """
    Генерирует валидную решётку Кардано заданного размера.

    Решётка валидна, если при четырёх поворотах отверстия не перекрывают
    друг друга и покрывают всю площадь матрицы ровно один раз.

    Args:
        size (int): Размер стороны квадратной решётки. Должен быть чётным.

    Returns:
        List[List[bool]]: Сгенерированная решётка (True - отверстие).

    Raises:
        ValueError: Если размер не является чётным положительным числом.
    """
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
            (size - 1 - c, r)
        ]
        is_free = all(not temp_matrix[row][col] for row, col in coords)

        if is_free:
            grille[r][c] = True
            hole_count += 1
            for row, col in coords:
                temp_matrix[row][col] = True
        
        if hole_count == holes_to_make:
            break
            
    return grille

def encrypt(text: str, grille: List[List[bool]]) -> str:
    """
    Выполняет шифрование текста с использованием решётки Кардано.
    """
    size = len(grille)
    if not all(len(row) == size for row in grille):
        raise ValueError("Решётка должна быть квадратной.")
    
    if len(text) != size * size:
        raise ValueError(
            f"Длина текста ({len(text)}) должна быть равна "
            f"размеру решётки {size}x{size} ({size*size})."
        )

    current_grille = grille
    result_matrix = [[''] * size for _ in range(size)]
    text_idx = 0

    for _ in range(4):
        for r in range(size):
            for c in range(size):
                if current_grille[r][c]:
                    result_matrix[r][c] = text[text_idx]
                    text_idx += 1
        current_grille = _rotate_grille_90_clockwise(current_grille)

    # --- ИСПРАВЛЕНИЕ БЫЛО ЗДЕСЬ ---
    # Было: result_matr
    # Стало: result_matrix
    return "".join("".join(row) for row in result_matrix)

def decrypt(ciphertext: str, grille: List[List[bool]]) -> str:
    """
    Выполняет дешифрование текста, зашифрованного решёткой Кардано.
    """
    size = len(grille)
    if not all(len(row) == size for row in grille):
        raise ValueError("Решётка должна быть квадратной.")

    if len(ciphertext) != size * size:
        raise ValueError(
            f"Длина шифротекста ({len(ciphertext)}) должна быть равна "
            f"размеру решётки {size}x{size} ({size*size})."
        )
                         
    cipher_matrix = [[''] * size for _ in range(size)]
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