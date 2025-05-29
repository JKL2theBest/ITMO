#ifndef FUNCTIONS_H
#define FUNCTIONS_H

// ANSI коды цветов
#define ANSI_COLOR_BLUE    "\x1b[34m"
#define ANSI_COLOR_RESET   "\x1b[0m"

// Ура, закончил писать код :D
// Функция обрабатывает и выводит номера телефонов из заданного входного файла в заданный выходной файл.
void processAndPrintPhoneNumbers(FILE *inputFile, FILE *outputFile, int from, int to, int useColor, int onlySameLine, char *DEBUG) {
    // Регулярное выражение для поиска номеров телефонов
    const char *phoneRegex = "[+]?[78][(]?[[:digit:]]{3}[)]?[[:digit:]]{3}[-]?[[:digit:]]{2}[-]?[[:digit:]]{2}";
    regex_t regex;
    if (regcomp(&regex, phoneRegex, REG_EXTENDED) != 0) {
        fprintf(stderr, "Ошибка компиляции регулярного выражения\n");
        exit(EXIT_FAILURE);
    }

    char buffer[1024];
    int currentObject = 0;

    if (DEBUG) {
            fprintf(stderr, "Ввод:  ");
        }
    while (fgets(buffer, sizeof(buffer), inputFile) != NULL) {
        if (DEBUG) {
            fprintf(stderr, "Вывод: ");
        }
        // Пропуск строк до указанного объекта "from"
        if (++currentObject < from) {
            continue;
        }
        // Поиск номеров телефонов в текущей строке
        regmatch_t match;
        char *current = buffer;
        while (regexec(&regex, current, 1, &match, 0) == 0) {
            // Проверка, если указана опция "onlySameLine" и совпадение не находится на той же строке
            if (onlySameLine && strchr(current, '\n') != NULL && current + match.rm_eo > strchr(current, '\n')) {
                break; // Игнорирование совпадений, которые выходят за пределы текущей строки
            }
            // Вывод части строки до совпадения
            fwrite(current, 1, match.rm_so, outputFile);
            // Вывод номера телефона с цветом или без него, в зависимости от опции "useColor"
            if (useColor) {
                fprintf(outputFile, ANSI_COLOR_BLUE);
            } else {
                fputs("*", outputFile);
            }
            // Вывод части номера телефона после совпадения
            fwrite(current + match.rm_so, 1, match.rm_eo - match.rm_so, outputFile);
            // Сброс цвета, если опция "useColor" включена
            if (useColor) {
                fprintf(outputFile, ANSI_COLOR_RESET);
            } else {
                fputs("*", outputFile);
            }
            current += match.rm_eo;
        }
        fputs(current, outputFile);
        if (currentObject == to) {
            break;
        }
        if (DEBUG) {
            fprintf(stderr, "Ввод:  ");
        }
    }
    regfree(&regex);
}

#endif
