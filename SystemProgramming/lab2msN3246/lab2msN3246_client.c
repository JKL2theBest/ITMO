#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <getopt.h>
#include <stdarg.h>

#define DEFAULT_ADDR "127.0.0.1"
#define DEFAULT_PORT "7777"
#define VERSION "lab2msN3246_client 1.0\nAuthor: Суханкулиев Мухаммет\nGroup: N3246\nПоток: ОСП N23 1.2\nVariant: 2\n"

static int debug_enabled = 0;

static void print_help(const char *prog) {
    fprintf(stdout,
        "Usage: %s [options] [\"numbers\"] [rounding]\n"
        "Options:\n"
        "  -a ip      IP address of server (env LAB2ADDR), default %s\n"
        "  -p port    Port of server (env LAB2PORT), default %s\n"
        "  -v         Print version and student information\n"
        "  -h         Print this help\n\n"
        "If numbers and rounding are not given as arguments, input is read from stdin.\n"
        "Rounding options: floor, ceil, trunc\n"
        , prog, DEFAULT_ADDR, DEFAULT_PORT);
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
// Валидность IPv4
//
static int validate_ip(const char *ip) {
    struct sockaddr_in sa;
    return inet_pton(AF_INET, ip, &(sa.sin_addr)) == 1;
}

static int validate_port(const char *port_str) {
    char *endptr;
    long port = strtol(port_str, &endptr, 10);
    if (*endptr != '\0' || port < 1 || port > 65535) return 0;
    return 1;
}

//
// Возвращает преобразованную строку без пробельных символов
// p.s. на сервере тоже обрабатывается
//
static char *read_line(FILE *f) {
    size_t size = 256;
    size_t len = 0;
    char *buf = malloc(size);
    if (!buf) return NULL;

    while (1) {
        if (fgets(buf + len, (int)(size - len), f) == NULL) {
            if (len == 0) {
                free(buf);
                return NULL;
            }
            break;
        }
        len += strlen(buf + len);
        if (len > 0 && buf[len - 1] == '\n') {
            buf[len - 1] = '\0';  // Удалить завершающую новую строку
            break;
        }
        // Увеличить буффер
        if (len == size - 1) {
            size *= 2;
            char *tmp = realloc(buf, size);
            if (!tmp) {
                free(buf);
                return NULL;
            }
            buf = tmp;
        }
    }
    return buf;
}

int main(int argc, char *argv[]) {
    // Получить переменные окружения, если заданы
    const char *ip = getenv("LAB2ADDR");
    if (!ip) ip = DEFAULT_ADDR;
    const char *port = getenv("LAB2PORT");
    if (!port) port = DEFAULT_PORT;
    const char *debug_env = getenv("LAB2DEBUG");
    debug_enabled = (debug_env != NULL && strlen(debug_env) > 0);

    int opt;
    while ((opt = getopt(argc, argv, "a:p:vh")) != -1) {
        switch (opt) {
            case 'a':
                ip = optarg;
                break;
            case 'p':
                port = optarg;
                break;
            case 'v':
                printf("Version %s\n", VERSION);
                return 0;
            case 'h':
                print_help(argv[0]);
                return 0;
            default:
                fprintf(stderr, "Unknown option\n");
                print_help(argv[0]);
                return 1;
        }
    }

    debug_printf("Debug mode enabled");
    debug_printf("Using IP=%s, port=%s", ip, port);

    if (!validate_ip(ip)) {
        fprintf(stderr, "Invalid IP address: %s\n", ip);
        return 1;
    }
    if (!validate_port(port)) {
        fprintf(stderr, "Invalid port: %s\n", port);
        return 1;
    }

    // Прочесть входные строки
    char *numbers_line = NULL;
    char *rounding_line = NULL;

    int remaining_args = argc - optind;

    if (remaining_args > 2) {
        fprintf(stderr, "Warning: too many arguments provided, only first two will be used.\n");
    }
    if (remaining_args >= 2) {
        numbers_line = strdup(argv[optind]);
        rounding_line = strdup(argv[optind + 1]);
        if (!numbers_line || !rounding_line) {
            fprintf(stderr, "Memory allocation failed\n");
            free(numbers_line);
            free(rounding_line);
            return 1;
        }
    } else if (remaining_args == 1) {
        // Числа из первого аргумента, округление из stdin
        numbers_line = strdup(argv[optind]);
        if (!numbers_line) {
            fprintf(stderr, "Memory allocation failed\n");
            return 1;
        }
        debug_printf("Enter rounding line\n        floor (в сторону минус бесконечности),\n        ceil (в сторону плюс бесконечности),\n        trunc (в сторону нуля):\n");
        rounding_line = read_line(stdin);
        if (!rounding_line) {
            fprintf(stderr, "Failed to read rounding line\n");
            free(numbers_line);
            return 1;
        }
    } else {
        debug_printf("Enter numbers line:\n");
        numbers_line = read_line(stdin);
        if (!numbers_line) {
            fprintf(stderr, "Failed to read numbers line\n");
            return 1;
        }
        debug_printf("Enter rounding line\n        floor (в сторону минус бесконечности),\n        ceil (в сторону плюс бесконечности),\n        trunc (в сторону нуля):\n");
        rounding_line = read_line(stdin);
        if (!rounding_line) {
            fprintf(stderr, "Failed to read rounding line\n");
            free(numbers_line);
            return 1;
        }
    }

    debug_printf("Numbers line: '%s'", numbers_line);
    debug_printf("Rounding line: '%s'", rounding_line);

    // Подготовка к подключению
    struct addrinfo hints = {0}, *res = NULL;
    hints.ai_family = AF_INET;       // IPv4
    hints.ai_socktype = SOCK_STREAM; // TCP

    int gai_err = getaddrinfo(ip, port, &hints, &res);
    if (gai_err != 0) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(gai_err));
        free(numbers_line);
        free(rounding_line);
        return 1;
    }

    // Подключение
    int sock = -1;
    for (struct addrinfo *p = res; p != NULL; p = p->ai_next) {
        sock = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
        if (sock == -1) continue;

        if (connect(sock, p->ai_addr, p->ai_addrlen) == 0) {
            debug_printf("Connected to server");
            break;
        }
        close(sock);
        sock = -1;
    }
    freeaddrinfo(res);

    if (sock == -1) {
        fprintf(stderr, "Failed to connect to %s:%s\n", ip, port);
        free(numbers_line);
        free(rounding_line);
        return 1;
    }

    // Подготовка в отправке запроса
    size_t req_len = strlen(numbers_line) + strlen(rounding_line) + 2;
    char *request = malloc(req_len + 1);
    if (!request) {
        fprintf(stderr, "Memory allocation failed\n");
        free(numbers_line);
        free(rounding_line);
        close(sock);
        return 1;
    }
    snprintf(request, req_len + 1, "%s\n%s\n", numbers_line, rounding_line);

    debug_printf("Sending request:\n%s", request);

    // Отправка
    ssize_t sent = 0;
    size_t to_send = req_len;
    while (to_send > 0) {
        ssize_t n = send(sock, request + sent, to_send, 0);
        if (n <= 0) {
            fprintf(stderr, "Send error: %s\n", strerror(errno));
            free(numbers_line);
            free(rounding_line);
            free(request);
            close(sock);
            return 1;
        }
        sent += n;
        to_send -= n;
    }

    free(numbers_line);
    free(rounding_line);
    free(request);

    // Получить от сервера
    size_t bufsize = 256;
    size_t pos = 0;
    char *response = malloc(bufsize);
    if (!response) {
        fprintf(stderr, "Memory allocation failed\n");
        close(sock);
        return 1;
    }

    while (1) {
        ssize_t n = recv(sock, response + pos, 1, 0);
        if (n <= 0) {
            if (n == 0)
                fprintf(stderr, "Connection closed by server unexpectedly\n");
            else
                fprintf(stderr, "Recv error: %s\n", strerror(errno));
            free(response);
            close(sock);
            return 1;
        }
        if (response[pos] == '\n') {
            response[pos] = '\0';
            break;
        }
        pos++;
        if (pos + 1 >= bufsize) {
            bufsize *= 2;
            char *tmp = realloc(response, bufsize);
            if (!tmp) {
                fprintf(stderr, "Memory allocation failed\n");
                free(response);
                close(sock);
                return 1;
            }
            response = tmp;
        }
    }

    close(sock);
    debug_printf("Connection closed");

    // Вывести ответ сервера в stdout
    printf("%s\n", response);

    if (debug_enabled) {
        fprintf(stderr, "[DEBUG] Received response: %s\n", response);
    }

    free(response);
    return 0;
}
