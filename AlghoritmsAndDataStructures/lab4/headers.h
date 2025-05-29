#ifndef HEADERS_H
#define HEADERS_H

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <string.h>
#include <math.h>
#include <signal.h>

#define MAX_INPUT 64  // Максимальная длина вводимой строки
// Макросы для цветов в красно-черном дереве
#define RED 1
#define BLACK 0

// --- Структуры данных ---
// Структура для передачи данных в потоке
typedef struct {
    double* array;
    int size;
    int id;
} ThreadData;

// Узел дека
typedef struct DequeNode {
    double* array;
    int size;
    struct DequeNode* prev;
    struct DequeNode* next;
} DequeNode;

// Структура дека
typedef struct Deque {
    DequeNode* front;
    DequeNode* rear;
    int size;
} Deque;

// Узел красно-черного дерева
typedef struct RBNode {
    double key;
    int color;
    struct RBNode* left;
    struct RBNode* right;
    struct RBNode* parent;
} RBNode;

// Красно-черное дерево
typedef struct RBTree {
    RBNode* root;
} RBTree;

typedef struct { 
    int l, r; // Пара индексов для сегмента
} Segment;

// --- Глобальные переменные ---
extern double* splitters;          // Разделители
extern double** sub_arrays;        // Подмассивы
extern int* sub_sizes;             // Размеры подмассивов
extern volatile sig_atomic_t exit_flag;

// --- Функции работы с деком ---
Deque* createDeque();
void insertFront(Deque* dq, double* array, int size);
void insertRear(Deque* dq, double* array, int size);
DequeNode* deleteFront(Deque* dq);
DequeNode* deleteRear(Deque* dq);
int isEmptyDeque(Deque* dq);
void freeDeque(Deque* dq);

void handle_sigint(int sig); // Обработчик сигнала SIGINT (Ctrl+C)

// --- Функции сортировки и распределения данных ---
int compare(const void* a, const void* b);
void* local_sort(void* arg);
void choose_samples(ThreadData* data, int p, double* samples);
void choose_splitters(double* samples, int total_samples, int p);
void redistribute(int p);
void* merge_sort(void* arg);

void write_to_file(const char* filename, double* array, int size); // Запись в файл

// --- Функции работы с красно-черным деревом ---
int* makeInsertionOrder(int n, int* outLen);    // Построение порядка вставки
RBTree* createRBTree();                         // Создание красно-черного дерева
void rbInsert(RBTree* tree, double key);        // Вставка в красно-черное дерево
RBNode* rbSearch(RBTree* tree, double key);     // Поиск узла по ключу
void freeRBTree(RBTree* tree);                  // Освобождение памяти для дерева
int rbGetColor(RBNode* node);                   // Получение цвета узла
void rbSetColor(RBNode* node, int color);       // Установка цвета узла
void leftRotate(RBTree* tree, RBNode* x);       // Левый поворот
void rightRotate(RBTree* tree, RBNode* y);      // Правый поворот
void rbFixInsert(RBTree* tree, RBNode* node);   // Исправление дерева после вставки
int rbGetRank(RBTree* tree, double key);        // Получение ранга узла по ключу
void exportRBTreeToDot(RBTree* tree, const char* filename);  // Экспорт в DOT формат

// --- Функции для работы с файлами данных ---
Deque* read_data(const char* filename);  // Чтение данных из файла

int main(int argc, char* argv[]);

#endif // HEADERS_H
