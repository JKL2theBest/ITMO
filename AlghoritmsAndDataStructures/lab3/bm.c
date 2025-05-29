#include "headers.h"

// Построение таблицы "плохих символов" для эвристики bad character
// badchar[c] хранит индекс последнего вхождения символа c в шаблоне
void preprocess_bad(const char* pat, int m, int badchar[256]) {
    for (int i = 0; i < 256; i++)
        badchar[i] = -1;
    for (int i = 0; i < m; i++)
        badchar[(unsigned char)pat[i]] = i;
}

// Построение таблицы сдвигов для эвристики совпавшего суффикса
void preprocess_good(const char* pat, int m, int* shift) {
    int* border = malloc((m + 1) * sizeof(int));  // border[i] — индекс, куда откатиться при несоответствии
    int i = m, j = m + 1;
    border[i] = j;
    // 1: вычисляем границы для суффиксов
    while (i > 0) {
        while (j <= m && pat[i - 1] != pat[j - 1]) {
            if (shift[j] == 0)
                shift[j] = j - i;  // Задаём сдвиг при несовпадении
            j = border[j];         // Переход по границе
        }
        border[--i] = --j;
    }
    // 2: заполняем неинициализированные элементы shift
    j = border[0];
    for (i = 0; i <= m; i++) {
        if (shift[i] == 0)
            shift[i] = j;           // Используем наименьший сдвиг
        if (i == j) j = border[j];  // Переход к следующей границе
    }

    free(border);
}

// Обёртка: ввод числа, преобразование в строку и поиск
void boyer_moore(double* array, int size) {
    char input[MAX_INPUT];
    // Устанавливаем обработчик сигнала SIGINT (Ctrl+C)
    signal(SIGINT, handle_sigint);
    while (1) {
        if (exit_flag) {
            printf("Программа остановлена.\n");
            break;
        }
        printf("\nВведите число для поиска методом Бойера-Мура('q' для выхода): ");
        if (!fgets(input, MAX_INPUT, stdin)) break;
        if (strncmp(input, "q", 1) == 0) break;
        if (strlen(input) >= MAX_INPUT - 1) {
            printf("Ввод слишком длинный. Повторите.\n");
            while (getchar() != '\n');
            continue;
        }
        // Преобразуем ввод в число
        char* endptr;
        double pattern = strtod(input, &endptr);
        if (endptr == input || (*endptr != '\n' && *endptr != '\0')) {
            printf("Некорректный ввод. Введите число.\n");
            continue;
        }
        // Преобразуем число для поиска в строку (точность до 15 значащих цифр)
        char pattern_str[MAX_INPUT];
        snprintf(pattern_str, MAX_INPUT, "%.15g", pattern);
        int found = -1;
        for (int i = 0; i < size; ++i) {
            // Преобразуем i-й элемент массива в строку
            char array_str[MAX_INPUT];
            snprintf(array_str, MAX_INPUT, "%.15g", array[i]);
            // Ищем шаблон в строковом представлении элемента массива
            found = boyer_moore_string(array_str, pattern_str);
            if (found != -1) {
                // Дополнительно сравниваем числа с учётом машинной точности
                if (fabs(array[i] - pattern) < 1e-9) {
                    printf("Число %.15g расположено по индексу %d.\n", array[i], i);
                    break;
                }
            }
        }
        if (found == -1) {
            printf("Значение не найдено\n");
        }
    }
}

// Основной алгоритм Бойера-Мура для поиска pattern в text
// Возвращает индекс первого вхождения или -1
int boyer_moore_string(const char* text, const char* pattern) {
    int m = strlen(pattern);
    int n = strlen(text);
    int bad_char[256];
    // Построение таблицы плохих символов
    for (int i = 0; i < 256; i++) {
        bad_char[i] = -1;
    }
    for (int i = 0; i < m; i++) {
        bad_char[(unsigned char) pattern[i]] = i;
    }
    int s = 0;  // Текущий сдвиг шаблона по отношению к тексту
    while (s <= n - m) {
        int j = m - 1;
        // Сравниваем шаблон с текстом справа налево
        while (j >= 0 && pattern[j] == text[s + j]) {
            j--;
        }
        if (j < 0) {
            // Полное совпадение
            return s;
        } else {
            // Сдвигаем шаблон с учётом позиции плохого символа
            int bad_idx = bad_char[(unsigned char) text[s + j]];
            s += (j - bad_idx > 1) ? j - bad_idx : 1;
        }
    }
    return -1;  // Совпадение не найдено
}