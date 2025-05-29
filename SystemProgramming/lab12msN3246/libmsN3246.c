//
// gcc -shared -fPIC -Wall -Wextra -Werror -O3 libmsN3246.c -o libmsN3246.so
//

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include "plugin_api.h"

#define CARD_BYTES 8  // 8 байт = 16 BCD-цифр (по 4 бита на цифру)

static char *g_lib_name = "libmsN3246.so";
static char *g_plugin_purpose = "Поиск файлов с корректными номерами кредитных карт в бинарной форме";
static char *g_plugin_author = "Суханкулиев Мухаммет, N3246";

static struct plugin_option g_po_arr[] = {
    {
        {
            "ccards-bin", no_argument, 0, 0
        },
        "Поиск корректных номеров кредитных карт в бинарной форме"
    }
};

static int g_po_arr_len = sizeof(g_po_arr) / sizeof(g_po_arr[0]);

//
//  Приватные функции
//
static inline int is_debug_mode(void) {
    return getenv("LAB1DEBUG") != NULL;
}

static int is_valid_bcd(const unsigned char *buf, size_t len) {
    for (size_t i = 0; i < len; ++i) {
        unsigned char hi = (buf[i] & 0xF0) >> 4;
        unsigned char lo = buf[i] & 0x0F;
        if (hi > 9 || lo > 9)
            return 0;
    }
    return 1;
}

static int is_valid_luhn(const unsigned char *buf) {
    unsigned char digits[16];
    for (size_t i = 0; i < CARD_BYTES; ++i) {
        digits[2 * i]     = (buf[i] & 0xF0) >> 4;
        digits[2 * i + 1] = buf[i] & 0x0F;
    }

    int sum = 0;
    for (int i = 15; i >= 0; --i) {
        int digit = digits[i];
        if ((15 - i) % 2 == 1) {
            digit *= 2;
            if (digit > 9) digit -= 9;
        }
        sum += digit;
    }
    return (sum % 10 == 0);
}

static int has_too_many_zeros(const unsigned char *buf) {
    int zero_count = 0;
    for (size_t i = 0; i < CARD_BYTES; ++i) {
        if (((buf[i] & 0xF0) >> 4) == 0) ++zero_count;
        if ((buf[i] & 0x0F) == 0) ++zero_count;
    }
    return zero_count >= 10;
}

static int starts_with_zero(const unsigned char *buf) {
    return ((buf[0] & 0xF0) >> 4) == 0;
}

static void print_card_number(FILE *stream, const unsigned char *buf) {
    for (int i = 0; i < CARD_BYTES; ++i) {
        fprintf(stream, "%X%X", (buf[i] & 0xF0) >> 4, buf[i] & 0x0F);
    }
    fputc('\n', stream);
}

static int is_valid_card(const unsigned char *buf) {
    return is_valid_bcd(buf, CARD_BYTES) &&
           !has_too_many_zeros(buf) &&
           !starts_with_zero(buf) &&
           is_valid_luhn(buf);
}

//
//  API функции
//
int plugin_get_info(struct plugin_info* ppi) {
    if (!ppi) {
        fprintf(stderr, "[%s] ERROR: Неверный аргумент\n", g_lib_name);
        return -1;
    }

    ppi->plugin_purpose = g_plugin_purpose;
    ppi->plugin_author = g_plugin_author;
    ppi->sup_opts_len = g_po_arr_len;
    ppi->sup_opts = g_po_arr;

    return 0;
}

int plugin_process_file(const char *fname, struct option in_opts[], size_t in_opts_len) {
    // Проверка, включён ли нужный флаг
    int enabled = 0;
    for (size_t i = 0; i < in_opts_len; ++i) {
        if (strcmp(in_opts[i].name, "ccards-bin") == 0) {
            enabled = 1;
            break;
        }
    }
    if (!enabled) return 0;

    // Открытие файла
    FILE *file = fopen(fname, "rb");
    if (!file) {
        fprintf(stderr, "[%s] ERROR: Не удалось открыть файл '%s': %s\n", g_lib_name, fname, strerror(errno));
        return 1;
    }

    unsigned char buffer[CARD_BYTES];
    unsigned char reversed[CARD_BYTES];
    size_t offset = 0;
    int found = 0;
    int debug = is_debug_mode();

    // Основная обработка файла
    while (fread(buffer, 1, CARD_BYTES, file) == CARD_BYTES) {
        // Пропуск полностью нулевых блоков
        if (memcmp(buffer, "\0\0\0\0\0\0\0\0", CARD_BYTES) == 0) {
            ++offset;
            fseek(file, offset, SEEK_SET);
            continue;
        }

        // Подготовка реверсированного буфера
        for (int i = 0; i < CARD_BYTES; ++i)
            reversed[i] = buffer[CARD_BYTES - 1 - i];

        int valid_le = is_valid_card(buffer);
        int valid_be = is_valid_card(reversed);

        if (debug && (valid_le || valid_be)) {
            fprintf(stderr, "[%s] DEBUG: Offset %zu: ", g_lib_name, offset);
            if (valid_le && valid_be) {
                fprintf(stderr, "LE & BE valid: ");
                print_card_number(stderr, buffer);
            } else if (valid_le) {
                fprintf(stderr, "LE valid: ");
                print_card_number(stderr, buffer);
            } else {
                fprintf(stderr, "BE valid: ");
                print_card_number(stderr, reversed);
            }
        }

        if (valid_le || valid_be)
            ++found;

        ++offset;
        fseek(file, offset, SEEK_SET);  // сдвиг на один байт
    }

    if (ferror(file)) {
        fprintf(stderr, "[%s] ERROR: Ошибка чтения файла '%s': %s\n", g_lib_name, fname, strerror(errno));
        fclose(file);
        return -1;
    }

    fclose(file);

    if (debug){
        printf("[%s] DEBUG: Найдено корректных номеров: %d в файле %s\n", g_lib_name, found, fname);
    }
    return (found > 0) ? 0 : 1;
}
