#include <windows.h>
#include <stdio.h>

int main() {
    char path_to_executable[] = "virtualalloc.exe";

    STARTUPINFO si = {0};
    PROCESS_INFORMATION pi = {0};

    si.cb = sizeof(si);

    if (CreateProcess(
            NULL,                    // Путь к исполнимому файлу (NULL для стандартного пути)
            path_to_executable,      // Имя файла, который нужно запустить
            NULL,                    // Дескриптор безопасности
            NULL,                    // Дескриптор безопасности
            FALSE,                   // Унаследование дескрипторов
            0,                       // Флаги создания
            NULL,                    // Переменные среды
            NULL,                    // Текущий каталог
            &si,                     // Структура STARTUPINFO
            &pi)                     // Структура PROCESS_INFORMATION
    ) {
        printf("Process created successfully.\n");

        WaitForSingleObject(pi.hProcess, INFINITE);

        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    } else {
        printf("CreateProcess failed (%d).\n", GetLastError());
    }

    return 0;
}
