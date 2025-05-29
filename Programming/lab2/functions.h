#ifndef FUNCTIONS_H
#define FUNCTIONS_H

// Функция "красивого" вывода матрицы на экран
void print_matrix(long double **matrix, int rows, int columns) {
  for (int i = 0; i < rows; i++) {
    for (int j = 0; j < columns; j++) {
      char buffer[100];
      sprintf(buffer, "%Lf", matrix[i][j]);
      printf("%*s ", columns, buffer);
    }
    printf("\n");
  }
}

int get_t(int rows, int columns, char* D){
  int t;
  if (D) {
    printf("На сколько элементов выполнить циклический сдвиг?: ");
    // прочесть t
    scanf("%d", &t);
    printf("Строк: %d\nСтолбцов: %d\nT = %d\n",rows,columns,t);
  } else {
    printf("На сколько элементов выполнить циклический сдвиг?: ");
    scanf("%d", &t);
  } 
  // Проверка на корректность ввода
  if (t>0 && t<100) { // Пробую ставить (t>0 && isdigit(t)), чтобы проверить, что оно является числом, а не строкой, но чет не получается =/
    t %= rows * columns;
    return t;
  } else {
    // Вывод ошибки
    printf("Значение T должно быть положительным целым числом.\n");
    t = 69; // ;)
    return t;
  }
}

// Функция для генерации случайного long double значения в диапазоне от min до max
long double getRandomLD(long double min, long double max) {
    return min + (max - min) * ((long double)rand() / (long double)RAND_MAX);
}

// Функция преобразования в соответствии с Рис.1 а
void shift(long double **matrix, int rows, int cols, int t) {
  // Преобразование матрицы в вектор по строкам
  long double vector[rows * cols];
  int index = 0;
  for (int i = 0; i < rows; i++) {
    if (i % 2 == 0) {
      for (int j = 0; j < cols; j++) {
        vector[index++] = matrix[i][j];
      }
    } else {
        for (int j = cols - 1; j >= 0; j--) {
          vector[index++] = matrix[i][j];
        }
      }
  }
  // Сдвиг вектора на t элементов вправо
  long double shiftedVector[rows * cols];
  for (int i = 0; i < rows * cols; i++) {
    int newIndex = (i + t) % (rows * cols);
    shiftedVector[newIndex] = vector[i];
  }
  // Преобразование вектора обратно в матрицу
  index = 0;
  for (int i = 0; i < rows; i++) {
    if (i % 2 == 0) {
      for (int j = 0; j < cols; j++) {
        matrix[i][j] = shiftedVector[index++];
      }
    } else {
        for (int j = cols - 1; j >= 0; j--) {
          matrix[i][j] = shiftedVector[index++];
        }
      }
  }
} // Было сложно, но я понял это и написал эту функцию... за 3 дня...

#endif
