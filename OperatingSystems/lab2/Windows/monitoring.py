import psutil
import csv
import time


with open('memory_log.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Time', 'FreeMemory(MB)'])

    try:
        while True:
            free_memory = psutil.virtual_memory().available / (1024 * 1024) 
            writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), free_memory])
            time.sleep(1)  
    except KeyboardInterrupt:
        print("Logging stopped.")
