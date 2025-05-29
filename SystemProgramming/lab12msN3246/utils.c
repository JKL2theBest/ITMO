#include "utils.h"
#include <ftw.h>
#include <dirent.h>
#include <dlfcn.h>
#include <stdarg.h>

// Определения extern-переменных
char *plugin_dir = NULL;
int combine_and = 1, combine_or = 0, invert_result = 0;
int show_version = 0, show_help = 0;
char *start_dir = NULL;
int debug_enabled = 0;

plugin_t plugins[MAX_PLUGINS];
size_t   plugins_count = 0;

struct option *all_plugin_options = NULL;
size_t		  all_plugin_options_count = 0;

struct option *global_opts = NULL;
size_t global_opts_len = 0;

char *passed_long_opts[MAX_PASSED_OPTS];
size_t passed_long_opts_count = 0;


// Проверяет, есть ли у плагина хотя бы одна опция из passed_long_opts[]
static int plugin_matches_passed_opts(const struct plugin_info *pi) {
    for (size_t i = 0; i < pi->sup_opts_len; i++) {
        const char *name = pi->sup_opts[i].opt.name;
        for (size_t j = 0; j < passed_long_opts_count; j++) {
            if (strcmp(name, passed_long_opts[j]) == 0)
                return 1;
        }
    }
    return 0;
}

// Вывод отладочных сообщений, если задана LAB1DEBUG
void debug_printf(const char *fmt, ...) {
	if (!debug_enabled) return;
	va_list ap;
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	va_end(ap);
}

void print_version(void) {
	printf("lab12msN3246 version 1.2\n");
	printf("Author: Суханкулиев Мухаммет\nGroup: N3246\nПоток: ОСП N23 1.2\nVariant: 24\n");
}

// Вывод справки по опциям и плагинам
void print_help(void) {
	printf("Usage: lab12msN3246 [options] [directory]\n");
	printf("Options:\n");
	printf("  -P dir   Указать каталог с плагинами\n");
	printf("  -A	   Объединение условий по AND (по умолчанию)\n");
	printf("  -O	   Объединение условий по OR\n");
	printf("  -N	   Инвертировать итоговое условие\n");
	printf("  -v	   Show author information\n");
	printf("  -h	   Show this help message\n\n");
}

// Вывод загруженных плагинов и их описаний
void print_loaded_plugins(void) {
	fprintf(stderr, "Loaded %zu plugin(s):\n", plugins_count);
	for (size_t i = 0; i < plugins_count; i++) {
		struct plugin_info *pi = &plugins[i].info;
		fprintf(stderr, "  Plugin [%s]\n", plugins[i].path);
		fprintf(stderr, "	Purpose: %s\n", pi->plugin_purpose);
		fprintf(stderr, "	Author : %s\n", pi->plugin_author);
		for (size_t j = 0; j < pi->sup_opts_len; j++) {
			fprintf(stderr, "	  --%s : %s\n", pi->sup_opts[j].opt.name, pi->sup_opts[j].opt_descr);
		}
	}
}

// Загрузка плагинов из указанного каталога
int load_plugins(const char *dir) {
    DIR *dp = opendir(dir);
    if (!dp) { 
		fprintf(stderr, "Cannot open plugin dir '%s': %s\n", dir, strerror(errno));
		return -1;
	}

    struct dirent *entry;
    plugins_count = 0;
    while ((entry = readdir(dp)) != NULL) {
        if (plugins_count >= MAX_PLUGINS) break;
        size_t len = strlen(entry->d_name);
        if (len <= 3 || strcmp(entry->d_name + len - 3, ".so") != 0) continue;

        char fullpath[MAX_PATH_LEN];
        snprintf(fullpath, sizeof(fullpath), "%s/%s", dir, entry->d_name);

        void *handle = dlopen(fullpath, RTLD_LAZY);
        if (!handle) { 
				fprintf(stderr, "dlopen failed '%s': %s\n", fullpath, dlerror());
				continue;
			}

        int (*get_info)(struct plugin_info*) = dlsym(handle, "plugin_get_info");
        if (!get_info) { dlclose(handle); continue; }

        struct plugin_info pi;
        if (get_info(&pi) < 0) { dlclose(handle); continue; }

        // **Фильтрация по passed_long_opts**
        if (passed_long_opts_count > 0 && !plugin_matches_passed_opts(&pi)) {
            debug_printf("Skipping plugin %s: no matching --opts\n", fullpath);
            dlclose(handle);
            continue;
        }

        // Только после проверки сохраняем плагин
        plugins[plugins_count].handle = handle;
        plugins[plugins_count].info   = pi;
        plugins[plugins_count].path   = strdup(fullpath);
        plugins_count++;
    }
    closedir(dp);
    if (plugins_count == 0) { 
		fprintf(stderr, "No valid plugins loaded from '%s'\n", dir);
		return -1;
	}
    return 0;
}
// Выгрузка плагинов
void unload_plugins(void) {
	for (size_t i = 0; i < plugins_count; i++) {
		if (plugins[i].handle) dlclose(plugins[i].handle);
		free(plugins[i].path);
	}
	plugins_count = 0;
}

// Сбор всех опций от плагинов
int collect_all_plugin_options(void) {
	size_t total_opts = 0;
	for (size_t i = 0; i < plugins_count; i++)
		total_opts += plugins[i].info.sup_opts_len;
	if (total_opts == 0) {
		fprintf(stderr, "No plugin options found\n");
		return -1;
	}
	all_plugin_options = calloc(total_opts + 1, sizeof(struct option)); // +1 для завершающего {0}
	if (!all_plugin_options) {
		fprintf(stderr, "Memory allocation failed\n");
		return -1;
	}
	size_t idx = 0;
	for (size_t i = 0; i < plugins_count; i++)
		for (size_t j = 0; j < plugins[i].info.sup_opts_len; j++)
			all_plugin_options[idx++] = plugins[i].info.sup_opts[j].opt;
	all_plugin_options[total_opts] = (struct option){0}; // Завершающий нулевой элемент
	all_plugin_options_count = total_opts;
	return 0;
}

// Проверка на конфликты опций
int check_option_conflicts(void) {
	for (size_t i = 0; i < all_plugin_options_count; i++)
		for (size_t j = i + 1; j < all_plugin_options_count; j++)
			if (strcmp(all_plugin_options[i].name, all_plugin_options[j].name) == 0) {
				fprintf(stderr, "Option name conflict: --%s\n", all_plugin_options[i].name);
				return -1;
			}
	return 0;
}

int parse_command_line(int argc, char *argv[]) {
	static struct option base_options[] = {
		{"P", required_argument, NULL, 'P'},
		{"A", no_argument, NULL, 'A'},
		{"O", no_argument, NULL, 'O'},
		{"N", no_argument, NULL, 'N'},
		{"v", no_argument, NULL, 'v'},
		{"h", no_argument, NULL, 'h'},
		{0, 0, 0, 0}
	};
	int opt, option_index;
    opterr = 0;
	int count_A = 0, count_O = 0;
	// Разбираем только базовые опции, неизвестные игнорируем
	while ((opt = getopt_long(argc, argv, "P:AONvh", base_options, &option_index)) != -1) {
		switch (opt) { case 'P': free(plugin_dir); plugin_dir = strdup(optarg); break;
			case 'A': combine_and = 1; combine_or = 0; count_A++; break;
			case 'O': combine_or = 1; combine_and = 0; count_O++; break;
			case 'N': invert_result = 1; break;
			case 'v': show_version = 1;	break;
			case 'h': show_help = 1; break;
			case '?': if (optopt != 0) { fprintf(stderr, "Unknown option: -%c\n", optopt); print_help(); return -1;
                            } else { break; }
			default: fprintf(stderr, "Unknown option\n"); return -1;
		}
	}
	if (count_A > 0 && count_O > 0) {
		fprintf(stderr, "Error: options -A and -O cannot be used together\n");
		return -1;
	}
	if (optind < argc) start_dir = argv[optind];
	return 0;
}

// Обход файловой системы: вызывается для каждого файла/каталога
int nftw_callback(const char *fpath, const struct stat *sb, int typeflag, struct FTW *ftwbuf) {
	(void) sb;	(void) ftwbuf;
	if (typeflag == FTW_SL) {
		debug_printf("Ignoring symlink: %s\n", fpath);
		return 0;
	}
	if (typeflag == FTW_F) {
		int match = 1;
		// Обработка файла каждым подключённым плагином
		for (size_t i = 0; i < plugins_count; i++) {
			int (*plugin_process_file)(const char *, struct option *, size_t) =
				dlsym(plugins[i].handle, "plugin_process_file");
			if (!plugin_process_file) {
				fprintf(stderr, "plugin_process_file not found in plugin '%s'\n", plugins[i].path);
				return -1;
			}
			// Выбор только тех опций, которые поддерживает данный плагин
			size_t plugin_opts_len = plugins[i].info.sup_opts_len;
			struct option *plugin_opts = calloc(plugin_opts_len, sizeof(struct option));
			if (!plugin_opts) {
				fprintf(stderr, "Memory allocation failed\n");
				return -1;
			}
			size_t count = 0;
			for (size_t j = 0; j < global_opts_len; j++) {
				for (size_t k = 0; k < plugin_opts_len; k++) {
					if (strcmp(global_opts[j].name, plugins[i].info.sup_opts[k].opt.name) == 0) {
						plugin_opts[count++] = global_opts[j];
						break;
					}
				}
			}
			// Вызов функции плагина
			int pres = plugin_process_file(fpath, plugin_opts, count);
			free(plugin_opts);

			if (pres < 0) {
				if (debug_enabled)
					fprintf(stderr, "Plugin '%s' error on '%s': %s\n", plugins[i].path, fpath, strerror(errno));
				return -1;
			}
			if (combine_and)
				match = match && (pres == 0);
			else if (combine_or)
				match = match || (pres == 0);
		}
		if (invert_result)
			match = !match;
		if (match)
			printf("%s\n", fpath);
	}
	return 0;
}

// Запуск обхода с использованием nftw()
int recursive_search(const char *dir_path, struct option *opts, size_t opts_len) {
	global_opts = opts;
	global_opts_len = opts_len;
	int flags = FTW_PHYS;	 // Не следовать по символическим ссылкам
	int max_fd = 20;		  // Максимум одновременно открытых файловых дескрипторов
	return nftw(dir_path, nftw_callback, max_fd, flags);
}