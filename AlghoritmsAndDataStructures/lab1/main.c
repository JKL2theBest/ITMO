#include "psrs.h"

// Главная функция
int main(int argc, char *argv[]) {
    if (argc < 4) {
        printf("Использование: %s <путь к файлу> <количество потоков> <тип массива: static/dynamic>\n", argv[0]);
        return 1;
    }
    const char *file_path = argv[1];
    int p = atoi(argv[2]);
    if (p <= 1 || p > 6 ) {
        printf("Ошибка: Неверное количество потоков. Должно быть больше 1 и не больше 6.\n");
        return 1;
    }
    const char *array_type = argv[3];
    // Переменные для данных
    double *numbers = NULL;
    int n = 0;
    if (!read_data_from_file(file_path, &numbers, &n, array_type)) {
        printf("Ошибка при чтении файла\n");
        return 1;
    }
    if (p > n) {
        printf("Ошибка: Количество потоков не может превышать количество элементов.\n");
        free(numbers);
        return 1;
    }
    // Резервирование памяти для результата
    double *result = (double*)malloc(n * sizeof(double));
    if (!result) {
        printf("Ошибка: Не удалось выделить память для результата\n");
        free(numbers);
        return 1;
    }
    // Массивы для потоков
    pthread_t *threads;
    ThreadData *thread_data;
    if (!initialize_threads(p, &threads, &thread_data)) {
        printf("Ошибка: Не удалось создать потоки threads\n");
        free(numbers);
        free(result);
        return 1;
    }
    // Разделение данных на части для каждого потока
    int base_size = n / p;
    int remainder = n % p;
    int offset = 0;
    for (int i = 0; i < p; ++i) {
        int local_size = base_size + (i < remainder ? 1 : 0);
        thread_data[i].array = numbers + offset;
        thread_data[i].size = local_size;
        thread_data[i].id = i;
        offset += local_size;
        pthread_create(&threads[i], NULL, local_sort, &thread_data[i]);
    }
    // Ожидание завершения всех потоков
    for (int i = 0; i < p; ++i) {
        pthread_join(threads[i], NULL);
    }
    // Создание подмассивов для слияния
    double *sub_arrays[p];
    int sizes[p];
    offset = 0;
    for (int i = 0; i < p; ++i) {
        sub_arrays[i] = numbers + offset;
        sizes[i] = thread_data[i].size;
        offset += sizes[i];
    }
    // Выбор разделителей
    double *splitters = (double*)malloc((p - 1) * sizeof(double));
    if (!splitters) {
        printf("Ошибка: Не удалось выделить память для разделителей\n");
        free_memory(numbers, result, NULL, NULL, threads, thread_data, array_type);
        return 1;
    }
    choose_splitters(sub_arrays, sizes, p, splitters);
    // Перераспределение данных
    double *new_numbers = (double*)malloc(n * sizeof(double));
    if (!new_numbers) {
        printf("Ошибка: Не удалось выделить память для new_numbers\n");
        free_memory(numbers, result, splitters, NULL, threads, thread_data, array_type);
        return 1;
    }
    redistribute_data(numbers, splitters, new_numbers, n, p);
    // Многопутевое слияние
    p_way_merge(sub_arrays, sizes, p, result);
    // Запись результата в файл
    write_result_to_file("sorted_result.txt", result, n);
    // Освобождение памяти
    free_memory(numbers, result, splitters, new_numbers, threads, thread_data, array_type);
    return 0;
}
