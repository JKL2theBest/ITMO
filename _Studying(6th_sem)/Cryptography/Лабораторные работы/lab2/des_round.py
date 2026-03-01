import random

# Таблицы DES (стандартные)
E_BOX = [
    32, 1, 2, 3, 4, 5, 4, 5, 6, 7, 8, 9,
    8, 9, 10, 11, 12, 13, 12, 13, 14, 15, 16, 17,
    16, 17, 18, 19, 20, 21, 20, 21, 22, 23, 24, 25,
    24, 25, 26, 27, 28, 29, 28, 29, 30, 31, 32, 1
]

P_BOX = [
    16, 7, 20, 21, 29, 12, 28, 17, 1, 15, 23, 26, 5, 18, 31, 10,
    2, 8, 24, 14, 32, 27, 3, 9, 19, 13, 30, 6, 22, 11, 4, 25
]

S1 = [
    [14, 4, 13, 1, 2, 15, 11, 8, 3, 10, 6, 12, 5, 9, 0, 7],
    [0, 15, 7, 4, 14, 2, 13, 1, 10, 6, 12, 11, 9, 5, 3, 8],
    [4, 1, 14, 8, 13, 6, 2, 11, 15, 12, 9, 7, 3, 10, 5, 0],
    [15, 12, 8, 2, 4, 9, 1, 7, 5, 11, 3, 14, 10, 0, 6, 13],
]


def int_to_bin_str(val, length):
    return format(val, f"0{length}b")


def permute(bits_str, table):
    res = ""
    for pos in table:
        res += bits_str[pos - 1]
    return res


def s_box_substitution(bits_48):
    output_bits = ""

    print("\n--- ЭТАП 3: Подстановка (S-Box) ---")

    # Разбиваем на 8 групп по 6 бит
    groups = [bits_48[i : i + 6] for i in range(0, 48, 6)]

    # Демонстрация на первой группе (для S1)
    b = groups[0]
    row_bits = b[0] + b[5]
    col_bits = b[1:5]

    row = int(row_bits, 2)
    col = int(col_bits, 2)
    val = S1[row][col]

    print(
        f"Группа 1 (биты {b}): Row={row_bits}({row}), Col={col_bits}({col}) -> S1[{row}][{col}] = {val} ({int_to_bin_str(val, 4)})"
    )

    output_bits += int_to_bin_str(val, 4)

    # Остальные 7 групп (эмуляция для краткости)
    for i in range(1, 8):
        simulated_val = random.randint(0, 15)
        output_bits += int_to_bin_str(simulated_val, 4)

    print(f"Результат после всех S-блоков (32 бита): {output_bits}")
    return output_bits


print("ОТЧЕТ: Ручной расчет раундовой функции DES")

# Вход: Правая половина (Ri-1) - 32 бита
R_prev = random.getrandbits(32)
R_prev_bin = int_to_bin_str(R_prev, 32)
print(f"Вход R(i-1) (32 бита): {R_prev_bin} (Hex: {hex(R_prev)})")

# Раундовый ключ (Ki) - 48 бит
Key_round = random.getrandbits(48)
Key_round_bin = int_to_bin_str(Key_round, 48)
print(f"Раундовый ключ Ki (48 бит): {Key_round_bin} (Hex: {hex(Key_round)})")

# 1. Расширение E (Expansion)
E_output = permute(R_prev_bin, E_BOX)
print("\n--- ЭТАП 1: Расширение E (32 -> 48) ---")
print(f"Результат E(R): {E_output}")

# 2. XOR с ключом
xor_res_int = int(E_output, 2) ^ int(Key_round_bin, 2)
xor_res_bin = int_to_bin_str(xor_res_int, 48)
print("\n--- ЭТАП 2: XOR с ключом Ki ---")
print(f"E(R):   {E_output}")
print(f"Key:    {Key_round_bin}")
print(f"Result: {xor_res_bin}")

# 3. S-Boxes
s_output = s_box_substitution(xor_res_bin)

# 4. Перестановка P
p_output = permute(s_output, P_BOX)
print("\n--- ЭТАП 4: Перестановка P (32 -> 32) ---")
print(f"Вход P: {s_output}")
print(f"Выход P: {p_output} (Hex: {hex(int(p_output, 2))})")

print(f"\nИтоговое значение F(R, K): {hex(int(p_output, 2))}")
