#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

#define ITERATIONS 100

void TestCalloc(size_t size, FILE *output) {
    LARGE_INTEGER frequency, start, end;
    QueryPerformanceFrequency(&frequency);

    double total_calloc_time = 0, total_free_time = 0, total_time = 0;

    for (int i = 0; i < ITERATIONS; i++) {
        QueryPerformanceCounter(&start);
        void *ptr = calloc(1, size);
        QueryPerformanceCounter(&end);

        if (!ptr) {
            perror("calloc failed");
            return;
        }

        double calloc_time = (double)(end.QuadPart - start.QuadPart) * 1e6 / frequency.QuadPart;
        total_calloc_time += calloc_time;

        QueryPerformanceCounter(&start);
        free(ptr);
        QueryPerformanceCounter(&end);

        double free_time = (double)(end.QuadPart - start.QuadPart) * 1e6 / frequency.QuadPart;
        total_free_time += free_time;

        total_time += calloc_time + free_time;
    }

    fprintf(output, "calloc,%zu,%.2f,%.2f,%.2f\n", size,
            total_calloc_time / ITERATIONS,
            total_free_time / ITERATIONS,
            total_time / ITERATIONS);
}

void TestRealloc(size_t size, FILE *output) {
    LARGE_INTEGER frequency, start, end;
    QueryPerformanceFrequency(&frequency);

    double total_realloc_time = 0, total_free_time = 0, total_time = 0;

    for (int i = 0; i < ITERATIONS; i++) {
        void *ptr = malloc(size / 2);
        if (!ptr) {
            perror("malloc for realloc failed");
            return;
        }

        QueryPerformanceCounter(&start);
        ptr = realloc(ptr, size);
        QueryPerformanceCounter(&end);

        if (!ptr) {
            perror("realloc failed");
            return;
        }

        double realloc_time = (double)(end.QuadPart - start.QuadPart) * 1e6 / frequency.QuadPart;
        total_realloc_time += realloc_time;

        QueryPerformanceCounter(&start);
        free(ptr);
        QueryPerformanceCounter(&end);

        double free_time = (double)(end.QuadPart - start.QuadPart) * 1e6 / frequency.QuadPart;
        total_free_time += free_time;

        total_time += realloc_time + free_time;
    }

    fprintf(output, "realloc,%zu,%.2f,%.2f,%.2f\n", size,
            total_realloc_time / ITERATIONS,
            total_free_time / ITERATIONS,
            total_time / ITERATIONS);
}

int main() {
    FILE *output = fopen("memory_test_results.csv", "w");
    if (!output) {
        perror("Cannot open file");
        return 1;
    }

    fprintf(output, "Function,Size(Bytes),AllocTime(us),FreeTime(us),TotalTime(us)\n");

    for (size_t size = 1; size <= 1024 * 1024 * 1024; size *= 2) {
        TestCalloc(size, output);
        TestRealloc(size, output);
        printf("Test completed for size: %zu Bytes\n", size);
    }

    fclose(output);
    printf("Results saved to memory_test_results.csv\n");
    return 0;
}
