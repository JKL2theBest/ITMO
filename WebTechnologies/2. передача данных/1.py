file_path = "fake.png"

# PDF сигнатура версии 1.2 (%PDF-1.2) + пустое тело
pdf_signature = b"%PDF-1.2\n"

# Записываем "PDF" в файл с расширением .png
with open(file_path, "wb") as f:
    f.write(pdf_signature)

print(f"Файл {file_path} создан.")
