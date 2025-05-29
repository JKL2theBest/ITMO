            // Заготовка программы. Сохраните в файле foo.c
// ID: d9e9e9f4eceef0ed  Эту строку не удалять!

// Добавьте заголовочные файлы, если нужно
// Функция, получающая массив и размер массива

#include <stdio.h>

long foo(long arr[], size_t len) {
  long sum = 0;
  for (size_t i = 0; i < len; i++) {
    if (arr[i] % 2 == 0) {
      sum += (arr[i] & 0xFF);
    }
  }
  return sum;
}

int main() {
  size_t len = 0;
  long arr[100];
  printf("Vvedi el. massiva (666, chtoby break): \n");
  while (1) {
    scanf("%ld", &arr[len]);
    if (arr[len] == 666) {
      break;
    }
    len++;
  }
  long result = foo(arr, len);
  printf("Summ mladshyh byte'ov vseh chetnyh el. massiva: \n%ld\n", result);
  return 0;
}
// p.s. резко написал функцию, но потом завис