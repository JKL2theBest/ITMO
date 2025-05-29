#include "IDL.h"
#include <stdio.h>

float compute_6(char *host, float a, float b) {
    CLIENT *clnt;
    float *result_1;
    values mul_6_arg;

    // Устанавливаем значения аргументов
    mul_6_arg.num1 = a;
    mul_6_arg.num2 = b;
    mul_6_arg.operation = '*';  // Определяем операцию как умножение

    // Создаем клиентскую сторону для RPC вызова
    clnt = clnt_create(host, COMPUTE, COMPUTE_VERS, "udp");
    if (clnt == NULL) {
        clnt_pcreateerror(host);
        exit(1);
    }

    // Выполняем RPC вызов для умножения
    result_1 = mul_6(&mul_6_arg, clnt);
    if (result_1 == (float *) NULL) {
        clnt_perror(clnt, "call failed");
        exit(1);
    }

    clnt_destroy(clnt);
    return (*result_1);  // Возвращаем результат умножения
}

int main(int argc, char *argv[]) {
    char *host;
    float number1, number2;

    printf("Enter the 2 numbers to multiply:\n");
    scanf("%f", &number1);
    scanf("%f", &number2);

    // Устанавливаем хост (сервера)
    host = argv[1];

    // Вычисляем и выводим результат
    float result = compute_6(host, number1, number2);
    printf("Result: %f\n", result);  // Добавляем вывод результата

    return 0;
}
