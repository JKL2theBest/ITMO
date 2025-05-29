#ifndef PSRS_H
#define PSRS_H

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <math.h>
#include <string.h>

#define MAX_NUMBERS 100000

typedef struct {
    double *array;
    int size;
    int id;
} ThreadData;

int read_data_from_file(const char *file_path, double **numbers, int *n, const char *array_type);
int initialize_threads(int p, pthread_t **threads, ThreadData **thread_data);
void *local_sort(void *arg);
void choose_splitters(double **sub_arrays, int *sizes, int p, double *splitters);
void redistribute_data(double *numbers, double *splitters, double *new_numbers, int n, int p);
void p_way_merge(double **sub_arrays, int *sizes, int p, double *result);
void write_result_to_file(const char *output_file, double *result, int n);
void free_memory(double *numbers, double *result, double *splitters, double *new_numbers, pthread_t *threads, ThreadData *thread_data, const char *array_type);

#endif // PSRS_H
