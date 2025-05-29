#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "functions.h"

int main(int argc, char *argv[]) {
    // Проверка запуска с переменной среды, включающей отладочный вывод.
    // Пример запуска с установкой переменной LAB4DEBUG в 1:
    // $ LAB4DEBUG=1 ./lab4msN3146 test.txt
    char *DEBUG = getenv("LAB3DEBUG");
    if (DEBUG) {
        fprintf(stderr, "Включен вывод отладочных сообщений\n");
    }
 
    if(argc != 2) {
        fprintf(stderr, "Использование: └─$%s имя_файла\n(-v для вывода информации о студенте)\n", argv[0]);
        return EXIT_FAILURE;
    }
    if(strcmp(argv[1], "-v") == 0) {
        if (DEBUG) {
            fprintf(stderr, "Опция -v включена\n");
            }
        fprintf(stderr, "Суханкулиев Мухаммет, гр. N3146\nВариант: 1-4-5-2\n");
        exit(EXIT_SUCCESS);
    }

    // Чтение данных из файла (добавил перехват ошибки переполнения стека, ибо таким образом злоумышленик может получить доступ к своей функции)
    signal(SIGSEGV, handle_sigsegv);
    Node* head = readDataFromFile(argv[1]);

    // Обработка ввода пользователя
    char command[256];
    while(fgets(command, sizeof(command), stdin)) {
        command[strcspn(command, "\n")] = 0;
        if(strncmp(command, "push_front ", 11) == 0) {
        push_front(&head, command + 11);
        } else if(strncmp(command, "push_back ", 10) == 0) {
            push_back(&head, command + 10);
        } else if(strcmp(command, "pop_front") == 0) {
            pop_front(&head);
        } else if(strcmp(command, "pop_back") == 0) {
            pop_back(&head);
        } else if(strncmp(command, "dump", 4) == 0) {
            char* filename = NULL;
            if(strlen(command) > 5) {
                filename = command + 5;
            }
            dump(head, filename);
        } else if(strcmp(command, "delete_even") == 0) {
            delete_even(&head);
        } else {
            fprintf(stderr, "Ошибка: неподдерживаемая команда: '%s'.\n", command);
        }
    }

    if (head == NULL){
        createEmptyFile(argv[1]);
    } else {
        writeDataToFile(head, argv[1]);
        Node* current = head;
        while (current != NULL) {
            Node* next = current->next;
            free(current->data);
            free(current);
            current = next;
        }
    }    
    return EXIT_SUCCESS;
}
