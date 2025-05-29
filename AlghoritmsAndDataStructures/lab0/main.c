#include "headers.h"

int main() {
    while (1) {
        Root roots[3];
        int root_count = 0;
        double a = safe_input("Введите коэффициент a: ");
        double b = safe_input("Введите коэффициент b: ");
        double c = safe_input("Введите коэффициент c: ");
        double d = safe_input("Введите коэффициент d: ");
        printf("Введенное уравнение:\n");
        print_number(a); printf("*x^3 + ");
        print_number(b); printf("*x^2 + ");
        print_number(c); printf("*x + ");
        print_number(d); printf(" = 0\n\n");
        double epsilon = input_epsilon();  // Считать один раз
        if (a == 0) {
            if (b == 0) {
                solve_linear(c, d);
                if (c != 0) {
                    roots[root_count++] = (Root){round_to_4(-d / c), 0, 0};
                }
            } else {
                solve_quadratic(b, c, d, epsilon);
                double D = c * c - 4 * b * d;
                if (D > 0) {
                    double sqrt_D = sqrt(D);
                    double r1 = round_to_4((-c + sqrt_D) / (2 * b));
                    double r2 = round_to_4((-c - sqrt_D) / (2 * b));
                    roots[root_count++] = (Root){r1, 0, 0};
                    if (r1 != r2) { // Добавляем второй корень, если он отличается
                        roots[root_count++] = (Root){r2, 0, 0};
                    }
                } else if (D == 0) {
                    roots[root_count++] = (Root){round_to_4(-c / (2 * b)), 0, 0};
                } else {
                    roots[root_count++] = (Root){round_to_4(-c / (2 * b)), round_to_4(sqrt(-D) / (2 * b)), 1};
                }
            }
        } else {
            double new_a, new_b, new_c, x_new;
            solve_cubic(a, b, c, d, epsilon, &x_new);
            roots[root_count++] = (Root){round_to_4(x_new), 0, 0};
            horner(a, b, c, x_new, &new_a, &new_b, &new_c, epsilon);
            printf("Уравнение, полученное методом Горнера:\n");
            print_number(new_a); printf("*x^2 + ");
            print_number(new_b); printf("*x + ");
            print_number(new_c); printf(" = 0\n");
            solve_quadratic(new_a, new_b, new_c, epsilon);
            double D = new_b * new_b - 4 * new_a * new_c;
            if (D > 0) {
                double sqrt_D = sqrt(D);
                double r1 = round_to_4((-new_b + sqrt_D) / (2 * new_a));
                double r2 = round_to_4((-new_b - sqrt_D) / (2 * new_a));
                roots[root_count++] = (Root){r1, 0, 0};
                if (r1 != r2) { // Добавляем второй корень, если он отличается
                    roots[root_count++] = (Root){r2, 0, 0};
                }
            } else if (D == 0) {
                double root = round_to_4(-new_b / (2 * new_a));
                if (root != roots[0].real) { // Проверяем, что корень не дублируется
                    roots[root_count++] = (Root){root, 0, 0};
                }
            } else {
                roots[root_count++] = (Root){round_to_4(-new_b / (2 * new_a)), round_to_4(sqrt(-D) / (2 * new_a)), 1};
            }
        }
        // Сортировка корней и вывод
        if (root_count > 1) {
            qsort(roots, root_count, sizeof(Root), compare_roots);
        }
        printf("\nНайденные корни уравнения:\n");
        printf("roots = [");
        for (int i = 0; i < root_count; i++) {
            if (i > 0) printf(", ");
            print_number(roots[i].real);
            if (roots[i].is_complex) {
                printf(" ± ");
                print_number(roots[i].imag);
                printf("*i");
            }
        }
        printf("]\n\n");
        // Запрос на повторный ввод
        char response[10];
        while (1) {
            printf("Хотите ввести новое уравнение? (y/n): ");
            if (fgets(response, sizeof(response), stdin) == NULL) {
                printf("\nВвод прерван пользователем.\n");
                exit(0);
            }
            if (response[0] == 'n' && response[1] == '\n') {
                exit(0);
            }
            if (response[0] == 'y' && response[1] == '\n') {
                break;
            }
            printf("Некорректный ввод. Введите 'y' (да) или 'n' (нет).\n");
        }
    }
    return 0;
}
