#include "headers.h"

double* splitters;
double** sub_arrays;
int* sub_sizes;
volatile sig_atomic_t exit_flag;

void handle_sigint(int sig) {
    (void)sig;
    exit_flag = 1;
}

int main(int argc, char* argv[]) {
    signal(SIGINT, handle_sigint);
    // Проверка аргументов командной строки
    if (argc != 3) {
        printf("Использование: %s <входной_файл> <количество_потоков>\n", argv[0]);
        return 1;
    }
    const char* filename = argv[1];
    int p = atoi(argv[2]);
    if (p < 2 || p > 6) {
        printf("Ошибка: количество потоков должно быть числом больше 1 и не больше 6.\n");
        return 1;
    }
    // Запись данных из файла в дек
    Deque* deque = read_data(filename);
    if (!deque) {
        return 1;
    }
    int n = deque->size;
    printf("Прочитано %d чисел из файла.\nСодержимое дека:\n", n);
    // Печать содержимого дека
    for (DequeNode* node = deque->front; node; node = node->next) {
        printf("%.15g ", *node->array);
    }
    printf("\n\n");
    if (n == 0) {
        fprintf(stderr, "Ошибка: файл не содержит double числа.\n");
        freeDeque(deque);
        return 1;
    }
    double* buffer = malloc(n * sizeof(double));
    if (!buffer) {
        fprintf(stderr, "Ошибка выделения памяти для массива.\n");
        freeDeque(deque);
        return 1;
    }
    // Заполнение массива из дека
    int index = 0;
    while (!isEmptyDeque(deque)) {
        DequeNode* dnode = deleteFront(deque);
        buffer[index++] = *dnode->array;
        free(dnode->array);
        free(dnode);
    }
    freeDeque(deque);

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
    // Локальная сортировка на каждом потоке
    printf("[Шаг 2] Локальная сортировка на каждом потоке...\n");
    int base = n / p, rem = n % p, offset = 0;
    for (int i = 0; i < p; ++i) {
        int size = base + (i < rem);     // Размер подмассива с учётом остатка
        sub_arrays[i] = buffer + offset; // Указатель на начало подмассива
        sub_sizes[i] = size;
        tdata[i] = (ThreadData){ sub_arrays[i], size, i };
        pthread_create(&threads[i], NULL, local_sort, &tdata[i]);
        offset += size;
    }
    for (int i = 0; i < p; ++i) pthread_join(threads[i], NULL);
    printf("[Шаг 3] Создание вспомогательного массива выборок...\n");
    double* samples = malloc(p * p * sizeof(double));
    choose_samples(tdata, p, samples);
    splitters = malloc((p - 1) * sizeof(double));
    choose_splitters(samples, p * p, p);
    free(samples);
    // Разбиение данных по разделителям
    printf("[Шаг 6] Разбиение данных в каждом потоке согласно разделителям...\n");
    redistribute(p);
    // Многопутевое слияние
    printf("[Шаг 7] Объединение групп и сортировка внутри потоков (многопутевое слияние)...\n");
    for (int i = 0; i < p; ++i) {
        tdata[i].array = sub_arrays[i];
        tdata[i].size = sub_sizes[i];
        pthread_create(&threads[i], NULL, merge_sort, &tdata[i]);
    }
    for (int i = 0; i < p; ++i) pthread_join(threads[i], NULL);
    // Объединение отсортированных частей
    double* result = malloc(n * sizeof(double));
    offset = 0;
    for (int i = 0; i < p; ++i) {
        memcpy(result + offset, sub_arrays[i], sub_sizes[i] * sizeof(double));
        offset += sub_sizes[i];
    }
    // Вывод отсортированного массива
    printf("\nОтсортированный массив:\n");
    for (int i = 0; i < n; ++i) printf("%.15g ", result[i]);
    printf("\n\n");
    write_to_file("sorted_result.txt", result, n);
    char command[256];
    // Открытие результата
    snprintf(command, sizeof(command), "subl sorted_result.txt");
    if (system(command) != 0) {
        printf("Ошибка при sorted_result.txt.\n");
    }
    // Работа с красно-черным деревом
    RBTree* tree = createRBTree();
    int insLen;
    int *insOrder = makeInsertionOrder(n, &insLen);
    for (int i = 0; i < insLen; ++i) {
        int idx = insOrder[i];
        rbInsert(tree, result[idx]);
    }
    free(insOrder);
    // Освобождение памяти
    for (int i = 0; i < p; ++i) free(sub_arrays[i]);
    free(sub_arrays);
    free(sub_sizes);
    free(splitters);
    free(threads);
    free(tdata);
    free(result);
    free(buffer);
    // Экспорт дерева в DOT файл и создание PNG
    const char* dotFilename = "tree.dot";
    const char* pngFilename = "tree.png";
    exportRBTreeToDot(tree, dotFilename);
    printf("DOT файл дерева сохранён в %s\n", dotFilename);
    // Генерация PNG с помощью Graphviz
    snprintf(command, sizeof(command), "dot -Tpng %s -o %s", dotFilename, pngFilename);
    int ret = system(command);
    if (ret == 0) {
        printf("PNG изображение дерева успешно создано: %s\n", pngFilename);
        // Открытие PNG файла
        snprintf(command, sizeof(command), "xdg-open %s", pngFilename);
        if (system(command) != 0) {
            printf("Ошибка при открытии PNG изображения.\n");
        }
    } else {
        printf("Ошибка: Убедитесь, что Graphviz установлен.\nДоступна ли команда dot -Tpng...?\n");
    }
    // Цикл для поиска числа в красно-черном дереве
    char input[MAX_INPUT];
    while (1) {
        if (exit_flag) {
            printf("Программа остановлена.\n");
            break;
        }
        printf("\nВведите число для поиска в красно-черном дереве ('q' для выхода): ");
        if (!fgets(input, MAX_INPUT, stdin)) break;
        if (strncmp(input, "q", 1) == 0) break;
        if (strlen(input) >= MAX_INPUT - 1) {
            printf("Ввод слишком длинный. Повторите.\n");
            while (getchar() != '\n');
            continue;
        }
        char* endptr;
        double val = strtod(input, &endptr);
        if (endptr == input || (*endptr != '\n' && *endptr != '\0')) {
            printf("Некорректный ввод. Введите число.\n");
            continue;
        }
        RBNode* found = rbSearch(tree, val);
        if (found) {
            int rank = rbGetRank(tree, val);
            const char* color = (found->color == 1) ? "красный" : "черный";
            printf("Позиция (ранг) числа %.15g в дереве: %d, цвет узла: %s\n",
                   val, rank, color);
        } else {
            printf("Число %.15g не найдено в дереве.\n", val);
    }}
    freeRBTree(tree);
    return 0;
}
