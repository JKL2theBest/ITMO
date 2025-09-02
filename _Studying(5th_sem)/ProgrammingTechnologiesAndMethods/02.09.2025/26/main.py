import sys


def find_best_pair(lines):
    """
    Анализирует данные о занятых местах и находит лучшую доступную пару
    соседних мест в соответствии с условиями задачи.
    """
    if not lines:
        raise ValueError("Файл пустой.")

    first_line_str = lines[0].strip()
    first_line_parts = first_line_str.split()

    if len(first_line_parts) != 3:
        raise ValueError(
            f"Строка 1: ожидалось 3 числа, найдено {len(first_line_parts)} ('{first_line_str}')"
        )
    try:
        N, M, K = map(int, first_line_parts)
    except ValueError:
        raise ValueError(f"Строка 1: нечисловые данные в '{first_line_str}'")

    if not (N >= 0 and M > 0 and K > 0):
        raise ValueError(
            f"Строка 1: неверные параметры N={N}, M={M}, K={K} (M, K должны быть > 0)"
        )

    occupied_seats = set()
    min_row_for_col = {}

    for i, line in enumerate(lines[1 : N + 1]):
        line_num = i + 2
        line_str = line.strip()
        parts = line_str.split()

        if len(parts) != 2:
            raise ValueError(
                f"Строка {line_num}: ожидалось 2 числа, найдено {len(parts)} ('{line_str}')"
            )
        try:
            r, s = map(int, parts)
        except ValueError:
            raise ValueError(f"Строка {line_num}: нечисловые координаты в '{line_str}'")

        if not (1 <= r <= M and 1 <= s <= K):
            raise ValueError(
                f"Строка {line_num}: координата ({r}, {s}) вне зала {M}x{K}"
            )

        occupied_seats.add((r, s))
        min_row_for_col[s] = min(min_row_for_col.get(s, M + 1), r)

    best_r, best_p_plus_1 = 0, 0

    for p in range(1, K):
        limit_row_p = min_row_for_col.get(p, M + 1)
        limit_row_p1 = min_row_for_col.get(p + 1, M + 1)
        candidate_r = min(limit_row_p, limit_row_p1) - 1

        if candidate_r < 1:
            continue

        if (candidate_r, p) not in occupied_seats and (
            candidate_r,
            p + 1,
        ) not in occupied_seats:
            if candidate_r > best_r:
                best_r, best_p_plus_1 = candidate_r, p + 1
            elif candidate_r == best_r and (p + 1) > best_p_plus_1:
                best_p_plus_1 = p + 1

    # По условию задачи решение гарантированно существует.
    # То есть этот блок является защитой на случай, если входные данные нарушат это условие.
    if best_r == 0:
        raise RuntimeError("Не удалось найти подходящую пару мест.")

    return best_r, best_p_plus_1


def main():
    if len(sys.argv) != 2:
        print("Ошибка: Требуется ровно один аргумент - имя файла.", file=sys.stderr)
        print("Пример использования: python main.py 26.txt", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        result_r, result_s = find_best_pair(lines)
        print(result_r, result_s)

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
