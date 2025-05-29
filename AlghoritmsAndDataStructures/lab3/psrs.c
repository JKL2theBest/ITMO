#include "headers.h"

// Сравнение двух элементов для qsort
int compare(const void* a, const void* b) {
    double da = *(double*)a;
    double db = *(double*)b;
    return (da > db) - (da < db);
}

// Локальная сортировка фрагмента данных
void* local_sort(void* arg) {
    ThreadData* data = (ThreadData*)arg;
    qsort(data->array, data->size, sizeof(double), compare);
    printf("Поток %d получил %d элементов. Отсортированный подмассив:\n", data->id, data->size);  
    for (int i = 0; i < data->size; ++i)
        printf("%.15g ", data->array[i]);
    printf("\n");
    return NULL;
}

// Выбор сэмплов: индексы определяются на основе размера данных
void choose_samples(ThreadData* data, int p, double* samples) {
    for (int i = 0; i < p; ++i) {
        for (int j = 0; j < p; ++j) {
            int idx = j * data[i].size / (p * p);
            samples[i * p + j] = data[i].array[idx];  // Запись сэмпла
        }
    }
}

// Выбор разделителей (splitters) для разбиения на группы
void choose_splitters(double* samples, int total_samples, int p) {
    printf("[Шаг 4] Сортировка вспомогательного массива выборок...\n");
    qsort(samples, total_samples, sizeof(double), compare);  // Сортировка сэмплов для выбора разделителей
    printf("[Шаг 5] Выбор разделителей для разбиения на группы...\n");
    for (int k = 1; k < p; ++k)
        splitters[k - 1] = samples[k * p + (p / 2) - 1];     // Используем медиану каждого блока
    printf("Выбранные разделители: ");
    for (int i = 0; i < p - 1; ++i)
        printf("%.15g ", splitters[i]);
    printf("\n");
}

// Распределение данных по очередям на основе разделителей
void redistribute(int p) {
    int* offsets = calloc(p * p, sizeof(int)); // Массив для отслеживания смещений данных
    int** sizes = malloc(p * sizeof(int*));    // Массив указателей на размеры для каждого потока
    for (int i = 0; i < p; ++i)
        sizes[i] = calloc(p, sizeof(int));
    // Создаём очередь для каждого потока
    Queue** queues = malloc(p * sizeof(Queue*));  
    for (int i = 0; i < p; ++i) {
        queues[i] = createQueue();
    }
    for (int i = 0; i < p; ++i) {
        for (int j = 0; j < sub_sizes[i]; ++j) {
            double val = sub_arrays[i][j];
            int g = 0;
            while (g < p - 1 && val > splitters[g]) g++; // Определяем в какую группу попадет элемент
            
            // Создаём подмассив для очереди
            double* part = malloc(sizeof(double));
            part[0] = val;
            enqueue(queues[g], part, 1);  // Добавляем элемент в соответствующую очередь
        }
    }
    // Воссоздание массивов из очередей
    for (int i = 0; i < p; ++i) {
        int total = 0;
        QueueNode* node = queues[i]->front;
        while (node != NULL) {
            total += node->size;
            node = node->next;
        }
        sub_arrays[i] = malloc(total * sizeof(double));
        sub_sizes[i] = total;
        int pos = 0;
        while ((node = dequeue(queues[i])) != NULL) {
            memcpy(sub_arrays[i] + pos, node->array, node->size * sizeof(double));
            pos += node->size;
            free(node->array);
            free(node);
        }
    }
    for (int i = 0; i < p; ++i) {
        free(queues[i]);
        free(sizes[i]);
    }
    free(queues);
    free(sizes);
    free(offsets);
}

// Финальная сортировка после объединения
void* merge_sort(void* arg) {
    ThreadData* data = (ThreadData*)arg;
    qsort(data->array, data->size, sizeof(double), compare);
    return NULL;
}