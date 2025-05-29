#define _XOPEN_SOURCE 700  // Для nftw()
#include "lab11msN3246.h"

int main(int argc, char *argv[]) {
    int opt;
    int show_help = 0, show_version = 0;

    struct option long_options[] = {
        {"help", no_argument, 0, 'h'},
        {"version", no_argument, 0, 'v'},
        {0, 0, 0, 0}
    };

    // Проверка LAB11DEBUG
    debug_mode = (getenv("LAB11DEBUG") != NULL);
    if (debug_mode) {
        fprintf(stderr, "[DEBUG] Debug mode is enabled\n");
    }

    // Обработка опций командной строки
    while ((opt = getopt_long(argc, argv, "hv", long_options, NULL)) != -1) {
        switch (opt) {
            case 'h':
                show_help = 1;
                break;
            case 'v':
                show_version = 1;
                break;
            default:
                fprintf(stderr, "Unknown option. Use -h for help.\n");
                return 1;
        }
    }
    if (show_help) {
        print_help();
    }
    if (show_version) {
        print_version();
    }
    if (show_help || show_version) {
        return 0;
    }

    // Доп. проверка аргументов
    if (optind + 2 != argc) {
        fprintf(stderr, "Usage: %s [options] <directory> <search_pattern>\n", argv[0]);
        return 1;
    }

    // Парсинг шаблона поиска
    if (parse_hex_pattern(argv[optind + 1]) != 0) {
        return 1;
    }
    if (debug_mode) {
        fprintf(stderr, "[DEBUG] Search pattern: ");
        for (size_t i = 0; i < pattern_size; i++) {
            fprintf(stderr, "%02x ", search_pattern[i]);
        }
        fprintf(stderr, "\n");
    }

    // Обработка каталога и выполнение поиска
    const char *dir = argv[optind];
    if (nftw(dir, search_file, 20, FTW_PHYS) == -1) {
        perror("Error processing directory");
        log_error("Error processing directory.");
        return 1;
    }
    free(search_pattern);
    return 0;
}
