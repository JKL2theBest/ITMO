#include "psrs.h"

double *splitters;
int *partition_sizes;

// Инициализация кольцевой очереди
void init_queue(CircularQueue *queue, int size) {
    queue->buffer = (double*)malloc(size * sizeof(double));
    if (!queue->buffer) {
        printf("Ошибка: Не удалось выделить память для кольцевой очереди\n");
        exit(1);
    }
    queue->head = 0;
    queue->tail = 0;
    queue->max_size = size;
    pthread_mutex_init(&queue->mutex, NULL);
    printf("Инициализация кольцевой очереди с размером %d...\n", size);
}

// Добавление элемента в кольцевую очередь
void enqueue(CircularQueue *queue, double value) {
    pthread_mutex_lock(&queue->mutex); 
    if ((queue->tail + 1) % queue->max_size != queue->head) {  // Проверка на заполненность
        queue->buffer[queue->tail] = value;
        queue->tail = (queue->tail + 1) % queue->max_size;
    } else {
        printf("Кольцевая очередь заполнена.\n");
    }
    pthread_mutex_unlock(&queue->mutex);  // Освобождение мьютекса после работы с очередью
}

// Функция сортировки
int compare(const void *a, const void *b) {
    if (*(double*)a < *(double*)b) return -1;
    if (*(double*)a > *(double*)b) return 1;
    return 0;
}

// Локальная сортировка для каждого потока
void *local_sort(void *arg) {
    ThreadData *data = (ThreadData*)arg;
    qsort(data->array, data->size, sizeof(double), compare);  // Сортировка каждого подмассива
    printf("Поток %d: Сортировка %d элементов...\nОтсортированный подмассив: \n", data->id, data->size);
    for (int i = 0; i < data->size; i++) {
        printf("%.15g ", data->array[i]);  // Печать отсортированного подмассива
    }
    printf("\n");
    return NULL;
}

// Чтение данных из файла и заполнение кольцевой очереди
int read_data_from_file(const char *file_path, CircularQueue *queue) {
    FILE *file = fopen(file_path, "r");
    if (!file) {
        printf("Ошибка: Не удалось открыть файл %s\n", file_path);
        return 0;
    }

    double *temp_array = NULL;
    int capacity = 100;
    int count = 0;

    temp_array = malloc(capacity * sizeof(double));
    if (!temp_array) {
        printf("Ошибка: не удалось выделить память\n");
        fclose(file);
        return 0;
    }

    char line[256];
    while (fgets(line, sizeof(line), file)) {
        // Пропускаем строки, содержащие только пробелы или символы новой строки
        int only_whitespace = 1;
        for (char *p = line; *p != '\0'; ++p) {
            if (!isspace((unsigned char)*p)) {
                only_whitespace = 0;
                break;
            }
        }
        if (only_whitespace) {
            continue;
        }

        char *token = strtok(line, " \n\r\t");
        while (token) {
            char *endptr;
            double val = strtod(token, &endptr);

            // Проверка на корректность числа
            if (*endptr != '\0') {
                printf("Ошибка: Некорректное значение \"%s\" в файле\n", token);
                free(temp_array);
                fclose(file);
                return 0;
            }
            if (isnan(val) || isinf(val)) {
                printf("Ошибка: Значение \"%s\" в файле недопустимо\n", token);
                free(temp_array);
                fclose(file);
                return 0;
            }

            // Расширение массива при необходимости
            if (count >= capacity) {
                capacity *= 2;
                double *new_array = realloc(temp_array, capacity * sizeof(double));
                if (!new_array) {
                    printf("Ошибка: не удалось перераспределить память\n");
                    free(temp_array);
                    fclose(file);
                    return 0;
                }
                temp_array = new_array;
            }

            temp_array[count++] = val;
            token = strtok(NULL, " \n\r\t");
        }
    }

    if (count == 0) {
        printf("Ошибка: В файле нет чисел для сортировки.\n");
        free(temp_array);
        fclose(file);
        return 0;
    }

    fclose(file);

    init_queue(queue, count);
    for (int i = 0; i < count; i++) {
        enqueue(queue, temp_array[i]);
    }

    free(temp_array);
    return 1;
}

// Функция для выбора выборок для разделителей
void choose_samples(ThreadData *thread_data, int p, int sample_count, double *samples) {
    for (int i = 0; i < p; ++i) {
        int size = thread_data[i].size;
        // Процесс выбора samples[i * sample_count + j] на основе разбиения подмассива
        for (int j = 0; j < sample_count; ++j) {
            int index = (j + 1) * size / (sample_count + 1);  // Выбор индекса для выборки
            samples[i * sample_count + j] = thread_data[i].array[index];
        }
    }
}

// Функция выбора разделителей (splitters)
void choose_splitters(double *samples, int total_samples, int p) {
    qsort(samples, total_samples, sizeof(double), compare);  // Сортировка выборок
    for (int i = 0; i < p - 1; ++i) {
        splitters[i] = samples[(i + 1) * total_samples / p];  // Выбор разделителей
    }
}

// Функция перераспределения данных по корзинам на основе разделителей
void redistribute_data(int p, double *numbers, int n, double **buckets, int *bucket_sizes) {
    int *offsets = (int*)calloc(p, sizeof(int));  // Массив для отслеживания индексов в корзинах
    memset(bucket_sizes, 0, p * sizeof(int));  // Инициализация всех размеров корзин в 0

    // Преобразование чисел в корзины на основе разделителей
    for (int i = 0; i < n; ++i) {
        double value = numbers[i];
        int target = 0;
        // Определение корзины, в которую попадет элемент
        while (target < p - 1 && value > splitters[target]) target++;
        bucket_sizes[target]++;  // Увеличение размера корзины
    }

    // Выделение памяти для каждой корзины
    for (int i = 0; i < p; ++i)
        buckets[i] = (double*)malloc(bucket_sizes[i] * sizeof(double));

    // Размещение чисел в соответствующих корзинах
    for (int i = 0; i < n; ++i) {
        double value = numbers[i];
        int target = 0;
        // Поиск корзины для текущего элемента
        while (target < p - 1 && value > splitters[target]) target++;
        buckets[target][offsets[target]++] = value;  // Размещение в корзине
    }

    free(offsets);  // Освобождение памяти для индексов
}

// Финальная сортировка для каждого потока
void *final_sort(void *arg) {
    ThreadData *data = (ThreadData*)arg;
    qsort(data->array, data->size, sizeof(double), compare);  // Финальная сортировка
    return NULL;
}

// Инициализация потоков и данных
int initialize_threads(int p, pthread_t **threads, ThreadData **thread_data) {
    *threads = malloc(p * sizeof(pthread_t));  // Выделение памяти для потоков
    *thread_data = malloc(p * sizeof(ThreadData));  // Выделение памяти для данных потоков
    if (!(*threads) || !(*thread_data)) {
        printf("Ошибка: Не удалось выделить память для потоков\n");
        free(*threads);
        free(*thread_data);
        return 0;
    }
    return 1;
}

// Запись отсортированных данных в файл
void write_result_to_file(const char *output_file, double *result, int n) {
    FILE *file = fopen(output_file, "w");
    if (!file) {
        printf("Ошибка: Не удалось открыть выходной файл %s\n", output_file);
        return;
    }
    for (int i = 0; i < n; i++)
        fprintf(file, "%.15g ", result[i]);  // Запись каждого числа в файл
    fclose(file);
    printf("Запись в файл \"%s\" завершена.\n", output_file);
}

// Функция вывода содержимого кольцевой очереди
void print_queue(CircularQueue *queue) {
    printf("Содержимое кольцевой очереди: \n");
    int current = queue->head;
    // Перебор элементов в кольцевой очереди и вывод их на экран
    while (current != queue->tail) {
        printf("%.15g ", queue->buffer[current]);
        current = (current + 1) % queue->max_size;
    }
    printf("\n");
}

// Освобождение выделенной памяти
void free_memory(double *numbers, double *result, pthread_t *threads, ThreadData *thread_data) {
    free(numbers);
    free(result);
    free(threads);
    free(thread_data);
}
