import ctypes

PAGE_SIZE = 4096  
allocated_memory = [] 
pages_allocated = 0 

try:
    while True:
        # Выделяем память
        mem = ctypes.windll.kernel32.VirtualAlloc(
            None,
            PAGE_SIZE,
            0x1000 | 0x2000,  # MEM_COMMIT | MEM_RESERVE
            0x04  # PAGE_READWRITE
        )
        
        if mem == 0: 
            print(f"Memory allocation failed after {pages_allocated} pages.")
            break

        allocated_memory.append(mem)  
        pages_allocated += 1
        print(f"Allocated {pages_allocated} page(s)")

except KeyboardInterrupt:
    print("Program interrupted.")

for mem in allocated_memory:
    ctypes.windll.kernel32.VirtualFree(mem, 0, 0x8000)  # FREEMEM
