#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <regex.h>
#include <errno.h>
#include <limits.h>
#include <unistd.h>

#include "functions.h"

#define _GNU_SOURCE

int main(int argc, char *argv[]) {
    // Проверка запуска с переменной среды, включающей отладочный вывод.
    // Пример запуска с установкой переменной LAB3DEBUG в 1:
    // $ LAB3DEBUG=1 ./lab3msN3146 -c nomera.txt
    char *DEBUG = getenv("LAB3DEBUG");
    if (DEBUG) {
        fprintf(stderr, "Включен вывод отладочных сообщений\n");
    }
    if (argc > 9) {
        fprintf(stderr, "Использование: %s [опции] [имя_вход_файла [имя_выход_файла]]\n", argv[0]);
        return EXIT_FAILURE; 
    }

    int opt;
    int from = 1; // Номер первого обрабатываемого объекта (строки)
    int to = -1;  // Номер последнего обрабатываемого объекта (строки)
    int useColor = 0; // Флаг использования цвета
    int onlySameLine = 0; // Флаг ограничения поиска одной строкой
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
                fprintf(stderr, "Использование: %s [-v] [-f M] [-t N] [-c] [-n] [имя_вход_файла [имя_выход_файла]]\n", argv[0]);
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
        processAndPrintPhoneNumbers(stdin, stdout, from, to, useColor, onlySameLine, DEBUG);
    } else if (numFiles == 1) { // Обработка текстового файла (вывод в консоль) 
        FILE *sourceFile = fopen(argv[optind], "r");
        if (sourceFile == NULL) {
            perror("Ошибка чтения файла");
            exit(EXIT_FAILURE);
        }
        if (DEBUG) {
            fprintf(stderr, "Из файла %s:\n", argv[optind ]);
        }
        processAndPrintPhoneNumbers(sourceFile, stdout, from, to, useColor, onlySameLine, DEBUG=0);
        fclose(sourceFile);
    } else if (numFiles == 2) { // Обработка текстового файла (вывод в новый файл) 
        FILE *sourceFile = fopen(argv[optind], "r");
        if (useColor) {
            printf("Оно тебе нужно?\nТы же понимаешь, что выведет белиберду?\n");
        }
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
        if (DEBUG) {
            fprintf(stderr, "\nP.S. Результат смотри в %s", argv[optind + 1]);
        }
        processAndPrintPhoneNumbers(sourceFile, destinationFile, from, to, useColor, onlySameLine, DEBUG=0);
        fclose(sourceFile);
        fclose(destinationFile);
    } else {
        fprintf(stderr, "Использование: %s [-v] [-f M] [-t N] [-c] [-n] [имя_вход_файла [имя_выход_файла]]\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    return EXIT_SUCCESS;
}
