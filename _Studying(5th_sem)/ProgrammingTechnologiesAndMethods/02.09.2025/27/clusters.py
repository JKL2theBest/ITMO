import sys
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from main import load_points
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="joblib")


def create_visualization(filepath):
    try:
        print(f"Обработка файла: {filepath}...")
        points = load_points(filepath)
        db = DBSCAN(eps=1.0, min_samples=11).fit(points)
        labels = db.labels_
        unique_labels = set(labels)

        plt.figure(figsize=(10, 8))
        colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))

        for k, col in zip(unique_labels, colors):
            label = "Аномалии" if k == -1 else f"Кластер {k}"
            color = "black" if k == -1 else col

            class_mask = labels == k
            xy = points[class_mask]
            plt.plot(
                xy[:, 0],
                xy[:, 1],
                "o",
                markerfacecolor=tuple(color),
                markeredgecolor="k",
                markersize=6,
                label=label,
            )

        num_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        plt.title(f"Найдено кластеров: {num_clusters}")
        plt.xlabel("Координата X")
        plt.ylabel("Координата Y")
        plt.legend()
        plt.grid(True)

        output_filename = f"{filepath.split('/')[-1].split('.')[0]}_visualization.png"
        plt.savefig(output_filename)
        print(f"График сохранен в файл: {output_filename}")
        plt.show()

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Ошибка: Требуется ровно один аргумент - имя файла.", file=sys.stderr)
        print("Пример: python visualize.py ../27a.txt", file=sys.stderr)
        sys.exit(1)

    create_visualization(sys.argv[1])
