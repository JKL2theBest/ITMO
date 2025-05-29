import matplotlib.pyplot as plt
import csv
import datetime
times = []
free_memory = []
with open('memory_log.csv', 'r') as file:
    reader = csv.reader(file)
    next(reader)  
    for row in reader:
        timestamp = float(row[0])
        memory = int(row[1])
        times.append(datetime.datetime.fromtimestamp(timestamp))
        free_memory.append(memory)
plt.figure(figsize=(10, 6))
plt.plot(times, free_memory, label="Free Memory (kB)", color="blue", linewidth=2)
plt.xlabel('Time')
plt.ylabel('Free Memory (kB)')
plt.title('Free Memory Over Time During Membomb Execution')
plt.grid(True)
plt.legend()
plt.show()
