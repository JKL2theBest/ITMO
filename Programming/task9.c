// Суханкулиев Мухаммет, гр. N3146

#include <stdlib.h>
#include <stdio.h>
#include <time.h>

// Структура S
typedef struct S {
    short x;
    float y;
    char z;
} S;

// TODO: Реализовать функцию init_array(). См. вызов ниже. Подумайте, какой должен быть заголовок.
void init_array(S *arr, size_t arr_size) {
    srand(time(NULL));
    for (size_t i = 0; i < arr_size; i++) {
        arr[i].x = rand() % 100;
        arr[i].y = (float)(rand() % 10000) / 100.0f;
        arr[i].z = 'A' + (rand() % 26);
    }
}

// TODO: Реализовать функцию print_array(). См. вызов ниже. Подумайте, какой должен быть заголовок.
void print_array(S *arr, size_t arr_size) {
    for (size_t i = 0; i < arr_size; i++) {
        printf("%d, %.2f, %c\n", arr[i].x, arr[i].y, arr[i].z);
    }
}

int compare(const void *a, const void *b) {
    S *s1 = (S *)a;
    S *s2 = (S *)b;
    return (int)(s2->y) - (int)(s1->y);
}
// TODO: Реализовать функцию sort_array(). См. вызов ниже. Подумайте, какой должен быть заголовок.
void sort_array(S *arr, size_t arr_size) {
    qsort(arr, arr_size, sizeof(S), compare);
}

int main(int argc, char *argv[]) {
    // 1. TODO: Проверить аргументы командной строки и получить размер массива.
    if (argc != 2) {
        printf("Использование: %s <array size>\n", argv[0]);
        return 1;
    }
    size_t arr_size = atoi(argv[1]);

    // 2. TODO: Выделить память из кучи для массива. Указатель arr должен
    // указывать на начало массива.
    S *arr = malloc(arr_size * sizeof(S));

    // 3. Заполнить массив структур случайными значениями
    init_array(arr, arr_size);
    // 4. Вывести массив на экран
    printf("Массив структур со случайными значениями:\n");
    // 5. Отсортировать массив структур по убыванию величины целой части поля y.
    print_array(arr, arr_size);
    sort_array(arr, arr_size);
    // 6. Вывести отсортированный массив на экран
    printf("\nОтсортированный массив:\n");
    print_array(arr, arr_size);

    free(arr);
    return 0;
}
