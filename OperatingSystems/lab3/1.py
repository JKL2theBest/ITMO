with open('results_8_reps.txt', 'r') as file:
    lines = file.readlines()

with open('results_kflops.csv', 'w') as csv_file:
    csv_file.write("No,KFLOPS\n") 

    for i, line in enumerate(lines, start=1):
        parts = line.split()
        if len(parts) > 1:  
            kflops = parts[-1]  
            csv_file.write(f"{i},{kflops}\n")

print("Файл успешно преобразован в CSV.")
