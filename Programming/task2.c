// Заготовка программы. Сохраните в файле main.c
// ID: bf8ff2eef2f1eaf7  Эту строку не удалять!

#include <stdio.h>
#include <stdlib.h>
// Добавьте заголовочные файлы, если нужно
// Программа, которая инвертирует 3 младших бита

int main(int argc, char *argv[]) {
  if (argc != 2) {
    fprintf(stderr, "Неверное количество аргументов\n");
    return 1;
  }

  // Преобразуем аргумент из шестнадцатеричной системы в десятичную
  unsigned long number = strtoul(argv[1], NULL, 16);

  // Разбиваем число на байты
  char *bytes = (char *)&number;

  // Инвертируем три младших бита в каждом байте
  for (int i = 0; i < sizeof(number) / sizeof(char); i++) {
    // Маска для инверсии трех младших битов
    char mask = 0x07;

    // Инвертируем три младших бита
    bytes[i] ^= mask;
  }

  // Выводим число в шестнадцатеричной системе без префикса 0x
  printf("%lx\n", number);

  return 0;
}