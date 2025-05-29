#include "headers.h"

double* splitters;
double** sub_arrays;
int* sub_sizes;
volatile sig_atomic_t exit_flag = 0;

// Обработчик сигнала SIGINT
void handle_sigint(int sig) {
    (void)sig;
    exit_flag = 1;
}

int main(int argc, char* argv[]) {
    signal(SIGINT, handle_sigint);
    if (argc != 3) {
        printf("Использование: %s <входной_файл> <кол-во_потоков>\n", argv[0]);
        return 1;
    }
    const char* filename = argv[1];
    int p = atoi(argv[2]);
    if (p < 2 || p > 6) {
        printf("Ошибка: количество потоков должно быть числом больше 1 и не больше 6.\n");
        return 1;
    }
    Queue* queue = read_data(filename);
    if (!queue) {
        return 1;
    }
    // Подсчитываем количество элементов в очереди
    int n = 0;
    QueueNode* node = queue->front;
    while (node != NULL) {
        n++;
        node = node->next;
    }
    // Выделяем память для массива в зависимости от количества элементов
    double* buffer = malloc(n * sizeof(double));
    if (!buffer) {
        fprintf(stderr, "Ошибка выделения памяти для массива.\n");
        freeQueue(queue);
        return 1;
    }
    // Заполняем массив данными из очереди
    int index = 0;
    while (!isEmpty(queue)) {
        QueueNode* node = dequeue(queue);
        buffer[index++] = *node->array;
        free(node->array);
        free(node);
    }
    printf("Прочитано %d чисел из файла.\n", n);
    // Проверки на корректность данных
    if (n == 0) {
        fprintf(stderr, "Ошибка: файл не содержит double числа.\n");
        free(buffer);
        return 1;
    }
    if (p > n) {
        printf("Количество потоков не может быть больше количества сортируемых элементов\n");
        free(buffer);
        return 1;
    }
    printf("PSRS-сортировка с использованием %d потоков...\n\n", p);
    printf("[Шаг 1] Исходный массив из %d элементов будет разделён между %d потоками.\n", n, p);
    pthread_t* threads = malloc(p * sizeof(pthread_t));
    ThreadData* tdata = malloc(p * sizeof(ThreadData));
    sub_arrays = malloc(p * sizeof(double*));
    sub_sizes = malloc(p * sizeof(int));
    printf("[Шаг 2] Локальная сортировка на каждом потоке...\n");
    int base = n / p, rem = n % p, offset = 0;
    for (int i = 0; i < p; ++i) {
        int size = base + (i < rem);     // Размер подмассива с учётом остатка
        sub_arrays[i] = buffer + offset; // Указатель на начало подмассива
        sub_sizes[i] = size;
        tdata[i] = (ThreadData){ sub_arrays[i], size, i };
        // Поток для локальной сортировки
        pthread_create(&threads[i], NULL, local_sort, &tdata[i]);
        offset += size;
    }
    // Ожидание завершения всех потоков
    for (int i = 0; i < p; ++i) pthread_join(threads[i], NULL);
    printf("[Шаг 3] Создание вспомогательного массива сэмплов (выборок) из локально отсортированных фрагментов...\n");
    double* samples = malloc(p * p * sizeof(double));
    choose_samples(tdata, p, samples);
    splitters = malloc((p - 1) * sizeof(double));
    choose_splitters(samples, p * p, p);
    free(samples);
    printf("[Шаг 6] Разбиение данных в каждом потоке согласно разделителям...\n");
    redistribute(p);
    printf("[Шаг 7] Объединение групп и сортировка внутри потоков (многопутевое слияние)...\n");
    // Запуск многопутевого слияния
    for (int i = 0; i < p; ++i) {
        tdata[i].array = sub_arrays[i];
        tdata[i].size = sub_sizes[i];
        pthread_create(&threads[i], NULL, merge_sort, &tdata[i]);
    }
    for (int i = 0; i < p; ++i) pthread_join(threads[i], NULL);
    // Объединение отсортированных подмассивов в итоговый результат
    double* result = malloc(n * sizeof(double));
    offset = 0;
    for (int i = 0; i < p; ++i) {
        memcpy(result + offset, sub_arrays[i], sub_sizes[i] * sizeof(double));
        offset += sub_sizes[i];
    }
    printf("\nОтсортированный массив:\n");
    for (int i = 0; i < n; ++i) printf("%.15g ", result[i]);
    printf("\n\n");
    write_to_file("sorted_result.txt", result, n);
    boyer_moore(result, n);
    for (int i = 0; i < p; ++i)
        free(sub_arrays[i]);
    freeQueue(queue);
    free(sub_arrays);
    free(sub_sizes);
    free(splitters);
    free(threads);
    free(tdata);
    free(result);
    free(buffer);
    return 0;
}