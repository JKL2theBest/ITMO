#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>

#define BOMB

int main() {
    long mempagesize = sysconf(_SC_PAGESIZE); 
    int pages_allocated = 0;

#ifdef BOMB
    while (1) {
        char *mem = mmap(NULL, mempagesize, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        
        if (mem == MAP_FAILED) {
            printf("Memory allocation failed after %d pages\n", pages_allocated);
            break;
        }
        
        pages_allocated++;
        for (long i = 0; i < mempagesize; i++) {
            mem[i] = 0;
        }
    }
#endif

    return 0;
}
