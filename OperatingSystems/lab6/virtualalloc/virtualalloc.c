#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

#define ITERATIONS 5000

int main() {
    FILE *output = fopen("virtualalloc_results.csv", "w");
    if (!output) {
        perror("Cannot open file");
        return 1;
    }

    fprintf(output, "Size(Bytes),VirtualAllocTime(ns),VirtualFreeTime(ns),TotalTime(ns)\n");

    LARGE_INTEGER frequency, start, end;
    QueryPerformanceFrequency(&frequency);

    for (size_t size = 1; size <= 1024 * 1024 * 1024; size *= 2) {  // Размеры от 1 байта до 1 ГБ
        double total_alloc_time = 0;
        double total_free_time = 0;
        double total_time = 0;

        for (int i = 0; i < ITERATIONS; i++) {
            QueryPerformanceCounter(&start);
            void *ptr = VirtualAlloc(NULL, size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
            if (!ptr) {
                perror("VirtualAlloc failed");
                return 1;
            }
            QueryPerformanceCounter(&end);
            double alloc_time = (double)(end.QuadPart - start.QuadPart) * 1e9 / frequency.QuadPart;
            total_alloc_time += alloc_time;

            QueryPerformanceCounter(&start);
            if (!VirtualFree(ptr, 0, MEM_RELEASE)) {
                perror("VirtualFree failed");
                return 1;
            }
            QueryPerformanceCounter(&end);
            double free_time = (double)(end.QuadPart - start.QuadPart) * 1e9 / frequency.QuadPart;
            total_free_time += free_time;

            total_time += alloc_time + free_time;
        }

        double avg_alloc_time = total_alloc_time / ITERATIONS;
        double avg_free_time = total_free_time / ITERATIONS;
        double avg_total_time = total_time / ITERATIONS;

        fprintf(output, "%zu,%.2f,%.2f,%.2f\n", size, avg_alloc_time, avg_free_time, avg_total_time);
        printf("Size: %zu Bytes, Avg VirtualAlloc Time: %.2f ns, Avg VirtualFree Time: %.2f ns, Avg Total Time: %.2f ns\n",
               size, avg_alloc_time, avg_free_time, avg_total_time);
    }

    fclose(output);
    printf("Results saved to virtualalloc_results.csv\n");
    return 0;
}
