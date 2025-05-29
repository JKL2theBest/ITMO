import matplotlib.pyplot as plt
import pandas as pd

data = pd.read_csv('process_count.txt', delimiter=',')
data['Time'] = pd.to_datetime(data['Time'], format='%H:%M:%S')

plt.figure(figsize=(10, 5))
plt.plot(data['Time'], data['Count_processes'], marker='o')
plt.xlabel('Time')
plt.ylabel('Count_processes')
plt.title('Changes')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('process_count_graph.png')
plt.show()
