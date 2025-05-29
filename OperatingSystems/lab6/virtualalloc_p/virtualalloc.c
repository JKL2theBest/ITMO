#include <stdio.h>
#include <windows.h>

#define ITERATIONS 10

void TestVirtualAlloc(size_t size, FILE *output) {
    LARGE_INTEGER frequency, start, end;
    QueryPerformanceFrequency(&frequency);

    double total_alloc_time = 0;
    double total_free_time = 0;
    double total_time = 0;

    for (int i = 0; i < ITERATIONS; i++) {
        QueryPerformanceCounter(&start);
        void* allocatedMemory = VirtualAlloc(NULL, size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
        if (allocatedMemory == NULL) {
            perror("VirtualAlloc failed");
            return;
        }
        QueryPerformanceCounter(&end);

        double alloc_time = (double)(end.QuadPart - start.QuadPart) * 1e9 / frequency.QuadPart;
        total_alloc_time += alloc_time;

        for (size_t j = 0; j < size / sizeof(int); j++) {
            ((int*)allocatedMemory)[j] = j;
        }

        QueryPerformanceCounter(&start);
        if (VirtualFree(allocatedMemory, 0, MEM_RELEASE) == 0) {
            perror("VirtualFree failed");
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
}

int main() {
    FILE *output = fopen("virtualalloc_results.csv", "w");
    if (!output) {
        perror("Cannot open file");
        return 1;
    }

    // Заголовки для CSV
    fprintf(output, "Size(Bytes),VirtualAllocTime(ns),VirtualFreeTime(ns),TotalTime(ns)\n");

    // Цикл для разных размеров памяти
    for (size_t size = 1; size <= 1024 * 1024 * 1024; size *= 2) {  // Размеры от 1 байта до 1 ГБ
        TestVirtualAlloc(size, output);
        printf("Test completed for size: %zu Bytes\n", size);
    }

    fclose(output);
    printf("Results saved to virtualalloc_results.csv\n");
    return 0;
}
