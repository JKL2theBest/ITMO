#ifndef FUNCTIONS_H
#define FUNCTIONS_H

// Функция, проверяющая является ли значение шестнадцатеричным числом
int is_hex(const char *str) {
  while (*str) {
    if (!isxdigit(*str)) {
      return 0;
    }
    str++;
  }
  return 1;
}

// Функция, переводящая шестнадцатеричное число в десятичное
unsigned int hex_to_dec(char *input) {
  unsigned int n;
  n = strtol(input, NULL, 16);
  return n;
}

#endif
