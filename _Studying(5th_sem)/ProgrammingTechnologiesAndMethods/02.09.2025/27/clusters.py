import sys
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from main import load_points
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="joblib")


def create_visualization(filepath):
    """Создает и сохраняет график кластеризации для данных из файла."""
    try:
        print(f"Обработка файла: {filepath}...")
        points = load_points(filepath)
        db = DBSCAN(eps=1.0, min_samples=11).fit(points)
        labels = db.labels_
        unique_labels = set(labels)

        plt.figure(figsize=(10, 8))
        cluster_labels = [l for l in unique_labels if l != -1]
        colors = plt.cm.Spectral(np.linspace(0, 1, len(cluster_labels)))

        color_map = {label: color for label, color in zip(cluster_labels, colors)}
        color_map[-1] = "black"

        for k in unique_labels:
            label = "Аномалии" if k == -1 else f"Кластер {k}"

            class_mask = labels == k
            xy = points[class_mask]

            plt.plot(
                xy[:, 0],
                xy[:, 1],
                "o",
                markerfacecolor=color_map[k],
                markeredgecolor="k",
                markersize=6,
                label=label,
            )

        num_clusters = len(cluster_labels)
        plt.title(f"Найдено кластеров: {num_clusters}")
        plt.xlabel("Координата X")
        plt.ylabel("Координата Y")
        plt.legend()
        plt.grid(True)

        base_name = filepath.split("/")[-1].split("\\")[-1].split(".")[0]
        output_filename = f"{base_name}_visualization.png"

        plt.savefig(output_filename)
        print(f"График сохранен в файл: {output_filename}")
        plt.show()

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Ошибка: Требуется ровно один аргумент - имя файла.", file=sys.stderr)
        print("Пример: python clusters.py ../27a.txt", file=sys.stderr)
        sys.exit(1)

    create_visualization(sys.argv[1])
