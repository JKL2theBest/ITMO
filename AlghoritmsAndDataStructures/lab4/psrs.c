#include "headers.h"

// Comparator для qsort (возвращает −1,0,1)
int compare(const void *pa, const void *pb) {
    double a = *(const double*)pa;
    double b = *(const double*)pb;
    return (a > b) - (a < b);
}

void* local_sort(void *arg) {
    ThreadData *td = (ThreadData*)arg;
    qsort(td->array, td->size, sizeof(double), compare);
    printf("Поток %d получил %zu элементов. Отсортированный подмассив:\n",
           td->id + 1, (size_t)td->size);
    for (int i = 0; i < td->size; i++) {
        printf("%.15g ", td->array[i]);
    }
    printf("\n");
    return NULL;
}

void choose_samples(ThreadData *threads, int p, double *samples) {
    for (int i = 0; i < p; i++) {
        const ThreadData *td = &threads[i];
        // Берём p сэмплов равномерно из отсортированного фрагмента
        for (int j = 0; j < p; j++) {
            size_t idx = (size_t)j * td->size / p;
            samples[(size_t)i * p + j] = td->array[idx];
}}}

void choose_splitters(double *samples, int total_samples, int p) {
    puts("[Шаг 4] Сортировка вспомогательного массива выборок...");
    qsort(samples, total_samples, sizeof(double), compare);
    puts("[Шаг 5] Выбор разделителей для разбиения на группы...");
    // Каждый (k*p + p/2)-й элемент из отсортированных samples —
    // это медиана блока из p элементов
    for (int k = 1; k < p; k++) {
        splitters[k - 1] = samples[k * p + (p / 2) - 1];
    }
    printf("Выбранные разделители: ");
    for (int i = 0; i < p - 1; i++) {
        printf("%.15g ", splitters[i]);
    }
    printf("\n");
}

// Перераспределение по группам
void redistribute(int p) {
    // 1) Создать p деков — по одному для каждой группы
    Deque **buckets = calloc((size_t)p, sizeof(Deque*));
    if (!buckets) {
        perror("calloc(buckets)");
        exit(EXIT_FAILURE);
    }
    for (int i = 0; i < p; i++) {
        buckets[i] = createDeque();
        if (!buckets[i]) {
            fprintf(stderr, "Не удалось создать deque для группы %d\n", i);
            exit(EXIT_FAILURE);
        }
    }
    // 2) Пройти по каждому локально-отсортированному фрагменту
    for (int src = 0; src < p; src++) {
        double *arr = sub_arrays[src];
        int     n   = sub_sizes[src];

        for (int j = 0; j < n; j++) {
            double v = arr[j];
            int grp = 0;
            // найти первую splitters[grp] >= v
            while (grp < p - 1 && v > splitters[grp]) {
                grp++;
            }
            // Поместить v в дек buckets[grp]
            double *single = malloc(sizeof(double));
            if (!single) {
                perror("malloc(single)");
                exit(EXIT_FAILURE);
            }
            *single = v;
            insertRear(buckets[grp], single, 1);
        }
    }
    // 3) Собирать назад: каждый buckets[i] преобразовать в sub_arrays[i]
    for (int i = 0; i < p; i++) {
        // 3.1) посчитать итоговый размер
        size_t total = 0;
        for (DequeNode *node = buckets[i]->front; node; node = node->next) {
            total += node->size;
        }
        // 3.2) аллоцировать
        double *out = malloc(total * sizeof(double));
        if (!out) {
            perror("malloc(sub_arrays[i])");
            exit(EXIT_FAILURE);
        }
        // 3.3) заполнить и очистить deque
        size_t pos = 0;
        DequeNode *node;
        while ((node = deleteFront(buckets[i])) != NULL) {
            memcpy(out + pos, node->array, node->size * sizeof(double));
            pos += node->size;
            free(node->array);
            free(node);
        }
        sub_arrays[i] = out;
        sub_sizes[i]  = (int)total;
        freeDeque(buckets[i]);
    }
    free(buckets);
}

void* merge_sort(void *arg) {
    ThreadData *td = (ThreadData*)arg;
    qsort(td->array, td->size, sizeof(double), compare);
    return NULL;
}
