#include "headers.h"

// Функция для создания новой очереди (инициализация пустой очереди)
Queue* createQueue() {
    Queue* newQueue = (Queue*)malloc(sizeof(Queue));  
    newQueue->front = newQueue->rear = NULL;  
    return newQueue;
}

// Функция для добавления элемента в очередь (в конец очереди)
void enqueue(Queue* q, double* array, int size) {
    QueueNode* newNode = (QueueNode*)malloc(sizeof(QueueNode));  
    newNode->array = array;  
    newNode->size = size;  
    newNode->next = NULL;  
    if (q->rear == NULL) {  
        q->front = q->rear = newNode;  
        return;
    }
    q->rear->next = newNode;  
    q->rear = newNode;  
}

// Функция для извлечения элемента из очереди (удаление первого элемента)
QueueNode* dequeue(Queue* q) {
    if (q->front == NULL)  
        return NULL;
    QueueNode* temp = q->front;  
    q->front = q->front->next;  
    if (q->front == NULL)  
        q->rear = NULL;
    return temp;  
}

// Функция для проверки, пуста ли очередь
int isEmpty(Queue* q) {
    return q->front == NULL;  
}

// Освобождение памяти, занятой очередью и её элементами
void freeQueue(Queue* q) {
    while (!isEmpty(q)) {  
        QueueNode* node = dequeue(q);  
        free(node->array);  
        free(node);  
    }
    free(q);  
}

// Функция для чтения данных из файла в очередь
Queue* read_data(const char* filename) {
    FILE* f = fopen(filename, "r");  
    if (!f) {
        perror("Ошибка открытия файла");
        return NULL;  
    }
    Queue* queue = createQueue();  
    char temp[256]; // Буфер для чтения строки
    char* endptr;   // Указатель для проверки корректности преобразования строки в число
    while (fscanf(f, "%s", temp) == 1) {  
        double value = strtod(temp, &endptr);  
        // Проверка: корректный double, нет мусора в строке, значение конечно
        if (endptr == temp || *endptr != '\0' || !isfinite(value)) {
            fprintf(stderr, "Ошибка: недопустимое значение \"%s\" в файле.\n", temp);
            fclose(f);  
            return NULL;  
        }
        double* valueArray = (double*)malloc(sizeof(double));  
        *valueArray = value;  
        enqueue(queue, valueArray, 1);  
    }
    fclose(f);  
    return queue;  
}

// Функция для записи данных в файл
void write_to_file(const char* filename, double* array, int size) {
    FILE* f = fopen(filename, "w");  
    if (!f) {
        perror("Ошибка создания файла для записи");
        return;  
    }
    for (int i = 0; i < size; ++i)  
        fprintf(f, "%.15g ", array[i]);
    fprintf(f, "\n");  
    fclose(f);  
    printf("Результат сортировки записан в '%s'\n", filename);  
}