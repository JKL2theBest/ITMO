import matplotlib.pyplot as plt
import csv

def plot_results(filename, title, ylabel):
    sizes = []
    malloc_times = []
    free_times = []
    total_times = []

    with open(filename) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            sizes.append(int(row[0]))
            malloc_times.append(float(row[1]))
            free_times.append(float(row[2]))
            total_times.append(float(row[3]))

    plt.figure(figsize=(10, 6))
    plt.plot(sizes, malloc_times, marker='o', label="Malloc Time")
    plt.plot(sizes, free_times, marker='x', label="Free Time")
    plt.plot(sizes, total_times, marker='s', label="Total Time")
    plt.title(title)
    plt.xlabel("Размер памяти (Байт)")
    plt.ylabel(ylabel)
    plt.grid(True, linestyle="--")
    plt.legend()
    plt.xscale('log')
    plt.show()

plot_results("all_results.csv", "Время malloc(), free() и их общее время", "Время (нс)")
