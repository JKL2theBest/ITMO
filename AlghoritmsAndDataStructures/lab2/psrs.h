#ifndef PSRS_H
#define PSRS_H

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <math.h>
#include <string.h>
#include <ctype.h>

typedef struct {
    double *buffer;           // Массив для хранения элементов кольцевой очереди
    int head;                 // Индекс головы очереди (где следующий элемент будет извлечен)
    int tail;                 // Индекс хвоста очереди (где следующий элемент будет добавлен)
    int max_size;             // Максимальный размер очереди
    pthread_mutex_t mutex;    // Мьютекс для синхронизации доступа к очереди
} CircularQueue;

typedef struct {
    double *array;            // Указатель на массив, который будет сортироваться
    int size;                 // Количество элементов в этом массиве
    int id;                   // Уникальный идентификатор потока
    CircularQueue *queue;     // Указатель на кольцевую очередь (если нужно)
} ThreadData;

// Глобальные переменные (определены в psrs.c)
extern double *splitters;
extern int *partition_sizes;

// Функции работы с очередью
void init_queue(CircularQueue *queue, int size);
void enqueue(CircularQueue *queue, double value);
void print_queue(CircularQueue *queue);

// Функции сортировки и PSRS
int compare(const void *a, const void *b);
void *local_sort(void *arg);
void *final_sort(void *arg);
void choose_samples(ThreadData *thread_data, int p, int sample_count, double *samples);
void choose_splitters(double *samples, int total_samples, int p);
void redistribute_data(int p, double *numbers, int n, double **buckets, int *bucket_sizes);

// Работа с потоками
int initialize_threads(int p, pthread_t **threads, ThreadData **thread_data);

// Работа с файлами
int read_data_from_file(const char *file_path, CircularQueue *queue);
void write_result_to_file(const char *output_file, double *result, int n);

// Очистка памяти
void free_memory(double *numbers, double *result, pthread_t *threads, ThreadData *thread_data);

#endif // PSRS_H
