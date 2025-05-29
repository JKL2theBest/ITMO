section .data
    hv_string db "Detected Hypervisor", 0
    no_hv_string db "No Hypervisor Detected", 0

section .text
    global _start

_start:
    ; Инициализация регистров
    mov eax, 1          ; Запрос 1 (Processor Info and Feature Bits)
    cpuid               ; Выполнить CPUID

    ; Проверить бит 31 в ECX
    test ecx, 1 << 31   ; Если установлен бит 31, то это гипервизор
    jnz detected

    ; Если гипервизор не найден
    mov rdi, 1          ; дескриптор stdout
    mov rsi, no_hv_string
    mov rdx, 23         ; длина строки
    mov rax, 0x1        ; syscall write
    syscall             ; выполнить syscall

    ; Завершаем программу после вывода
    jmp exit_program

detected:
    ; Если гипервизор найден
    mov rdi, 1          ; дескриптор stdout
    mov rsi, hv_string
    mov rdx, 23         ; длина строки
    mov rax, 0x1        ; syscall write
    syscall             ; выполнить syscall

exit_program:
    ; Завершить программу
    mov rax, 60         ; syscall exit
    xor rdi, rdi        ; код возврата 0
    syscall             ; выполнить syscall
