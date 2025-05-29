import matplotlib.pyplot as plt
import pandas as pd

data = pd.read_csv('process_count.txt', delimiter=',')
data['Время'] = pd.to_datetime(data['Время'], format='%H:%M:%S')

plt.figure(figsize=(10, 5))
plt.plot(data['Время'], data['Число процессов'], marker='o')
plt.xlabel('Время')
plt.ylabel('Число процессов')
plt.title('Изменение числа процессов во времени')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('process_count_graph.png')
plt.show()
