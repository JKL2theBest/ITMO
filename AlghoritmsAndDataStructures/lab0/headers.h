#ifndef HEADERS_H
#define HEADERS_H

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <ctype.h>
#include <string.h>

#define EPSILON_DEFAULT 0.0001
#define TINY_VALUE 1e-10
#define INPUT_LIMIT 16

typedef struct {
    double real;
    double imag;
    int is_complex;
} Root;

void clear_stdin() {
    int c;
    while ((c = getchar()) != '\n' && c != EOF);
}

int is_input_too_long(const char *buffer) {
    if (buffer[strlen(buffer) - 1] != '\n') {
        printf("Ошибка: введено слишком длинное число.\n");
        clear_stdin();
        return 1;
    }
    return 0;
}

int is_empty_or_whitespace(const char *str) {
    while (*str) {
        if (!isspace((unsigned char)*str)) return 0;
        str++;
    }
    return 1;
}

int is_invalid_number(const char *endptr) {
    while (isspace((unsigned char)*endptr)) endptr++;
    return *endptr != '\0' && *endptr != '\n';
}

double check_tiny_value(double value) {
    if (fabs(value) < TINY_VALUE && value != 0) {
        printf("Предупреждение: число %.5e слишком мало, заменено на 0.\n", value);
        return 0.0;
    }
    return value;
}

double safe_input(const char *prompt) {
    char buffer[INPUT_LIMIT + 2];
    char *endptr;
    double value;
    while (1) {
        printf("%s", prompt);
        if (fgets(buffer, sizeof(buffer), stdin) == NULL) {
            printf("\nВвод прерван пользователем.\n");
            exit(0);
        }
        if (is_input_too_long(buffer)) continue;
        if (is_empty_or_whitespace(buffer)) {
            printf("Ошибка: ввод не должен быть пустым. Повторите ввод.\n");
            continue;
        }
        value = strtod(buffer, &endptr);
        if (is_invalid_number(endptr)) {
            printf("Некорректный ввод. Введите одно число.\n");
            continue;
        }
        if (!isfinite(value)) {
            printf("Ошибка: введено недопустимое значение.\n");
            continue;
        }
        return check_tiny_value(value);
    }
}

void print_number(double value) {
    if (fabs(value) < TINY_VALUE) value = 0.0;
    if (value == (int)value) {
        printf("%d", (int)value);
    } else {
        printf("%.4f", value);
    }
}

void solve_linear(double c, double d) {
    if (c == 0) {
        printf(d == 0 ? "\nРешение – любое число.\n" : "\nРешений нет.\n");
    } else {
        printf("\nРешение линейного уравнения:\nx = %.4f\n", -d / c);
    }
}

double round_to_4(double value) {
    return round(value * 10000.0) / 10000.0;
}

void solve_quadratic(double a, double b, double c, double epsilon) {
    double D = round_to_4(b * b - 4 * a * c);
    if (D > 0) {
        double sqrt_D = sqrt(D);
        double x1 = round_to_4((-b + sqrt_D) / (2 * a));
        double x2 = round_to_4((-b - sqrt_D) / (2 * a));
        if (fabs(x1) <= epsilon) x1 = 0.0;
        if (fabs(x2) <= epsilon) x2 = 0.0;
        printf("\nКорни квадратного уравнения:\nx1 = %.4f\nx2 = %.4f\n\n", x1, x2);
    } else if (D == 0) {
        double x = round_to_4(-b / (2 * a));
        if (fabs(x) <= epsilon) x = 0.0;
        printf("\nКорень квадратного уравнения:\nx1 = %.4f\n\n", x);
    } else {
        double real = round_to_4(-b / (2 * a));
        double imag = round_to_4(sqrt(-D) / (2 * a));
        if (fabs(real) <= epsilon) real = 0.0;
        if (fabs(imag) <= epsilon) imag = 0.0;
        printf("\nКомплексные корни квадратного уравнения:\nx1 = %.4f + %.4f*i\nx2 = %.4f - %.4f*i\n\n", real, imag, real, imag);
    }
}

double cubic_function(double a, double b, double c, double d, double x) {
    return a * x * x * x + b * x * x + c * x + d;
}

double cubic_derivative(double a, double b, double c, double x) {
    return 3 * a * x * x + 2 * b * x + c;
}

void find_root_interval(double a, double b, double c, double d, double *x1, double *x2) {
    double D = b * b - 3 * a * c;
    double left, right;
    if (D >= 0) {
        double sqrt_D = sqrt(D);
        double x_crit1 = (-b + sqrt_D) / (3 * a);
        double x_crit2 = (-b - sqrt_D) / (3 * a);
        if (x_crit1 > x_crit2) {
            double temp = x_crit1;
            x_crit1 = x_crit2;
            x_crit2 = temp;
        }
        left = x_crit1;
        right = x_crit2;
    } else {
        left = -0.5;
        right = 0.5;
    }
    // Проверка смены знака
    double f_left = cubic_function(a, b, c, d, left);
    double f_right = cubic_function(a, b, c, d, right);
    int max_iterations = 10000;
    while (f_left * f_right > 0 && max_iterations-- > 0) {
        left -= 0.1;
        right += 0.1;
        f_left = cubic_function(a, b, c, d, left);
        f_right = cubic_function(a, b, c, d, right);
        if (fabs(left) > 1e6 || fabs(right) > 1e6) {
            printf("Ошибка: не удалось найти интервал с изменением знака.\n");
            *x1 = -10;
            *x2 = 10;
            return;
        }
    }
    *x1 = left -0.5;
    *x2 = right +0.5;
}

double chord_method(double a, double b, double c, double d, double x0, double xn) {
    double fx0 = cubic_function(a, b, c, d, x0);
    double fxn = cubic_function(a, b, c, d, xn);
    return xn - fxn * (xn - x0) / (fxn - fx0);
}

double tangent_method(double a, double b, double c, double d, double xn) {
    double fxn = cubic_function(a, b, c, d, xn);
    double fpxn = cubic_derivative(a, b, c, xn);
    if (fabs(fpxn) < TINY_VALUE) {
        printf("Ошибка: производная функции близка к нулю, не удается продолжить метод касательных.\n");
        return xn;  // Избегаем деление на ноль
    }
    return xn - fxn / fpxn;
}

double validate_epsilon(double epsilon) {
    if (!isfinite(epsilon) || epsilon <= 0) {
        printf("Введена пустая строка или недопустимое значение. Используется значение по умолчанию %.4f.\n", EPSILON_DEFAULT);
        return EPSILON_DEFAULT;
    }
    if (fabs(epsilon) < TINY_VALUE) {
        printf("Предупреждение: epsilon %.5e слишком мал, заменено на %.4f.\n", epsilon, EPSILON_DEFAULT);
        return EPSILON_DEFAULT;
    }
    if (epsilon >= 1) {
        printf("Ошибка: epsilon должен быть меньше 1. Используется значение по умолчанию %.4f.\n", EPSILON_DEFAULT);
        return EPSILON_DEFAULT;
    }
    return epsilon;
}

double input_epsilon() {
    char buffer[INPUT_LIMIT + 2];
    char *endptr;
    double epsilon;
    printf("Введите точность epsilon (по умолчанию %.4f): ", EPSILON_DEFAULT);
    if (fgets(buffer, sizeof(buffer), stdin) == NULL) {
        printf("\nВвод прерван пользователем.\n");
        exit(0);
    }
    if (is_input_too_long(buffer)) {
        printf("Заменено на %.4f.\n", EPSILON_DEFAULT);
        return EPSILON_DEFAULT;
    }
    epsilon = strtod(buffer, &endptr);
    if (is_invalid_number(endptr)) {
        printf("Некорректный ввод. Используется значение по умолчанию %.4f.\n", EPSILON_DEFAULT);
        return EPSILON_DEFAULT;
    }
    return validate_epsilon(epsilon);
}

// Основная функция решения кубического уравнения методом хорд и касательных
void solve_cubic(double a, double b, double c, double d, double epsilon, double *root) {
    double x0, xn, x_chord, x_tangent, x_new;
    int iteration = 0;
    find_root_interval(a, b, c, d, &x0, &xn);
    x_chord = chord_method(a, b, c, d, x0, xn);
    x_tangent = tangent_method(a, b, c, d, xn);
    x_new = (x_chord + x_tangent) / 2;
    do {
        x0 = x_chord;
        xn = x_tangent;
        x_chord = chord_method(a, b, c, d, x0, xn);
        x_tangent = tangent_method(a, b, c, d, xn);
        x_new = (x_chord + x_tangent) / 2;
        x_new = round_to_4(x_new); // Гарантированное округление на каждой итерации
        if (fabs(x_new) <= epsilon) {
            x_new = 0.0; // Принудительное округление к 0
        }
        iteration++;
        printf("Отрезок [%.4f; %.4f]\n", x0, xn);
    } while (fabs(x_new - x0) > epsilon && fabs(x_new - xn) > epsilon);
        x_new = round_to_4(x_new); // Финальное округление перед выводом
    if (fabs(x_new) <= epsilon) {
        x_new = 0.0;
    }

    printf("Всего итераций: %d\n", iteration);
    printf("\nНайденное приближение корня:\nx = %.4f\n\n", x_new);
    *root = x_new;
}

void horner(double a, double b, double c, double root, double *new_a, double *new_b, double *new_c, double epsilon) {
    *new_a = a;
    *new_b = round_to_4((*new_a) * root + b);
    if (fabs(*new_b) <= epsilon) *new_b = 0.0; // Устранение ложных комплексных корней
    *new_c = round_to_4((*new_b) * root + c);
    if (fabs(*new_c) <= epsilon) *new_c = 0.0;
}

int compare_roots(const void *a, const void *b) {
    const Root *ra = (const Root *)a;
    const Root *rb = (const Root *)b;
    if (ra->real < rb->real) return -1;
    if (ra->real > rb->real) return 1;
    return 0;
}

#endif
