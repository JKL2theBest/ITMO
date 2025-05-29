#include "headers.h"

// Вспомогательная функция для вычисления размера поддерева с корнем в узле
static int subtree_size(RBNode* node) {
    if (node == NULL) return 0;
    return 1 + subtree_size(node->left) + subtree_size(node->right);
}

// Вычисление ранга (1-основанный) узла с данным ключом в дереве
int rbGetRank(RBTree* tree, double key) {
    RBNode* current = tree->root;
    int rank = 0;

    // Поиск узла с заданным ключом
    while (current != NULL) {
        if (key < current->key) {
            current = current->left;
        } else if (key > current->key) {
            rank += 1 + subtree_size(current->left);
            current = current->right;
        } else {
            rank += subtree_size(current->left) + 1;
            return rank;  // Возвращаем ранг узла
        }
    }
    return -1; // Ключ не найден
}

// Вспомогательная функция для записи узла и рёбер в DOT файл
static void writeDotNode(FILE* fp, RBNode* node) {
    if (node == NULL) {
        return;
    }

    const char* color = (node->color == RED) ? "red" : "black";

    // Записываем описание узла в формате DOT
    fprintf(fp,
        "    \"%p\" [label=\"%.15g\", color=%s, fontcolor=%s, style=filled, fillcolor=white, shape=circle];\n",
        (void*)node, node->key, color, color);

    if (node->left) {
        fprintf(fp, "    \"%p\" -> \"%p\";\n", (void*)node, (void*)node->left);
        writeDotNode(fp, node->left);
    } else {
        fprintf(fp,
            "    null%pL [label=\"NIL\", shape=box, style=filled, fillcolor=gray];\n",
            (void*)node);
        fprintf(fp, "    \"%p\" -> null%pL [style=dotted];\n",
            (void*)node, (void*)node);
    }

    if (node->right) {
        fprintf(fp, "    \"%p\" -> \"%p\";\n", (void*)node, (void*)node->right);
        writeDotNode(fp, node->right);
    } else {
        fprintf(fp,
            "    null%pR [label=\"NIL\", shape=box, style=filled, fillcolor=gray];\n",
            (void*)node);
        fprintf(fp, "    \"%p\" -> null%pR [style=dotted];\n",
            (void*)node, (void*)node);
}}

void exportRBTreeToDot(RBTree* tree, const char* filename) {
    if (tree == NULL || tree->root == NULL) {
        fprintf(stderr, "Дерево пусто, DOT файл не создан.\n");
        return;
    }

    FILE* fp = fopen(filename, "w");
    if (!fp) {
        perror("Ошибка открытия файла для записи DOT");
        return;
    }

    // Записываем начало DOT-графа
    fprintf(fp, "digraph RBTree {\n");
    fprintf(fp, "    node [fontname=\"Arial\"];\n");

    // Рекурсивная запись дерева
    writeDotNode(fp, tree->root);

    // Закрытие DOT-графа
    fprintf(fp, "}\n");
    fclose(fp);
}
