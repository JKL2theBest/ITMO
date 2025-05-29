#include "psrs.h"

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Использование: %s <путь к файлу> <количество потоков>\n", argv[0]);
        return 1;
    }

    const char *file_path = argv[1];
    int p = atoi(argv[2]);

    if (p <= 1 || p > 6) {
        printf("Ошибка: Неверное количество потоков. Должно быть больше 1 и не больше 6.\n");
        return 1;
    }

    CircularQueue queue;
    if (!read_data_from_file(file_path, &queue)) return 1;

    // Выводим содержимое кольцевой очереди после её заполнения
    print_queue(&queue);

    double *numbers = queue.buffer;
    int n = (queue.tail - queue.head + queue.max_size) % queue.max_size;

    if (p > n) {
        printf("Ошибка: Количество потоков не может превышать количество элементов.\n");
        free(queue.buffer);
        return 1;
    }

    double *result = malloc(n * sizeof(double));
    if (!result) {
        printf("Ошибка: Не удалось выделить память для результата\n");
        free(queue.buffer);
        return 1;
    }

    pthread_t *threads;
    ThreadData *thread_data;
    if (!initialize_threads(p, &threads, &thread_data)) {
        free(queue.buffer);
        free(result);
        return 1;
    }

    int base_size = n / p, remainder = n % p, offset = 0;
    // Разделение массива на части для каждого потока
    for (int i = 0; i < p; ++i) {
        int local_size = base_size + (i < remainder);
        thread_data[i] = (ThreadData){ .array = numbers + offset, .size = local_size, .id = i, .queue = &queue };
        offset += local_size;
        pthread_create(&threads[i], NULL, local_sort, &thread_data[i]);  // Создание потоков для локальной сортировки
    }
    for (int i = 0; i < p; ++i) pthread_join(threads[i], NULL);  // Ожидание завершения всех потоков

    // Выборка для разделителей
    int sample_count = p - 1;
    double *samples = malloc(p * sample_count * sizeof(double));
    choose_samples(thread_data, p, sample_count, samples);

    // Выбор разделителей
    splitters = malloc((p - 1) * sizeof(double));
    choose_splitters(samples, p * sample_count, p);
    free(samples);

    // Перераспределение данных по корзинам
    double **buckets = malloc(p * sizeof(double*));
    partition_sizes = calloc(p, sizeof(int));
    redistribute_data(p, numbers, n, buckets, partition_sizes);

    // Финальная сортировка для каждого потока
    for (int i = 0; i < p; ++i) {
        thread_data[i] = (ThreadData){ .array = buckets[i], .size = partition_sizes[i], .id = i };
        pthread_create(&threads[i], NULL, final_sort, &thread_data[i]);
    }
    for (int i = 0; i < p; ++i) pthread_join(threads[i], NULL);

    printf("Сортировка для каждого потока выполнена. Объединение результатов...\n");

    // Объединение результатов из всех корзин
    offset = 0;
    for (int i = 0; i < p; ++i) {
        memcpy(result + offset, buckets[i], partition_sizes[i] * sizeof(double));
        offset += partition_sizes[i];
        free(buckets[i]);
    }

    // Запись результата в файл
    write_result_to_file("sorted_result.txt", result, n);
    free_memory(numbers, result, threads, thread_data);
    free(splitters);
    free(partition_sizes);
    free(buckets);

    return 0;
}
