#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <ctype.h>
#include <errno.h>
#include <time.h>
#include <unistd.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/wait.h>
#include <math.h>
#include <stdarg.h>

#define DEFAULT_ADDR "127.0.0.1"
#define DEFAULT_PORT 7777
#define DEFAULT_LOGFILE "/tmp/lab2.log"
#define VERSION "lab2msN3246_server 1.0\nAuthor: Суханкулиев Мухаммет\nGroup: N3246\nПоток: ОСП N23 1.2\nVariant: 2\n"

// Для обработки сигналов
static volatile sig_atomic_t stop_flag = 0;
static volatile sig_atomic_t print_stats_flag = 0;

// Логгирование
static FILE *log_file = NULL;
static int debug_enabled = 0;
static unsigned long successful_requests = 0;
static unsigned long error_requests = 0;
static time_t server_start_time;

// Опции сервера
static unsigned int wait_seconds = 0; // DEFAULTWAIT
static int daemon_mode = 0;

static void print_help(const char *prog) {
    fprintf(stderr,
        "Usage: %s [options]\n"
        "Options:\n"
        "  -w N        Wait N seconds before processing request (env LAB2WAIT), default 0\n"
        "  -d          Run as daemon\n"
        "  -l logfile  Log file path (env LAB2LOGFILE), default %s\n"
        "  -a ip       Server listen IP (env LAB2ADDR), default %s\n"
        "  -p port     Server listen port (env LAB2PORT), default %d\n"
        "  -v          Print version and student information\n"
        "  -h          Print this help\n\n"
        "Environment variables:\n"
        "  LAB2ADDR, LAB2PORT, LAB2LOGFILE, LAB2WAIT, LAB2DEBUG\n",
        prog, DEFAULT_LOGFILE, DEFAULT_ADDR, DEFAULT_PORT);
}

static void debug_printf(const char *fmt, ...) {
    if (!debug_enabled) return;
    va_list ap;
    va_start(ap, fmt);
    fprintf(stderr, "[DEBUG] ");
    vfprintf(stderr, fmt, ap);
    fprintf(stderr, "\n");
    va_end(ap);
}

//
// Записать текущее время в формате "дд.мм.гг ЧЧ:ММ:СС"
//
static void timestamp(char *buf, size_t size) {
    time_t now = time(NULL);
    struct tm tm;
    localtime_r(&now, &tm);
    strftime(buf, size, "%d.%m.%y %H:%M:%S", &tm);
}

//
// Запись лога в консоль и в файл
//
static void log_msg(const char *fmt, ...) {
    if (!log_file) return;
    char timebuf[32];
    timestamp(timebuf, sizeof timebuf);

    va_list args;

    fprintf(log_file, "[%s] ", timebuf);
    va_start(args, fmt);
    vfprintf(log_file, fmt, args);
    va_end(args);
    fprintf(log_file, "\n");
    fflush(log_file);

    printf("[%s] ", timebuf);
    va_start(args, fmt);
    vprintf(fmt, args);
    va_end(args);
    printf("\n");
    fflush(stdout);
}

//
// Логгирование ошибки
//
static void log_error(const char *fmt, ...) {
    if (!log_file) return;
    char timebuf[32];
    timestamp(timebuf, sizeof timebuf);

    va_list args;

    fprintf(log_file, "[%s] ERROR: ", timebuf);
    va_start(args, fmt);
    vfprintf(log_file, fmt, args);
    va_end(args);
    fprintf(log_file, "\n");
    fflush(log_file);

    fprintf(stderr, "[%s] ERROR: ", timebuf);
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);
    fprintf(stderr, "\n");
    fflush(stderr);
}

//
// Обработчик сигнала для убийства детей (child processes)
//
void reap_children(int signo) {
    (void)signo;
    int status;
    pid_t pid;
    while ((pid = waitpid(-1, &status, WNOHANG)) > 0) {
        if (debug_enabled) {
            log_msg("[DEBUG] Reaped child process pid=%d", pid);
        }
    }
}

//
// Обработчик SIGINT, SIGTERM, SIGQUIT
//
void termination_handler(int signo) {
    (void)signo;
    stop_flag = 1;
}

//
// Обработчик SIGUSR1
//
void sigusr1_handler(int signo) {
    (void)signo;
    print_stats_flag = 1;
}

//
// Донастройка обработчиков
//
void setup_signal_handlers() {
    struct sigaction sa;

    // SIGINT, SIGTERM, SIGQUIT для выключения
    sa.sa_handler = termination_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGQUIT, &sa, NULL);

    // SIGUSR1 чтобы вывести статистику
    sa.sa_handler = sigusr1_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGUSR1, &sa, NULL);

    // SIGCHLD РИПнуть детей
    sa.sa_handler = reap_children;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART | SA_NOCLDSTOP;
    sigaction(SIGCHLD, &sa, NULL);
}

void print_stats() {
    time_t now = time(NULL);
    unsigned long uptime = now - server_start_time;

    fprintf(stderr, "=== Server statistics ===\n");
    fprintf(stderr, "Uptime: %lu seconds\n", uptime);
    fprintf(stderr, "Successful requests: %lu\n", successful_requests);
    fprintf(stderr, "Error requests: %lu\n", error_requests);
    fprintf(stderr, "=========================\n");
    fflush(stderr);
}

//
// Демонизация с помощью fork и перенаправления stdio в /dev/null
//
static void daemonize(void) {
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        exit(EXIT_FAILURE);
    }
    if (pid > 0) {
        exit(EXIT_SUCCESS);
    }
    if (setsid() < 0) {
        perror("setsid");
        exit(EXIT_FAILURE);
    }
    freopen("/dev/null", "r", stdin);
    freopen("/dev/null", "w", stdout);
    freopen("/dev/null", "w", stderr);
}

static void open_log_file(const char *path) {
    if (log_file) fclose(log_file);
    log_file = fopen(path, "a");
    if (!log_file) {
        fprintf(stderr, "ERROR: cannot open log file %s: %s\n", path, strerror(errno));
        exit(EXIT_FAILURE);
    }
}

//
// Проверка на пробельные символы
//
static int is_lab2_space(char c) {
    return c == 0x20 || c == 0x09 || c == 0x0B || c == 0x0C || c == 0x0D;
}

//
// Обработка строки чисел
//
static double* parse_numbers(const char *line, size_t *count) {
    if (!line || !count) return NULL;

    const char *p = line;
    while (*p && is_lab2_space(*p)) p++;
    if (*p == '\0' || *p == '\n') {
        // Пустая строка
        return NULL;
    }

    size_t capacity = 8;
    double *numbers = malloc(capacity * sizeof(double));
    if (!numbers) return NULL;

    *count = 0;

    while (*p) {
        while (*p && is_lab2_space(*p)) p++;
        if (!*p || *p == '\n') break;

        char *endptr;
        errno = 0;
        double val = strtod(p, &endptr);
        if (p == endptr) {
            free(numbers);
            return NULL;
        }
        if (errno == ERANGE) {
            free(numbers);
            return NULL;
        }
        if (*endptr && !is_lab2_space(*endptr) && *endptr != '\n') {
            free(numbers);
            return NULL; // Инвалидный характер
        }

        if (*count >= capacity) {
            capacity *= 2;
            double *tmp = realloc(numbers, capacity * sizeof(double));
            if (!tmp) {
                free(numbers);
                return NULL;
            }
            numbers = tmp;
        }
        numbers[*count] = val;
        (*count)++;

        p = endptr;
    }
    return numbers;
}

//
// Способы округления
//
enum RoundMode { ROUND_FLOOR, ROUND_CEIL, ROUND_TRUNC };

//
// Обработка второй строки
//
static int parse_round_mode(const char *line, enum RoundMode *mode) {
    if (!line || !mode) return -1;

    char buf[64];
    size_t len = strlen(line);
    if (len >= sizeof(buf)) return -1;
    size_t j = 0;
    for (size_t i = 0; i < len; i++) {
        if (!is_lab2_space(line[i]) && line[i] != '\n') {
            buf[j++] = (char)tolower((unsigned char)line[i]);
        }
    }
    buf[j] = '\0';

    if (strcmp(buf, "floor") == 0) {
        *mode = ROUND_FLOOR;
        return 0;
    }
    if (strcmp(buf, "ceil") == 0) {
        *mode = ROUND_CEIL;
        return 0;
    }
    if (strcmp(buf, "trunc") == 0) {
        *mode = ROUND_TRUNC;
        return 0;
    }
    return -1;
}

static void apply_rounding(double *nums, size_t count, enum RoundMode mode) {
    for (size_t i = 0; i < count; i++) {
        switch (mode) {
            case ROUND_FLOOR: nums[i] = floor(nums[i]); break;
            case ROUND_CEIL:  nums[i] = ceil(nums[i]); break;
            case ROUND_TRUNC: nums[i] = trunc(nums[i]); break;
        }
    }
}

static char* format_response(const double *nums, size_t count) {
    if (!nums) return NULL;

    // Приблизительный размер (max 30 chars per number + spaces + LF)
    size_t bufsize = count * 32 + 2;
    char *resp = malloc(bufsize);
    if (!resp) return NULL;

    size_t offset = 0;
    for (size_t i = 0; i < count; i++) {
        int written = snprintf(resp + offset, bufsize - offset, "%.0f", nums[i]);
        if (written < 0 || (size_t)written >= bufsize - offset) {
            free(resp);
            return NULL;
        }
        offset += (size_t)written;
        if (i + 1 < count) {
            if (offset < bufsize - 1) {
                resp[offset] = ' ';
                offset++;
                resp[offset] = '\0';
            }
        }
    }
    // Добавить завершающий LF (в выводе некрасиво получается, но зато все работает)
    if (offset < bufsize - 1) {
        resp[offset] = '\n';
        offset++;
        resp[offset] = '\0';
    } else {
        free(resp);
        return NULL;
    }
    return resp;
}

//
// ERROR N
//
static char* format_error(int code) {
    char *resp = malloc(32);
    if (!resp) return NULL;
    snprintf(resp, 32, "ERROR %d\n", code);
    return resp;
}

static char* read_line(int sockfd) {
    size_t bufsize = 128;
    char *buffer = malloc(bufsize);
    if (!buffer) return NULL;

    size_t pos = 0;
    while (1) {
        char c;
        ssize_t r = recv(sockfd, &c, 1, 0);
        if (r < 0) {
            free(buffer);
            return NULL;
        }
        if (r == 0) {
            // EOF before LF, treat as end
            break;
        }
        if (c == '\n') {
            buffer[pos] = '\0';
            return buffer;
        }
        buffer[pos++] = c;
        if (pos >= bufsize) {
            bufsize *= 2;
            char *tmp = realloc(buffer, bufsize);
            if (!tmp) {
                free(buffer);
                return NULL;
            }
            buffer = tmp;
        }
    }
    buffer[pos] = '\0';
    return buffer;
}

//
// Обработка клиента
//
static void handle_client(int client_fd) {
    if (wait_seconds > 0) {
        sleep(wait_seconds);
    }

    log_msg("New request accepted by pid %d", getpid());

    // Две строки от клиента
    char *line1 = read_line(client_fd);
    if (!line1) {
        log_error("Failed to read first line");
        debug_printf("read_line(client_fd) returned NULL at first line");
        goto error;
    }
    char *line2 = read_line(client_fd);
    if (!line2) {
        log_error("Failed to read second line");
        free(line1);
        goto error;
    }

    log_msg("Received from client: line1='%s'", line1);
    log_msg("Received from client: line2='%s'", line2);

    // Числа (первая строка)
    size_t count;
    double *numbers = parse_numbers(line1, &count);
    if (!numbers) {
        log_error("Failed to parse numbers");
        free(line1);
        free(line2);
        char *resp = format_error(1);
        if (resp) {
            log_msg("Sending to client: '%s'", resp);
            send(client_fd, resp, strlen(resp), 0);
        }
        free(resp);
        error_requests++;
        goto done;
    }

    // Способ округления (вторая строка)
    enum RoundMode mode;
    if (parse_round_mode(line2, &mode) != 0) {
        log_error("Failed to parse rounding mode");
        free(line1);
        free(line2);
        free(numbers);
        char *resp = format_error(2);
        if (resp) {
            log_msg("Sending to client: '%s'", resp);
            send(client_fd, resp, strlen(resp), 0);
        }
        free(resp);
        error_requests++;
        goto done;
    }

    apply_rounding(numbers, count, mode);

    char *resp = format_response(numbers, count);
    if (!resp) {
        log_error("Failed to format response");
        free(line1);
        free(line2);
        free(numbers);
        char *resp_err = format_error(3);
        if (resp_err) {
            log_msg("Sending to client: '%s'", resp_err);
            send(client_fd, resp_err, strlen(resp_err), 0);
        }
        free(resp_err);
        error_requests++;
        goto done;
    }

    log_msg("Sending to client: '%s'", resp);

    // Отправка пакета
    ssize_t sent = send(client_fd, resp, strlen(resp), 0);
    if (sent < 0) {
        log_error("Failed to send response");
        error_requests++;
    } else {
        successful_requests++;
    }
    free(resp);
    free(numbers);
    free(line1);
    free(line2);

done:
    log_msg("Request processing finished by pid %d", getpid());
    close(client_fd);
    exit(EXIT_SUCCESS);

error:
    close(client_fd);
    exit(EXIT_FAILURE);
}

//
// Это мэйн
//
int main(int argc, char *argv[]) {
    const char *addr = NULL;
    unsigned short port = 0;
    const char *logpath = NULL;

    char *env_addr = getenv("LAB2ADDR");
    char *env_port = getenv("LAB2PORT");
    char *env_logfile = getenv("LAB2LOGFILE");
    char *env_wait = getenv("LAB2WAIT");
    char *env_debug = getenv("LAB2DEBUG");

    if (env_addr && *env_addr) addr = env_addr;
    if (env_port) port = (unsigned short)atoi(env_port);
    if (env_logfile && *env_logfile) logpath = env_logfile;
    if (env_wait) wait_seconds = (unsigned int)atoi(env_wait);
    if (env_debug && (strcmp(env_debug, "1") == 0 || strcasecmp(env_debug, "true") == 0))
        debug_enabled = 1;

    if (!addr) addr = DEFAULT_ADDR;
    if (port == 0) port = DEFAULT_PORT;
    if (!logpath) logpath = DEFAULT_LOGFILE;

    int opt;
    while ((opt = getopt(argc, argv, "a:p:l:w:dvh")) != -1) {
        switch (opt) {
            case 'a': addr = optarg; break;
            case 'p': port = (unsigned short)atoi(optarg); break;
            case 'l': logpath = optarg; break;
            case 'w': wait_seconds = (unsigned int)atoi(optarg); break;
            case 'd': daemon_mode = 1; break;
            case 'v':
                printf("%s\n", VERSION);
                exit(EXIT_SUCCESS);
            case 'h':
            default:
                print_help(argv[0]);
                exit(EXIT_SUCCESS);
        }
    }

    open_log_file(logpath);

    if (daemon_mode) {
        daemonize();
    }

    debug_printf("Debug mode enabled");
    log_msg("Server starting on %s:%u", addr, port);
    server_start_time = time(NULL);

    setup_signal_handlers();

    // Создание сокета
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        log_error("socket() failed: %s", strerror(errno));
        exit(EXIT_FAILURE);
    }

    // Разрешить REUSEADDR
    int optval = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &optval, sizeof(optval)) < 0) {
        log_error("setsockopt() failed: %s", strerror(errno));
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in serv_addr = {0};
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(port);
    if (inet_pton(AF_INET, addr, &serv_addr.sin_addr) != 1) {
        log_error("Invalid IP address: %s", addr);
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    if (bind(server_fd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        log_error("bind() failed: %s", strerror(errno));
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    // Слушать
    if (listen(server_fd, 5) < 0) {
        log_error("listen() failed: %s", strerror(errno));
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    log_msg("Server listening...");

    // Мэйн цикл
    while (!stop_flag) {
        if (print_stats_flag) {
            print_stats();
            print_stats_flag = 0;
        }

        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);
        int client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);
        if (client_fd < 0) {
            if (errno == EINTR) continue;
            log_error("accept() failed: %s", strerror(errno));
            break;
        }

        pid_t pid = fork();
        if (pid < 0) {
            log_error("fork() failed: %s", strerror(errno));
            close(client_fd);
            continue;
        } else if (pid == 0) {
            // Обработка клиента дочерним процессом (ребенком)
            close(server_fd);
            handle_client(client_fd);
            close(client_fd);
            exit(EXIT_SUCCESS);
        } else {
            // Родитель закрывает ребенка
            close(client_fd);
        }
    }

    log_msg("Server shutting down");
    close(server_fd);
    if (log_file) fclose(log_file);

    return 0;
}
