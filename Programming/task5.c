// Заготовка программы. Сохраните в файле main.c
// ID: 76464257494b5548  Эту строку не удалять!

// Сама функция
#include <stddef.h>

int my_memcmp(const void *s1, const void *s2, size_t n) {
    const unsigned char *p1 = s1, *p2 = s2;

    while (n-- > 0) {
        if (*p1 != *p2) {
            return (*p1 > *p2) ? 1 : -1;
        }
        p1++;
        p2++;
    }

    return 0;
}

//Пример выполнения
#include <stdio.h>

int main() {
    //Сравнение строк
    const char *str1 = "Hello";
    const char *str2 = "World";

    int result = my_memcmp(str1, str2, 5);

    if (result < 0) {
        printf("Строка 1 меньше строки 2\n");
    } else if (result > 0) {
        printf("Строка 1 больше строки 2\n");
    } else {
        printf("Строки идентичны\n");
    }

    return 0;
}
