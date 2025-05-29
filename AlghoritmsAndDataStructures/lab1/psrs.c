#include "psrs.h"

// Функция сортировки
int compare(const void *a, const void *b) {
    if (*(double*)a < *(double*)b) return -1;
    if (*(double*)a > *(double*)b) return 1;
    return 0;
}

// Локальная сортировка для каждого потока
void *local_sort(void *arg) {
    ThreadData *data = (ThreadData*)arg;
    qsort(data->array, data->size, sizeof(double), compare);
    printf("Поток %d: Сортировка %d элементов...\nОтсортированный подмассив: \n", data->id, data->size);
    for (int i = 0; i < data->size; ++i) {
        printf("%.15g ", data->array[i]);
    }
    printf("\n");
    return NULL;
}

// Чтение данных из файла и заполнение массива
int read_data_from_file(const char *file_path, double **numbers, int *n, const char *array_type) {
    FILE *file = fopen(file_path, "r");
    if (!file) {
        printf("Ошибка: Не удалось открыть файл %s\n", file_path);
        return 0;
    }
    double temp;
    *n = 0;
    // Считываем количество чисел в файле
    while (fscanf(file, "%lf", &temp) == 1) {
        (*n)++;
    }
    rewind(file);
    // Выбор типа массива
    if (strcmp(array_type, "static") == 0) {
        if (*n > MAX_NUMBERS) {
            printf("Предупреждение: Данные превышают MAX_NUMBERS. Переход к динамическому массиву.\n");
            *numbers = (double*)malloc(*n * sizeof(double));  // Динамическая память, если превышен лимит
        } else {
            static double static_numbers[MAX_NUMBERS];  // Статический массив
            *numbers = static_numbers;  // Указываем на начало статического массива
        }
    } else if (strcmp(array_type, "dynamic") == 0) {
        *numbers = (double*)malloc(*n * sizeof(double));  // Динамическая память
    } else {
        printf("Ошибка: Неверный тип массива. Используйте 'static' или 'dynamic'.\n");
        fclose(file);
        return 0;
    }
    if (!*numbers) {
        printf("Ошибка: Не удалось выделить память для чисел\n");
        fclose(file);
        return 0;
    }
    // Считываем данные из файла с проверкой на ошибки
    int valid_count = 0;
    char line[256];  // Буфер для строки
    while (fgets(line, sizeof(line), file)) {
        char *token = strtok(line, " \n\r\t");  // Разделяем строку на токены по пробелам и символам новой строки
        while (token) {
            // Проверка, что строка является корректным числом
            char *endptr;
            temp = strtod(token, &endptr);
            // Если strtod не смог преобразовать строку в число
            if (*endptr != '\0') {
                printf("Ошибка: Некорректное значение \"%s\" в файле\n", token);
                if (array_type && strcmp(array_type, "dynamic") == 0) {  // Освобождаем только динамически выделенную память
                    free(*numbers);
                }
                fclose(file);
                return 0;
            }
            // Проверка на NaN и Infinity
            if (isnan(temp) || isinf(temp)) {
                printf("Ошибка: Значение \"%s\" в файле недопустимо\n", token);
                if (array_type && strcmp(array_type, "dynamic") == 0) {  // Освобождаем только динамически выделенную память
                    free(*numbers);
                }
                fclose(file);
                return 0;
            }
            if (valid_count < *n) {
                (*numbers)[valid_count++] = temp;
            }
            token = strtok(NULL, " \n\r\t");  // Переход к следующему токену
        }
    }
    if (valid_count == 0) {
        printf("Ошибка: В файле нет чисел для сортировки.\n");
        if (array_type && strcmp(array_type, "dynamic") == 0) {  // Освобождаем только динамически выделенную память
            free(*numbers);
        }
        fclose(file);
        return 0;
    }
    fclose(file);
    return 1;
}

// Функция для выделения памяти для потоков и данных потока
int initialize_threads(int p, pthread_t **threads, ThreadData **thread_data) {
    *threads = (pthread_t*)malloc(p * sizeof(pthread_t));
    *thread_data = (ThreadData*)malloc(p * sizeof(ThreadData));
    if (!*threads || !*thread_data) {
        printf("Ошибка: Не удалось выделить память для потоков или данных потока\n");
        return 0;
    }
    return 1;
}

// Выбор регулярных образцов для разделителей
void choose_splitters(double **sub_arrays, int *sizes, int p, double *splitters) {
    printf("Формирование вспомогательного массива и выбор разделителей...\n");
    // Выделение памяти для выборки
    int sample_size = p - 1;
    double *sample = (double*)malloc(sample_size * sizeof(double));
    if (!sample) {
        printf("Ошибка: Не удалось выделить память для выборки\n");
        return;
    }
    int sample_index = 0;
    // Формирование выборки из подмассивов
    for (int i = 0; i < p; ++i) {
        int local_size = sizes[i];
        if (local_size > 0) {
            int step = (local_size > p) ? (local_size / p) : 1; // Защита от деления на 0
            for (int j = 1; j < p; ++j) {
                int index = j * step;
                if (index < local_size) {
                    // Убедиться, что индекс не выходит за пределы массива
                    if (sample_index < sample_size) {
                        sample[sample_index++] = sub_arrays[i][index];
                    } else {
                        break;
                    }
                }
            }
        }
    }
    // Сортировка выборки
    qsort(sample, sample_size, sizeof(double), compare);
    // Выбор разделителей из отсортированной выборки
    for (int i = 0; i < p - 1; ++i) {
        splitters[i] = sample[i];
    }
    free(sample);
}

// Перераспределение данных по разделителям
void redistribute_data(double *numbers, double *splitters, double *new_numbers, int n, int p) {
    int *counts = (int*)calloc(p, sizeof(int));
    if (!counts) {
        printf("Ошибка: Не удалось выделить память для counts\n");
        return;
    }
    memset(counts, 0, p * sizeof(int));
    printf("Перераспределение данных по разделителям...\n");
    for (int i = 0; i < n; ++i) {
        int j;
        for (j = 0; j < p - 1; ++j) {
            if (numbers[i] <= splitters[j]) {
                break;
            }
        }
        counts[j]++;
        new_numbers[counts[j] - 1] = numbers[i];  // Запись перераспределенного числа в new_numbers
    }
    free(counts);
}

// Многопутевое слияние отсортированных подмассивов
void p_way_merge(double **sub_arrays, int *sizes, int p, double *result) {
    printf("Многопутевое слияние отсортированных подмассивов...\n");
    int *indices = (int*)calloc(p, sizeof(int));
    if (!indices) {
        printf("Ошибка: Не удалось выделить память для индексов\n");
        return;
    }
    memset(indices, 0, p * sizeof(int));
    int total_size = 0;
    for (int i = 0; i < p; ++i) {
        total_size += sizes[i];
    }
    int current_index = 0;
    while (current_index < total_size) {
        double min_value = __DBL_MAX__;
        int min_index = -1;

        for (int j = 0; j < p; ++j) {
            if (indices[j] < sizes[j] && sub_arrays[j][indices[j]] < min_value) {
                min_value = sub_arrays[j][indices[j]];
                min_index = j;
            }
        }
        result[current_index] = min_value;
        indices[min_index]++;
        current_index++;
    }
    free(indices);
}

// Запись результата в файл
void write_result_to_file(const char *output_file, double *result, int n) {
    FILE *file = fopen(output_file, "w");
    if (!file) {
        printf("Ошибка: Не удалось открыть выходной файл %s\n", output_file);
        return;
    }
    for (int i = 0; i < n; i++) {
        fprintf(file, "%.15g ", result[i]);
    }
    fclose(file);
    printf("Запись в файл \"%s\" завершена.\n", output_file);
}

// Освобождение памяти
void free_memory(double *numbers, double *result, double *splitters, double *new_numbers, pthread_t *threads, ThreadData *thread_data, const char *array_type) {
    if (array_type && strcmp(array_type, "dynamic") == 0) {
        free(numbers);  // Освобождаем только если это динамический массив
    }
    free(result);
    free(splitters);
    free(new_numbers);
    free(threads);
    free(thread_data);
}
