// Заготовка программы. Сохраните в файле main.c
// ID: 49797c647c7c607d  Эту строку не удалять!

#include <stdio.h>

int main(int argc, char *argv[]) {
    // Проверяем, что передано правильное количество аргументов
    if (argc != 2) {
        fprintf(stderr, "Использование: %s <имя файла>\n", argv[0]);
        return 1;
    }

    // Открываем файл для чтения
    FILE *file = fopen(argv[1], "rb");
    if (!file) {
        perror("Ошибка при открытии файла");
        return 1;
    }

    unsigned int sum = 0;
    unsigned char byte;
    while (fread(&byte, sizeof(byte), 1, file)) {
        if (byte % 2 != 0) {
            sum += byte;
        }
    }

    if (ferror(file)) {
        perror("Ошибка при чтении файла");
        return 1;
    }

    printf("%u\n", sum);

    fclose(file);
    return 0;
}
