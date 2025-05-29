import matplotlib.pyplot as plt
import csv

def plot_results(filename, title, ylabel):
    sizes = []
    alloc_times = []
    free_times = []
    total_times = []

    with open(filename) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            sizes.append(int(row[0]))
            alloc_times.append(float(row[1]))
            free_times.append(float(row[2]))
            total_times.append(float(row[3]))

    plt.figure(figsize=(10, 6))
    plt.plot(sizes, alloc_times, marker='o', label="VirtualAlloc Time")
    plt.plot(sizes, free_times, marker='x', label="VirtualFree Time")
    plt.plot(sizes, total_times, marker='s', label="Total Time")
    plt.title(title)
    plt.xlabel("Размер памяти (Байт)")
    plt.ylabel(ylabel)
    plt.grid(True, linestyle="--")
    plt.legend()
    plt.xscale('log')
    plt.show()

# Построение графика для всех данных
plot_results("virtualalloc_results.csv", "Время VirtualAlloc(), VirtualFree() и общее время", "Время (нс)")
