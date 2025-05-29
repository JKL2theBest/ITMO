#include "utils.h"

int main(int argc, char *argv[]) {
	if (getenv("LAB1DEBUG")) debug_enabled = 1;
	int ret = EXIT_SUCCESS;
	// Каталог плагинов: по умолчанию каталог исполняемого файла
	char exe_path[PATH_MAX];
	ssize_t len = readlink("/proc/self/exe", exe_path, sizeof(exe_path) - 1);
	if (len != -1) {
		exe_path[len] = '\0';
		char *last_slash = strrchr(exe_path, '/');
		if (last_slash) *last_slash = '\0';
		else strcpy(exe_path, ".");
		plugin_dir = strdup(exe_path);
	} else { plugin_dir = strdup("."); }

	// Первичный парсинг базовых опций
	if (parse_command_line(argc, argv) != 0) { free(plugin_dir); return EXIT_FAILURE; }
	if (show_version) {	print_version(); free(plugin_dir); return EXIT_SUCCESS; }
	if (show_help || !start_dir) { print_help(); free(plugin_dir); return EXIT_SUCCESS; }

	// Собираем все --длинные опции из argv[]
	for (int i = 1; i < argc; i++) {
	    if (strncmp(argv[i], "--", 2) == 0) {
	        char *eq = strchr(argv[i] + 2, '=');
	        size_t len = eq ? (size_t)(eq - (argv[i] + 2)) : strlen(argv[i] + 2);
	        if (passed_long_opts_count < MAX_PASSED_OPTS) {
	            passed_long_opts[passed_long_opts_count++] = strndup(argv[i] + 2, len);
	        }
	    }
	}

	// Загрузка плагинов
	if (load_plugins(plugin_dir) != 0) { free(plugin_dir); return EXIT_FAILURE; }
	// Сразу показываем, какие плагины загрузились
	print_loaded_plugins();
	// Сбор всех опций из плагинов
	if (collect_all_plugin_options() != 0) { unload_plugins(); free(plugin_dir); return EXIT_FAILURE; }
	// Проверка на конфликты между опциями
	if (check_option_conflicts() != 0) { unload_plugins(); free(all_plugin_options); free(plugin_dir); return EXIT_FAILURE; }
	// Массив указателей на значения опций плагинов
	char **plugin_opt_args = calloc(all_plugin_options_count, sizeof(char *));
	if (!plugin_opt_args) {
		fprintf(stderr, "Memory allocation failed\n");
		unload_plugins();
		free(all_plugin_options);
		free(plugin_dir);
		return EXIT_FAILURE;
	}
	// Подготовка объединённого списка опций: базовые + плагиновые
	size_t base_opts_len = 6;
	struct option *combined_options = calloc(base_opts_len + all_plugin_options_count + 1, sizeof(struct option));
	if (!combined_options) {
		fprintf(stderr, "Memory allocation failed\n");
		free(plugin_opt_args);
		unload_plugins();
		free(all_plugin_options);
		free(plugin_dir);
		return EXIT_FAILURE;
	}
	struct option base_options[] = {
		{"P",	required_argument, NULL, 'P'},
		{"A",	no_argument,	   NULL, 'A'},
		{"O",	no_argument,	   NULL, 'O'},
		{"N",	no_argument,	   NULL, 'N'},
		{"v",	no_argument,	   NULL, 'v'},
		{"h",	no_argument,	   NULL, 'h'}
	};
	memcpy(combined_options, base_options, sizeof(base_options));
	for (size_t i = 0; i < all_plugin_options_count; i++) {
		combined_options[base_opts_len + i] = all_plugin_options[i];
		combined_options[base_opts_len + i].val = 256 + (int)i;
	}

	// Повторный парсинг опций с учётом опций плагинов
	optind = 1;
	int opt, option_index;
	int count_A = 0, count_O = 0;
	while ((opt = getopt_long(argc, argv, "P:AONvh", combined_options, &option_index)) != -1) {
		size_t plugin_idx = opt - 256;
		if (plugin_idx < all_plugin_options_count) {
			if (combined_options[base_opts_len + plugin_idx].has_arg == required_argument) {
				if (!optarg) {
					fprintf(stderr, "Missing argument for --%s\n", combined_options[base_opts_len + plugin_idx].name);
					goto fail;
				}
				plugin_opt_args[plugin_idx] = strdup(optarg);
			} else { plugin_opt_args[plugin_idx] = strdup("1"); }
		}
	}

	if (count_A > 0 && count_O > 0) {
		fprintf(stderr, "Error: -A and -O cannot be used together\n");
		goto fail;
	}
	if (optind < argc) start_dir = argv[optind];
	int passed_long = 0;
	for (int i = 1; i < optind; i++) {
		if (strncmp(argv[i], "--", 2) == 0) {
			passed_long++;
		}
	}
	// подсчитать, сколько из них (опций) распознано
	int recognized = 0;
	for (size_t i = 0; i < all_plugin_options_count; i++) {
		if (plugin_opt_args[i] != NULL) {
			recognized++;
		}
	}
	if (passed_long > recognized) {
		fprintf(stderr,
			"Error: unsupported option(s): passed %d plugin options, but only %d supported\n",
			passed_long, recognized);
		goto fail;
	}
	for (size_t i = 0; i < all_plugin_options_count; i++) {
		if (all_plugin_options[i].has_arg == required_argument && (!plugin_opt_args[i] || plugin_opt_args[i][0] == '\0')) {
			fprintf(stderr, "Missing argument for plugin(s)");
			goto fail;
		}
		all_plugin_options[i].flag = (int *)plugin_opt_args[i];
	}


	fprintf(stderr, "Parsed options:\n");
	if (plugin_dir)	fprintf(stderr, "  -P plugin_dir = %s\n", plugin_dir);
	fprintf(stderr, "  -A = %s\n", combine_and ? "true" : "false");
	fprintf(stderr, "  -O = %s\n", combine_or  ? "true" : "false");
	fprintf(stderr, "  -N = %s\n", invert_result ? "true" : "false");
	fprintf(stderr, "  -v = %s\n", show_version  ? "true" : "false");
	fprintf(stderr, "  -h = %s\n", show_help	 ? "true" : "false");

	for (size_t i = 0; i < all_plugin_options_count; ++i) {
		const char *name = all_plugin_options[i].name;
		const char *val  = plugin_opt_args[i];
		if (val) {
			fprintf(stderr, "  --%s = %s\n", name, val);
		} else { // no_argument
			// опция-флаг: покажем явно, даже если val == NULL
			fprintf(stderr, "  --%s = %s\n", name, "null");
		}
	}
	fprintf(stderr, "\n");

	if (optind < argc) start_dir = argv[optind]; // развернуть start_dir в абсолютный путь
   {
	   char buf[PATH_MAX];
	   if (!realpath(start_dir, buf)) {
		   fprintf(stderr, "Error: cannot resolve '%s': %s\n",
				   start_dir, strerror(errno));
		   goto fail;
	   }
	   start_dir = strdup(buf);
   }
	// Запуск поиска
	int result = recursive_search(start_dir, all_plugin_options, all_plugin_options_count);
	if (result != 0)
		ret = EXIT_FAILURE;

cleanup:
	for (size_t i = 0; i < passed_long_opts_count; ++i) {
	    free(passed_long_opts[i]);
	}
	unload_plugins();
	if (plugin_opt_args) {
		for (size_t i = 0; i < all_plugin_options_count; i++)
			free(plugin_opt_args[i]);
		free(plugin_opt_args);
	}
	free(combined_options);
	free(all_plugin_options);
	free(plugin_dir);
	if (start_dir && start_dir != argv[optind]) free(start_dir);
	return ret;

fail:
	ret = EXIT_FAILURE;
	goto cleanup;
}