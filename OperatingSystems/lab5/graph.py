import pandas as pd
import matplotlib.pyplot as plt

bonnie_file = './bonnie_processed.csv'
iozone_file = './iozone_processed.csv'

bonnie_data = pd.read_csv(bonnie_file)
iozone_data = pd.read_csv(iozone_file)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

bonnie_data.plot(kind='bar', x='fs_name', y=['write_speed_kB_per_sec', 'read_speed_kB_per_sec', 'latency_rewrite_us'], 
                 ax=ax1, width=0.8, position=1, color=['blue', 'green', 'red'])

ax1.set_title('Bonnie Benchmark')
ax1.set_xlabel('File System')
ax1.set_ylabel('Speed (kB/s) / Latency (us)')
ax1.set_xticklabels(bonnie_data['fs_name'], rotation=45)
ax1.legend(title="Metrics", loc='upper left')

iozone_data.plot(kind='bar', x='fs_name', y=['write', 'rewrite', 'read', 'reread', 'random_write', 'random_read'],
                 stacked=True, ax=ax2, width=0.8, color=['blue', 'green', 'red', 'orange', 'purple', 'brown'])

ax2.set_title('IOzone Benchmark (Stacked)')
ax2.set_xlabel('File System')
ax2.set_ylabel('Operations Count')
ax2.set_xticklabels(iozone_data['fs_name'], rotation=45)
ax2.legend(title="Operations", loc='upper left')

plt.tight_layout()
plt.show()
