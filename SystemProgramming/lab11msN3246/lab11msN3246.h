#ifndef LAB11MSN3246_H
#define LAB11MSN3246_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>
#include <errno.h>
#include <ftw.h>
#include <syslog.h>

#define MAX_PATTERN_SIZE 256
#define BUFFER_SIZE 4096

unsigned char *search_pattern = NULL;  // Динамическая память для шаблона поиска
size_t pattern_size = 0;
int debug_mode = 0;  // Глобальная переменная для режима отладки

void print_help() {
    printf("Usage: [LAB11DEBUG=1] ./lab11msN3246 [options]  <directory> <search_pattern>\n");
    printf("Options:\n");
    printf("  -h, --help       Show this help message\n");
    printf("  -v, --version    Show version information\n");
}

void print_version() {
    printf("lab11msN3246 version 1.0\n");
    printf("Author: Суханкулиев Мухаммет, Group: N3246, Поток: ОСП N23 1.2, Variant: 4\n");
}

int is_hex_digit(char c) {
    return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');
}

int parse_hex_pattern(const char *str) {
    if (strlen(str) < 4 || strncmp(str, "0x", 2) != 0) {
        fprintf(stderr, "Error: Search pattern must start with '0x' and be at least 2 characters long after '0x'.\n");
        return -1;
    }

    size_t len = strlen(str) - 2;
    if (len % 2 != 0 || len / 2 > MAX_PATTERN_SIZE) {
        fprintf(stderr, "Error: Invalid search pattern length.\n");
        return -1;
    }

    for (size_t i = 2; i < 2 + len; i++) {
        if (!is_hex_digit(str[i])) {
            fprintf(stderr, "Error: Invalid hex format in search pattern.\n");
            return -1;
        }
    }

    pattern_size = len / 2;
    search_pattern = (unsigned char *)malloc(pattern_size);
    if (!search_pattern) {
        fprintf(stderr, "Error: Memory allocation failed for search pattern.\n");
        return -1;
    }

    for (size_t i = 0; i < pattern_size; i++) {
        sscanf(str + 2 + (i * 2), "%2hhx", &search_pattern[i]);
    }

    return 0;
}

int search_file(const char *path, const struct stat *statbuf, int type, struct FTW *ftwbuf) {
    if (path == NULL || statbuf == NULL || ftwbuf == NULL) {
        fprintf(stderr, "[DEBUG] Error: NULL pointer passed to search_file.\n");
        return 1;
    }

    if (debug_mode) {
        fprintf(stderr, "[DEBUG] Searching file: %s\n", path);
    }

    if (type == FTW_F) {
        FILE *file = fopen(path, "rb");  // Открываем файл для бинарного чтения
        if (!file) {
            if (errno == EACCES) {
                if (debug_mode) {
                    fprintf(stderr, "Error: Permission denied for file: %s\n", path);
                }
                return 0;  // Пропуск файла
            }
            perror("Error opening file");
            return 1;
        }

        size_t file_size = statbuf->st_size;
        if (file_size == 0) {
            if (debug_mode) {
                fprintf(stderr, "[DEBUG] File %s is empty.\n", path);
            }
            fclose(file);
            return 0;
        }

        unsigned char buffer[BUFFER_SIZE];
        size_t bytes_read = 0;
        int found = 0;

        while ((bytes_read = fread(buffer, 1, BUFFER_SIZE, file)) > 0) {
            for (size_t i = 0; i + pattern_size <= bytes_read; i++) {
                if (memcmp(buffer + i, search_pattern, pattern_size) == 0) {
                    printf("Pattern found in file: %s\n", path);
                    found = 1;
                    break;
                }
            }
            if (found) break;
        }

        if (bytes_read < BUFFER_SIZE && ferror(file)) {
            perror("Error reading file");
            fclose(file);
            return 1;
        }

        fclose(file);
    } else if (type == FTW_D) {
        if (debug_mode) {
            fprintf(stderr, "[DEBUG] Directory: %s\n", path);
        }
    } else {
        if (debug_mode) {
            fprintf(stderr, "[DEBUG] Other type: %s\n", path);
        }
    }

    return 0;
}

void log_error(const char *msg) {
    openlog("lab11msN3246", LOG_PID | LOG_CONS, LOG_USER);
    syslog(LOG_ERR, "%s", msg);
    closelog();
}

#endif // LAB11MSN3246_H
