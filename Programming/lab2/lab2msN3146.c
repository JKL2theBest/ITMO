// Суханкулиев Мухаммет N3146, 341992, ПРОГР-1.2; Вариант 5-12
// Способ представления матрицы - VLA
// Задание: Осуществить в матрице циклический сдвиг на Т элементов так, как показано на Рис. 1а. (змейкой по горизонтали)
// Тип элементов: long double

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include "functions.h"

int main(int argc, char *argv[]) {
    // Проверка запуска с переменной среды, включающей отладочный вывод.
    // Пример запуска с установкой переменной LAB2DEBUG в 1:
    // $ LAB2DEBUG=1 ./lab2msN3146 6 9
    char *DEBUG = getenv("LAB2DEBUG");
    if (DEBUG) {
        fprintf(stderr, "Включен вывод отладочных сообщений\n");
    }

    if ((argc != 4 || strcmp(argv[1], "-m")) && (argc != 3)) {
        fprintf(stderr, "Usage: %s [-m] число_строк число_столбцов\n", argv[0]);
        return EXIT_FAILURE; // По сути мне не обязательно добавлять дополнительные выводы ошибок при разных входных данных
    }                        // т.к. при вводе некорректного значения и так срабатывает этот if
                             // чтобы добавить такие выводы нужно изменить этот исходный код. делать я этого не буду =)
    
    //
    // Тут может быть ваш код. В этом файле Вы можете поменять все, что угодно.
    // Главное - чтобы потом все правильно работало ;-)

    int rows, columns, t;
    // Проверка входных данных
    if (argc == 3) {
        // Если введено 3 элемента, то проверить, что второй и третий - положительные числа.
        rows = atoi(argv[1]);
        columns = atoi(argv[2]);
        if (rows > 0 && columns > 0) {
            // Создание матрицы
            long double **matrix = malloc(rows * sizeof(long double *));
            for (int i = 0; i < rows; i++) {
                matrix[i] = malloc(columns * sizeof(long double));
            }
            // Заполнение матрицы случайными long double значениями
            srand(time(NULL));
            for (int i = 0; i < rows; i++) {
                for (int j = 0; j < columns; j++) {
                    matrix[i][j] = getRandomLD(-255, 255); // числа в диапазоне от 1е-37 до 1е+37 не помещаются на экране 
                }
            }
            // Вывод
            if (DEBUG) printf("Генерация случайных long double чисел... (в диапазоне от -255 до 255)\n");
            printf("Исходная матрица:\n");
            print_matrix(matrix, rows, columns);
            // Получить значение Т
            t = get_t(rows,columns,DEBUG);
            if (t == 69) { // Вывод ошибки если функция возвратила 69
                return EXIT_FAILURE;
            }

            // Преобразование матрицы
            shift(matrix, rows, columns, t);

            // Вывод матрицы на экран
            printf("Результат:\n");
            print_matrix(matrix, rows, columns);
            // Освобождение памяти
            for (int i = 0; i < rows; i++) {
                free(matrix[i]);
            }
            free(matrix);
        } else {
            // Вывести сообщение об ошибке.
            fprintf(stderr, "Введи 2 int числа! ('%s' и '%s' не подходят)\n", argv[1],argv[2]);
            return EXIT_FAILURE;
        }
    } else if (argc == 4) {
        // Если введено 4 элемента, то проверить, что второй элемент - строка "-m", а третий и четвертый - положительные числа.
        if (strcmp(argv[1], "-m") == 0) {
            rows = atoi(argv[2]);
            columns = atoi(argv[3]);
            if (rows > 0 && columns > 0) {
                // Создание матрицы
                long double **matrix = malloc(rows * sizeof(long double *));
                for (int i = 0; i < rows; i++) {
                    matrix[i] = malloc(columns * sizeof(long double));
                }
                // Заполнение матрицы
                printf("Введите элементы (long double) матрицы через пробел (и/или Enter): ");
                for (int i = 0; i < rows; i++) {
                    for (int j = 0; j < columns; j++) {
                        // Проверка на корректность ввода
                        if (scanf("%Lf", &matrix[i][j]) != 1) {
                            // Вывод ошибки
                            printf("Ошибка ввода элемента матрицы [%d,%d].\n", i+1, j+1);
                            return EXIT_FAILURE;
                        }
                    }
                }
                // Вывод
                printf("Исходная матрица:\n");
                print_matrix(matrix, rows, columns);
                // Получить значение Т
                t = get_t(rows,columns,DEBUG);
                if (t == 69) {
                    return EXIT_FAILURE;
                }

                // Преобразование
                shift(matrix, rows, columns, t);

                // Вывод матрицы на экран
                printf("Результат:\n");
                print_matrix(matrix, rows, columns);
                // Освобождение памяти
                for (int i = 0; i < rows; i++) {
                    free(matrix[i]);
                }
                free(matrix);
            } else {
                // Вывести сообщение об ошибке.
                fprintf(stderr, "Даже вместе с '-m' нужно ввести 2 int числа!\n");
                return EXIT_FAILURE;
            }
        }
    }

    return EXIT_SUCCESS;
}
