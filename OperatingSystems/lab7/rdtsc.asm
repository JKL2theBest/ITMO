section .data
    vm_string db "Running in a VM", 0
    no_vm_string db "Running on Bare Metal", 0

section .text
    global _start

_start:
    ; Измерить время до выполнения инструкций
    rdtsc                   ; получить время
    mov rdi, rax            ; сохранить младшие 64 бита

    ; Выполнить серию инструкций
    mov rcx, 1000000        ; цикл
.loop:
    dec rcx
    jnz .loop

    ; Измерить время после выполнения инструкций
    rdtsc
    sub rax, rdi            ; разница во времени (младшие 64 бита)

    ; Если время слишком велико, это может быть VM
    cmp rax, 1000000
    ja vm_detected

no_vm_detected:
    mov rdi, 1              ; дескриптор stdout
    mov rsi, no_vm_string
    mov rdx, 23             ; длина строки
    mov rax, 0x1            ; syscall write
    syscall                 ; выполнить syscall

    jmp exit_program

vm_detected:
    mov rdi, 1              ; дескриптор stdout
    mov rsi, vm_string
    mov rdx, 15             ; длина строки
    mov rax, 0x1            ; syscall write
    syscall                 ; выполнить syscall

exit_program:
    ; Завершить программу
    mov rax, 60             ; syscall exit
    xor rdi, rdi            ; код возврата 0
    syscall                 ; выполнить syscall
