#ifndef HEADERS_H
#define HEADERS_H

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <string.h>
#include <math.h>
#include <ctype.h>
#include <signal.h>

#define MAX_INPUT 64  // Максимальная длина вводимой строки

// Структура данных для потока
typedef struct {
    double* array;
    int size;
    int id;
} ThreadData;

// Узел очереди
typedef struct QueueNode {
    double* array;
    int size;
    struct QueueNode* next;
} QueueNode;

// Очередь на основе связного списка
typedef struct Queue {
    QueueNode* front;  // Указатель на начало
    QueueNode* rear;   // Указатель на конец
} Queue;

// Глобальные переменные
extern double* splitters;
extern double** sub_arrays;
extern int* sub_sizes;
extern volatile sig_atomic_t exit_flag; // Флаг завершения (SIGINT)

// Очередь: функции создания, работы и очистки
Queue* createQueue();
void enqueue(Queue* q, double* array, int size);
QueueNode* dequeue(Queue* q);
int isEmpty(Queue* q);
void freeQueue(Queue* q);

// Обработчик сигнала SIGINT (Ctrl+C)
void handle_sigint(int sig);

// Функции сортировки и распределения
int compare(const void* a, const void* b);
void* local_sort(void* arg);
void choose_samples(ThreadData* data, int p, double* samples);
void choose_splitters(double* samples, int total_samples, int p);
void redistribute(int p);      // Перераспределение элементов по разделителям
void* merge_sort(void* arg);   // Финальное многопутевое слияние

// Алгоритм Бойера-Мура для поиска строки (значение double преобразуется в строку)
void preprocess_bad(const char* pat, int m, int badchar[256]);  // Эвристика стоп-символа
void preprocess_good(const char* pat, int m, int* shift);       // Эвристика совпавшего суффикса
void boyer_moore(double* array, int size);                      // Обёртка для поиска значения double в массиве через Бойера-Мура по строковому представлению
int boyer_moore_string(const char* text, const char* pattern);  // Основной алгоритм Бойера-Мура для поиска шаблона в тексте

// Работа с файлами и вводом/выводом
Queue* read_data(const char* filename);
void write_to_file(const char* filename, double* array, int size);

int main(int argc, char* argv[]);

#endif // HEADERS_H