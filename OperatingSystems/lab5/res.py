import re
import os

def process_bonnie_log(input_file, fs_name, output_file):
    with open(input_file, 'r') as infile:
        write_header = not os.path.exists(output_file) or os.stat(output_file).st_size == 0
        lines = infile.readlines()
        if len(lines) < 24:
            print(f"Ошибка: в файле {input_file} меньше 24 строк.")
            return
        line = lines[23]
        parts = line.split(',')
        if len(parts) < 6:
            print(f"Ошибка: в строке 24 файла {input_file} недостаточно элементов.")
            return
        write_speed = parts[9]
        read_speed = parts[15]
        latency_rewrite = parts[40]
        latency_rewrite = latency_rewrite.replace('us', '').strip()
        with open(output_file, 'a') as outfile:
            if write_header:
                outfile.write("fs_name,write_speed_kB_per_sec,read_speed_kB_per_sec,latency_rewrite_us\n")
            outfile.write(f"{fs_name},{write_speed},{read_speed},{latency_rewrite}\n")

def process_iozone_log(input_file, fs_name, output_file):
    with open(input_file, 'r') as infile:
        write_header = not os.path.exists(output_file) or os.stat(output_file).st_size == 0
        lines = infile.readlines()
        if len(lines) < 29:
            print(f"Ошибка: в файле {input_file} меньше 29 строк.")
            return
        line = lines[28]
        line = re.sub(r'\s+', ',', line.strip())
        parts = line.split(',')
        selected_values = parts[2:8]
        with open(output_file, 'a') as outfile:
            if write_header:
                outfile.write("fs_name,write,rewrite,read,reread,random_write,random_read\n")
            outfile.write(f"{fs_name}," + ",".join(selected_values) + "\n")

def process_all_logs(directory, bonnie_output_file, iozone_output_file):
    open(bonnie_output_file, 'w').close()
    open(iozone_output_file, 'w').close()
    for filename in os.listdir(directory):
        if filename.startswith("bonnie") and filename.endswith(".log"):
            input_file = os.path.join(directory, filename)
            fs_name = filename.split('_')[1]
            process_bonnie_log(input_file, fs_name, bonnie_output_file)
        if filename.startswith("iozone") and filename.endswith(".log"):
            input_file = os.path.join(directory, filename)
            fs_name = filename.split('_')[1]
            process_iozone_log(input_file, fs_name, iozone_output_file)

input_directory = './'
bonnie_output_file = './bonnie_processed.csv'
iozone_output_file = './iozone_processed.csv'

process_all_logs(input_directory, bonnie_output_file, iozone_output_file)
