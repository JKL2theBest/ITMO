#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <regex.h>
#include <errno.h>
#include <limits.h>
#include <unistd.h>

#define _GNU_SOURCE

// ANSI коды цветов
#define ANSI_COLOR_MAGENTA    "\x1b[35m" //Пурпурный
#define ANSI_COLOR_RESET   "\x1b[0m"

// Функция обрабатывает и выводит номера телефонов из заданного входного файла в заданный выходной файл.
void processAndPrintPhoneNumbers(FILE *inputFile, FILE *outputFile, int from, int to, int useColor, int onlySameLine) {
    // Регулярное выражение для поиска номеров телефонов
    const char *phoneRegex = "[+]?[78][(]?[[:digit:]]{3}[)]?[[:digit:]]{3}[-]?[[:digit:]]{2}[-]?[[:digit:]]{2}";
    regex_t regex;
    if (regcomp(&regex, phoneRegex, REG_EXTENDED) != 0) {
        fprintf(stderr, "Ошибка компиляции регулярного выражения\n");
        exit(EXIT_FAILURE);
    }

    char buffer[1024];
    int currentObject = 0;
    while (fgets(buffer, sizeof(buffer), inputFile) != NULL) {
        // Пропуск строк до указанного объекта "from"
        if (++currentObject < from) {
            continue;
        }
        // Поиск номеров телефонов в текущей строке
        regmatch_t match;
        char *current = buffer;
        while (regexec(&regex, current, 1, &match, 0) == 0) {
            if (onlySameLine && strchr(current, '\n') != NULL && current + match.rm_eo > strchr(current, '\n')) {
                break;
            }
            // Вывод части строки до совпадения
            fwrite(current, 1, match.rm_so, outputFile);
            // Вывод номера телефона с цветом или без него, в зависимости от опции "useColor"
            if (useColor) {
                fprintf(outputFile, ANSI_COLOR_MAGENTA);
            } else {
                fputs("*", outputFile);
            }
            // Вывод части номера телефона после совпадения
            fwrite(current + match.rm_so, 1, match.rm_eo - match.rm_so, outputFile);
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
    }
    regfree(&regex);
}


int main(int argc, char *argv[]) {
    // Проверка запуска с переменной среды, включающей отладочный вывод.
    // Пример запуска с установкой переменной LAB3DEBUG в 1:
    // $ LAB3DEBUG=1 ./lab3xxN3146 file.txt
    char *DEBUG = getenv("LAB3DEBUG");
    if (DEBUG) {
        fprintf(stderr, "Включен вывод отладочных сообщений\n");
    }
    if (argc > 9) {
        fprintf(stderr, "Использование: %s [опции] [имя_вход_файла [имя_выход_файла]]\n", argv[0]);
        return EXIT_FAILURE; 
    }

    int opt;
    int from = 1; 
    int to = -1;  
    int useColor = 0; 
    int onlySameLine = 0; 
    while ((opt = getopt(argc, argv, "vf:t:cn")) != -1) {
        switch (opt) {
            case 'v':
                if (DEBUG) {
                    fprintf(stderr, "Опция -v включена\n");
                }
                fprintf(stderr, "Суханкулиев Мухаммет, гр. N3146\nВариант: 12-2-1-4\n");
                exit(EXIT_SUCCESS);
                break;
            case 'f': // Опция "-f" для указания номера первого объекта (строки)
                from = atoi(optarg);
                if (from <= 0) {
                    fprintf(stderr, "Неверное значение параметра -f\n");
                    exit(EXIT_FAILURE);
                }
                if (DEBUG) {
                    fprintf(stderr, "Опция -f включена\n");
                }
                break;
            case 't': // Опция "-t" для указания номера последнего объекта (строки)
                if (sscanf(optarg, "%d", &to) != 1 || to <= 0) {
                    fprintf(stderr, "Неверное значение параметра -t\n");
                    exit(EXIT_FAILURE);
                }
                if (DEBUG) {
                    fprintf(stderr, "Опция -t включена\n");
                }
                break;
            case 'c': // Опция "-c" для включения использования цвета
                if (DEBUG) {
                    fprintf(stderr, "Опция -c включена\n");
                }
                useColor = 1;
                break;
            case 'n': // Опция "-n" для ограничения поиска одной строкой
                if (DEBUG) {
                    fprintf(stderr, "Опция -n включена\n");
                }
                onlySameLine = 1;
                break;
            default: // Обработка нераспознанных опций
                fprintf(stderr, "Использование: %s [опции] [имя_вход_файла [имя_выход_файла]]\n", argv[0]);
                exit(EXIT_FAILURE);
        }
    }
    // Обработка последнего объекта (строки)
    if (to == -1) {
        to = INT_MAX;
    }

    int numFiles = argc - optind;
    // Обработка одного файла (стандартного ввода или указанного в командной строке)
    if (numFiles == 0) {
        processAndPrintPhoneNumbers(stdin, stdout, from, to, useColor, onlySameLine);
    } else if (numFiles == 1) { // Обработка текстового файла (вывод в консоль) 
        FILE *sourceFile = fopen(argv[optind], "r");
        if (sourceFile == NULL) {
            perror("Ошибка чтения файла");
            exit(EXIT_FAILURE);
        }
        processAndPrintPhoneNumbers(sourceFile, stdout, from, to, useColor, onlySameLine);
        fclose(sourceFile);
    } else if (numFiles == 2) { // Обработка текстового файла (вывод в новый файл) 
        FILE *sourceFile = fopen(argv[optind], "r");
        if (sourceFile == NULL) {
            perror("Ошибка чтения файла");
            exit(EXIT_FAILURE);
        }
        FILE *destinationFile = fopen(argv[optind + 1], "w");
        if (destinationFile == NULL) {
            perror("Ошибка создания файла");
            fclose(sourceFile);
            exit(EXIT_FAILURE);
        }
        processAndPrintPhoneNumbers(sourceFile, destinationFile, from, to, useColor, onlySameLine);
        fclose(sourceFile);
        fclose(destinationFile);
    } else {
        fprintf(stderr, "Использование: %s [опции] [имя_вход_файла [имя_выход_файла]]\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    return EXIT_SUCCESS;
}
