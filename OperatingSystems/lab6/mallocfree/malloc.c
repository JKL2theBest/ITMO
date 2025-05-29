#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

#define ITERATIONS 5000

int main() {
    FILE *output = fopen("all_results.csv", "w");
    if (!output) {
        perror("Cannot open file");
        return 1;
    }

    fprintf(output, "Size(Bytes),MallocTime(ns),FreeTime(ns),TotalTime(ns)\n");

    LARGE_INTEGER frequency, start, end;
    QueryPerformanceFrequency(&frequency);

    for (size_t size = 1; size <= 1024 * 1024 * 1024; size *= 2) {  // Размеры от 1 байта до 1 ГБ
        double total_malloc_time = 0;
        double total_free_time = 0;
        double total_time = 0;

        for (int i = 0; i < ITERATIONS; i++) {
            QueryPerformanceCounter(&start);
            void *ptr = malloc(size);
            if (!ptr) {
                perror("malloc failed");
                return 1;
            }
            QueryPerformanceCounter(&end);
            double malloc_time = (double)(end.QuadPart - start.QuadPart) * 1e9 / frequency.QuadPart;
            total_malloc_time += malloc_time;

            // Измеряем время для free
            QueryPerformanceCounter(&start);
            free(ptr);
            QueryPerformanceCounter(&end);
            double free_time = (double)(end.QuadPart - start.QuadPart) * 1e9 / frequency.QuadPart;
            total_free_time += free_time;

            total_time += malloc_time + free_time;
        }

        double avg_malloc_time = total_malloc_time / ITERATIONS;
        double avg_free_time = total_free_time / ITERATIONS;
        double avg_total_time = total_time / ITERATIONS;

        fprintf(output, "%zu,%.2f,%.2f,%.2f\n", size, avg_malloc_time, avg_free_time, avg_total_time);
        printf("Size: %zu Bytes, Avg Malloc Time: %.2f ns, Avg Free Time: %.2f ns, Avg Total Time: %.2f ns\n",
               size, avg_malloc_time, avg_free_time, avg_total_time);
    }

    fclose(output);
    printf("Results saved to all_results.csv\n");
    return 0;
}
