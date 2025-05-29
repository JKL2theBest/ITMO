#include <windows.h>
#include <stdio.h>

#define BOMB

int main() {
    SYSTEM_INFO sysInfo;
    GetSystemInfo(&sysInfo)
    SIZE_T pageSize = sysInfo.dwPageSize;
    int pages_allocated = 0;

#ifdef BOMB
    while (1) {  
        void* mem = VirtualAlloc(NULL, pageSize, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
        
        if (mem == NULL) { 
            printf("Memory allocation failed after %d pages\n", pages_allocated);
            break; 
        }
        pages_allocated++;
        printf("Allocated %d page(s)\n", pages_allocated);
    }
#endif

    return 0;
}
