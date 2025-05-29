import matplotlib.pyplot as plt

process_counts = []

with open("log.txt", "r") as file:
    for line in file:
        line = line.strip()
        if line: 
            try:
                process_counts.append(int(line))
            except ValueError:
                print(f"Неправильная строка: {line} - пропущена.")

times = list(range(len(process_counts)))

if process_counts:
    plt.figure(figsize=(12, 6))
    plt.plot(times, process_counts, marker='o', color='b', linestyle='-')
    plt.title('Количество процессов во времени')
    plt.xlabel('Индекс (время)')
    plt.ylabel('Количество процессов')
    plt.grid()
    plt.show()
else:
    print("Нет доступных данных для построения графика.")
