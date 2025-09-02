# Суханкулиев Мухаммет, N3346, ТМПрог_ТЗИ_N3 1.5, Python 3.13.2
# Решение задания 2
import sys
import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import (
    cdist,
)  # Вместо sqrt((B[0] - A[0])**2 + (B[1] - A[1])**2)


def load_points(filepath):
    """Загружает точки из файла, обрабатывая запятую как десятичный разделитель."""
    points = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    processed_line = line_str.replace(",", ".")
                    parts = processed_line.split()
                    if len(parts) != 2:
                        raise ValueError("Не 2 координаты")
                    points.append([float(parts[0]), float(parts[1])])
                except (ValueError, IndexError):
                    raise ValueError(
                        f"Строка {i+1}: некорректный формат в '{line_str}'"
                    )
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл не найден: {filepath}")

    if not points:
        raise ValueError(f"Файл пуст или не содержит корректных строк: {filepath}")

    return np.array(points)


def solve_clusters(points, filepath, expected_clusters):
    """Кластеризует точки, находит d_min и d_max между кластерами."""
    db = DBSCAN(eps=1.0, min_samples=11).fit(points)
    labels = db.labels_
    unique_labels = set(labels) - {-1}

    if len(unique_labels) != expected_clusters:
        raise RuntimeError(
            f"В файле '{filepath}' найдено {len(unique_labels)} кластеров, "
            f"ожидалось {expected_clusters}. Проверьте данные или параметры DBSCAN."
        )

    if len(unique_labels) < 2:
        return 0.0, 0.0

    clusters = [points[labels == label] for label in unique_labels]
    d_min, d_max = float("inf"), 0.0

    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            distance_matrix = cdist(clusters[i], clusters[j])
            d_min = min(d_min, np.min(distance_matrix))
            d_max = max(d_max, np.max(distance_matrix))

    return d_min, d_max


def main():
    if len(sys.argv) < 3 or (len(sys.argv) - 1) % 2 != 0:
        print("Ошибка: Неверное количество аргументов.", file=sys.stderr)
        print("Пример: python main.py 27a.txt 2 27b.txt 3", file=sys.stderr)
        sys.exit(1)
    try:
        for i in range(1, len(sys.argv), 2):
            filepath = sys.argv[i]
            try:
                k = int(sys.argv[i + 1])
                if k < 1:
                    raise ValueError
            except ValueError:
                raise ValueError(
                    f"Число кластеров должно быть целым > 0: '{sys.argv[i + 1]}'"
                )

            points_data = load_points(filepath)
            d_min, d_max = solve_clusters(points_data, filepath, k)

            print(int(d_min * 10000))
            print(int(d_max * 10000))
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
