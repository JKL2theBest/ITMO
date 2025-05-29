#ifndef UTILS_H
#define UTILS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <limits.h>
#include <getopt.h> 
#include <sys/types.h>
#include "plugin_api.h"

#define MAX_PLUGINS   64
#define MAX_PATH_LEN  PATH_MAX

typedef struct {
    void              *handle; // дескриптор из dlopen()
    struct plugin_info info;   // данные, полученные plugin_get_info()
    char              *path;   // полный путь до .so-файла
} plugin_t;


// Массив имён всех --длинных опций, переданных пользователем
#define MAX_PASSED_OPTS 128
extern char *passed_long_opts[MAX_PASSED_OPTS];
extern size_t passed_long_opts_count;

//
// Глобальные параметры утилиты (extern-переменные)
//
extern char   *plugin_dir;      // каталог для поиска плагинов
extern int     combine_and;     // -A (AND) режим объединения плагинных условий
extern int     combine_or;      // -O (OR) режим
extern int     invert_result;   // -N инверсия итогового результата
extern int     show_version;    // -v вывод версии и автора
extern int     show_help;       // -h вывод справки
extern char   *start_dir;       // начальный каталог для поиска
extern int     debug_enabled;   // LAB1DEBUG вкл/выкл отладку

//
// Массив загруженных плагинов
//
extern plugin_t  plugins[MAX_PLUGINS];
extern size_t    plugins_count;

//
// Собранные опции всех плагинов (после collect_all_plugin_options)
//
extern struct option *all_plugin_options;
extern size_t          all_plugin_options_count;

// Отладочный вывод (использует debug_enabled)
void debug_printf(const char *fmt, ...);

// Информационные сообщения утилиты
void print_version(void);
void print_help(void);
void print_loaded_plugins(void);

// Парсинг только коротких базовых опций
int  parse_command_line(int argc, char *argv[]);

// Загрузка/выгрузка плагинов из plugin_dir
int  load_plugins(const char *dir);
void unload_plugins(void);

// Сбор опций из каждого плагина в единый массив
int collect_all_plugin_options(void);

// Проверка дублирования имён опций разных плагинов
int check_option_conflicts(void);

// Запуск рекурсивного поиска с переданными опциями
int recursive_search(const char   *dir_path,
                     struct option *opts,
                     size_t         opts_len);

#endif // UTILS_H