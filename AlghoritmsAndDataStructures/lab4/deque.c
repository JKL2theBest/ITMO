#include "headers.h"

Deque* createDeque() {
    Deque* dq = (Deque*)malloc(sizeof(Deque));  
    dq->front = dq->rear = NULL;
    dq->size = 0;
    return dq;
}

int isEmptyDeque(Deque* dq) {
    return dq->front == NULL;
}

void insertFront(Deque* dq, double* array, int size) {
    DequeNode* newNode = (DequeNode*)malloc(sizeof(DequeNode));  
    newNode->array = array;
    newNode->size = size;
    newNode->prev = NULL;
    newNode->next = dq->front;
    if (isEmptyDeque(dq)) {
        dq->front = dq->rear = newNode;
    } else {
        dq->front->prev = newNode;
        dq->front = newNode;
    }
    dq->size++;
}

void insertRear(Deque* dq, double* array, int size) {
    DequeNode* newNode = (DequeNode*)malloc(sizeof(DequeNode));  
    newNode->array = array;
    newNode->size = size;
    newNode->next = NULL;
    if (isEmptyDeque(dq)) {
        dq->front = dq->rear = newNode;
        newNode->prev = NULL;
    } else {
        newNode->prev = dq->rear;
        dq->rear->next = newNode;
        dq->rear = newNode;
    }
    dq->size++;
}

DequeNode* deleteFront(Deque* dq) {
    if (isEmptyDeque(dq)) return NULL;
    DequeNode* temp = dq->front;
    dq->front = dq->front->next;
    if (dq->front) dq->front->prev = NULL;
    else dq->rear = NULL;
    dq->size--;
    return temp;
}

DequeNode* deleteRear(Deque* dq) {
    if (isEmptyDeque(dq)) return NULL;
    DequeNode* temp = dq->rear;
    dq->rear = dq->rear->prev;
    if (dq->rear) dq->rear->next = NULL;
    else dq->front = NULL;
    dq->size--;
    return temp;
}

void freeDeque(Deque* dq) {
    while (!isEmptyDeque(dq)) {
        DequeNode* node = deleteFront(dq);
        free(node->array);
        free(node);
    }
    free(dq);
}

// Чтение данных из файла в дек
Deque* read_data(const char* filename) {
    FILE* f = fopen(filename, "r");
    if (!f) {
        perror("Ошибка открытия файла");
        return NULL;
    }
    Deque* deque = createDeque();
    if (!deque) {
        fprintf(stderr, "Ошибка создания дека.\n");
        fclose(f);
        return NULL;
    }

    char temp[256];
    while (fscanf(f, "%255s", temp) == 1) {
        char* endptr;
        double val = strtod(temp, &endptr);
        if (endptr == temp || *endptr != '\0' || !isfinite(val)) {
            fprintf(stderr, "Ошибка: недопустимый элемент \"%s\" в файле.\n", temp);
            freeDeque(deque);
            fclose(f);
            return NULL;
        }
        double* part = malloc(sizeof(double));
        if (!part) {
            fprintf(stderr, "Ошибка выделения памяти.\n");
            freeDeque(deque);
            fclose(f);
            return NULL;
        }
        *part = val;
        insertRear(deque, part, 1);
    }
    fclose(f);
    return deque;
}

// Запись отсортированного массива в файл
void write_to_file(const char* filename, double* array, int size) {
    FILE* f = fopen(filename, "w");
    if (!f) {
        perror("Ошибка создания файла");
        return;
    }
    for (int i = 0; i < size; ++i) {
        fprintf(f, "%.15g ", array[i]);
    }
    printf("Результат записан в %s.\n\n", filename);
    fclose(f);
}
