import matplotlib.pyplot as plt
import csv

def plot_results(filename, title, ylabel, label):
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

    plt.plot(sizes, malloc_times, marker='o', label=f"{label} Malloc/Alloc Time")
    plt.plot(sizes, free_times, marker='x', label=f"{label} Free/Free Time")
    plt.plot(sizes, total_times, marker='s', label=f"{label} Total Time")

def plot_comparison():
    plt.figure(figsize=(10, 6))

    plot_results("D:\\Документы\\Учеба\\2 kurs\\ОС\\lab6\\mallocfree\\all_results.csv", "Среванение времени для Malloc", "Время (нс)", "Malloc")

    plot_results("virtualalloc_results.csv", "Сравнение времени для VirtualAlloc", "Время (нс)", "VirtualAlloc")

    plt.title("Сравнение Memory Allocation: malloc() и VirtualAlloc()")
    plt.xlabel("Размер памяти (Байты)")
    plt.ylabel("Время (нс)")
    plt.xscale('log')
    plt.grid(True, linestyle="--")
    plt.legend()
    plt.show()

plot_comparison()
