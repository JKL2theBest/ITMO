#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include <stdint.h>
#include <unistd.h>
#include <regex.h>
#include <signal.h>

typedef struct Node {
    char* data;
    struct Node* next;
} Node;

Node* createNode(char* data) {
    Node* new_node = (Node*)malloc(sizeof(Node));
    if(new_node == NULL) {
        fprintf(stderr, "Ошибка выделения памяти\n");
        return NULL;
    }
    new_node->data = strdup(data);
    new_node->next = NULL;
    return new_node;
}

// Проверка Доменного имени
int isValidDomain(char* domain) {
    regex_t regex;
    int reti;
    reti = regcomp(&regex, "^([a-z0-9]+(-[a-z0-9]+)*\\.)+[a-z]{2,}$", REG_EXTENDED);
    if (reti) {
        fprintf(stderr, "Could not compile regex\n");
        return 0;
    }
    reti = regexec(&regex, domain, 0, NULL, 0);
    regfree(&regex);
    if (!reti) {
        return 1;
    } else if (reti == REG_NOMATCH) {
        return 0;
    } else {
        fprintf(stderr, "Regex match failed\n");
        return 0;
    }
}

void free_list(Node** head) {
    Node* tmp;
    while (*head != NULL) {
        tmp = *head;
        *head = (*head)->next;
        free(tmp->data);
        free(tmp);
    }
}

void push_front(Node** head, char* data) {
    if (isValidDomain(data)) {
        Node* new_node = createNode(data);
        if(new_node == NULL) {
            return;
        }
        new_node->next = *head;
        *head = new_node;
    } else {
        fprintf(stderr, "Ошибка: строка '%s' не является доменным именем.\n", data);
    }
}

void push_back(Node** head, char* data) {
    if (isValidDomain(data)) {
        Node* new_node = createNode(data);
        if(new_node == NULL) {
            return;
        }

        if (*head == NULL) {
            *head = new_node;
        } else {
            Node* current = *head;
            while (current->next != NULL) {
                current = current->next;
            }
            current->next = new_node;
        }
    } else {
        fprintf(stderr, "Ошибка: строка '%s' не является доменным именем.\n", data);
    }
}

void pop_front(Node** head) {
    if (*head == NULL) {
        return;
    }
    Node* next_node = (*head)->next;
    free((*head)->data);
    free(*head);
    *head = next_node;
}

void pop_back(Node** head) {
    if (*head == NULL) {
        return;
    }
    Node* current = *head;
    Node* prev = NULL;
    while (current->next != NULL) {
        prev = current;
        current = current->next;
    }
    if (prev == NULL) {
        *head = NULL;
    } else {
        prev->next = NULL;
    }
    free(current->data);
    free(current);
}

void dump(Node* head, char* filename) {
    FILE* stream;
    if (filename != NULL) {
        stream = fopen(filename, "w");
        if (stream == NULL) {
            fprintf(stderr, "Ошибка: не удалось открыть файл '%s' для записи.\n", filename);
            return;
        }
    } else {
        stream = stdout;
    }
    Node* current = head;
    while (current != NULL) {
        fprintf(stream, "%p %p %s\n", (void*)current, (void*)current->next, current->data);
        current = current->next;
    }
    if (filename != NULL) {
        fclose(stream);
    }
}

// Удаление элементов на четных позициях из списка
void delete_even(Node** head) {
    Node* current = *head;
    Node* prev = NULL;
    int index = 0;
    while (current != NULL) {
        if (index % 2 == 0) {
            Node* next = current->next;
            if (prev == NULL) {
                *head = next;
            } else {
                prev->next = next;
            }
            free(current->data);
            free(current);
            current = next;
        } else {
            prev = current;
            current = current->next;
        }
        index++;
    }
}

// Запись данных из файла, заданного формата, в Односвязный список
Node* readDataFromFile(char* filename) {
    FILE *file = fopen(filename, "rb");
    if (file != NULL) {
        uint32_t offset;
        if (fread(&offset, sizeof(uint32_t), 1, file) != 1) {
            printf("Некорректный формат файла\n");
            exit(EXIT_FAILURE);
        }
        Node *head = NULL, *current = NULL;
        char buffer[256];
        uint16_t index;
        uint32_t i = 0;
        while (i < offset) {
            int j = 0;
            char c;
            while ((c = fgetc(file)) != '\0') {
                buffer[j++] = c;
            }
            buffer[j] = '\0';
            Node *node = (Node*)malloc(sizeof(Node));
            node->data = strdup(buffer);
            node->next = NULL;
            if (head == NULL) {
                head = node;
                current = node;
            } else {
                current->next = node;
                current = node;
            }
            i += j + 1;
        }
        if (i != offset) {
            printf("Некорректный формат файла\n");
            exit(EXIT_FAILURE);
        }
        fseek(file, offset, SEEK_SET);
        while (fread(&index, sizeof(uint16_t), 1, file) == 1) {
            Node *node = head;
            for (i = 0; i < index && node != NULL; i++) {
                node = node->next;
            }
        }
        fclose(file);
        return head;
    } else {
        return NULL;
    }
}

// Запись данных в файл, в определенном формате
void writeDataToFile(Node* head, char* filename) {
    FILE *file = fopen(filename, "wb");
    if (file == NULL) {
        printf("Не удалось открыть файл\n");
        return;
    }
    Node *current = head;
    uint32_t offset = 0;
    uint16_t index = 0;
    while (current != NULL) {
        offset += strlen(current->data) + 1;
        current = current->next;
    }
    offset += sizeof(uint16_t) * index;
    fwrite(&offset, sizeof(uint32_t), 1, file);
    current = head;
    while (current != NULL) {
        fwrite(current->data, sizeof(char), strlen(current->data) + 1, file);
        current = current->next;
    }
    current = head;
    while (current != NULL) {
        fwrite(&index, sizeof(uint16_t), 1, file);
        index++;
        current = current->next;
    }
    fclose(file);
}

void createEmptyFile(char* filename) {
    FILE *file = fopen(filename, "w");
    if (file != NULL) {
        fclose(file);
    } else {
        printf("Не удалось создать файл\n");
    }
}

void handle_sigsegv(int sig) {
    (void)sig;
    printf("Некорректный формат файла\n");
    exit(EXIT_FAILURE);
}

#endif
