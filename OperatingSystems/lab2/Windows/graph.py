import matplotlib.pyplot as plt
import pandas as pd

data = pd.read_csv('memory_log.csv')

data['Time'] = pd.to_datetime(data['Time'])

# Строим график
plt.figure(figsize=(10, 5))
plt.plot(data['Time'], data['FreeMemory(MB)'], marker='o', linestyle='-')
plt.title('Free Memory Over Time')
plt.xlabel('Time')
plt.ylabel('Free Memory (MB)')
plt.xticks(rotation=45)
plt.tight_layout() 
plt.grid()
plt.savefig('memory_graph.png')  
plt.show() 
