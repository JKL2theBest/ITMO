import matplotlib.pyplot as plt
import pandas as pd

malloc_file = r"D:\Документы\Учеба\2 kurs\ОС\lab6\mallocfree\all_results.csv"
other_file = "memory_test_results.csv"

malloc_data = pd.read_csv(malloc_file)
malloc_data['AllocTime(us)'] = malloc_data['MallocTime(ns)'] / 1000
malloc_data['TotalTime(us)'] = malloc_data['TotalTime(ns)'] / 1000

other_data = pd.read_csv(other_file)

def plot_individual(data, functions, title, ylabel):
    plt.figure(figsize=(12, 8))
    for func in functions:
        subset = data[data['Function'] == func]
        plt.plot(subset['Size(Bytes)'], subset['TotalTime(us)'], 
                 marker='o' if func == 'calloc' else 's', 
                 linestyle='-', 
                 label=f"{func.capitalize()} Total Time")

    plt.xscale('log')
    plt.yscale('log')
    plt.title(title)
    plt.xlabel("Размер памяти (Байт)")
    plt.ylabel(ylabel)
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.legend()
    plt.show()

def plot_comparison(malloc_data, other_data, title, ylabel):
    plt.figure(figsize=(12, 8))
    
    # Malloc
    plt.plot(malloc_data['Size(Bytes)'], malloc_data['TotalTime(us)'], 
             marker='o', linestyle='-', label="Malloc Total Time")
    
    # Calloc and Realloc
    for func in ['calloc', 'realloc']:
        subset = other_data[other_data['Function'] == func]
        plt.plot(subset['Size(Bytes)'], subset['TotalTime(us)'], 
                 marker='o' if func == 'calloc' else 's', 
                 linestyle='--' if func == 'calloc' else '-.',
                 label=f"{func.capitalize()} Total Time")
    
    plt.xscale('log')
    plt.yscale('log')
    plt.title(title)
    plt.xlabel("Размер памяти (Байт)")
    plt.ylabel(ylabel)
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.legend()
    plt.show()

def plot_comparison_with_details(malloc_data, other_data, title, ylabel):
    plt.figure(figsize=(12, 8))

    plt.plot(malloc_data['Size(Bytes)'], malloc_data['TotalTime(us)'], 
             marker='o', linestyle='-', label="Malloc Total Time", color='blue')
    
    for func, color in zip(['calloc', 'realloc'], ['green', 'orange']):
        subset = other_data[other_data['Function'] == func]
        
        # AllocTime
        plt.plot(subset['Size(Bytes)'], subset['AllocTime(us)'], 
                 marker='^', linestyle='--', label=f"{func.capitalize()} Alloc Time", color=color)
        
        # FreeTime
        plt.plot(subset['Size(Bytes)'], subset['FreeTime(us)'], 
                 marker='v', linestyle=':', label=f"{func.capitalize()} Free Time", color=color)
        
        # TotalTime
        plt.plot(subset['Size(Bytes)'], subset['TotalTime(us)'], 
                 marker='o', linestyle='-', label=f"{func.capitalize()} Total Time", color=color)

    plt.xscale('log')
    plt.yscale('log')
    plt.title(title)
    plt.xlabel("Размер памяти (Байт)")
    plt.ylabel(ylabel)
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.legend()
    plt.show()

plot_comparison_with_details(malloc_data, other_data, 
                             "Сравнение Malloc, Calloc и Realloc Times", "Время (мкс)")

plot_comparison(malloc_data, other_data, 
                "Сравнение of Malloc, Calloc, and Realloc Total Time", "Время (мкс)")
