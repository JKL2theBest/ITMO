#include "headers.h"

static RBNode* createNode(double key) {
    RBNode* node = (RBNode*)malloc(sizeof(RBNode));
    node->key = key;
    node->color = RED;
    node->left = NULL;
    node->right = NULL;
    node->parent = NULL;
    return node;
}

RBTree* createRBTree() {
    RBTree* tree = (RBTree*)malloc(sizeof(RBTree));
    tree->root = NULL;
    return tree;
}

int rbGetColor(RBNode* node) {
    return node ? node->color : BLACK;
}

void rbSetColor(RBNode* node, int color) {
    if (node) node->color = color;
}

void leftRotate(RBTree* tree, RBNode* x) {
    RBNode* y = x->right;
    x->right = y->left;
    if (y->left) y->left->parent = x;
    y->parent = x->parent;
    if (!x->parent)
        tree->root = y;
    else if (x == x->parent->left)
        x->parent->left = y;
    else
        x->parent->right = y;
    y->left = x;
    x->parent = y;
}

void rightRotate(RBTree* tree, RBNode* y) {
    RBNode* x = y->left;
    y->left = x->right;
    if (x->right) x->right->parent = y;
    x->parent = y->parent;
    if (!y->parent)
        tree->root = x;
    else if (y == y->parent->left)
        y->parent->left = x;
    else
        y->parent->right = x;
    x->right = y;
    y->parent = x;
}

void rbFixInsert(RBTree* tree, RBNode* node) {
    while (node != tree->root && rbGetColor(node->parent) == RED) {
        RBNode* parent = node->parent;
        RBNode* grand = parent->parent;
        if (!grand) break; // защита
        RBNode* uncle = (parent == grand->left) ? grand->right : grand->left;

        if (rbGetColor(uncle) == RED) {
            rbSetColor(parent, BLACK);
            rbSetColor(uncle, BLACK);
            rbSetColor(grand, RED);
            node = grand;
        } else {
            if (parent == grand->left) {
                if (node == parent->right) {
                    node = parent;
                    leftRotate(tree, node);
                    parent = node->parent;
                }
                rbSetColor(parent, BLACK);
                rbSetColor(grand, RED);
                rightRotate(tree, grand);
            } else {
                if (node == parent->left) {
                    node = parent;
                    rightRotate(tree, node);
                    parent = node->parent;
                }
                rbSetColor(parent, BLACK);
                rbSetColor(grand, RED);
                leftRotate(tree, grand);
    }}}
    rbSetColor(tree->root, BLACK);
}

void rbInsert(RBTree* tree, double key) {
    RBNode* node = createNode(key);
    RBNode* y = NULL;
    RBNode* x = tree->root;
    while (x) {
        y = x;
        if (key < x->key)
            x = x->left;
        else
            x = x->right;
    }
    node->parent = y;
    if (!y)
        tree->root = node;
    else if (key < y->key)
        y->left = node;
    else
        y->right = node;
    rbFixInsert(tree, node);
}

RBNode* rbSearch(RBTree* tree, double key) {
    RBNode* cur = tree->root;
    while (cur) {
        if (key < cur->key)
            cur = cur->left;
        else if (key > cur->key)
            cur = cur->right;
        else
            return cur;
    }
    return NULL;
}

static void freeRBNode(RBNode* node) {
    if (!node) return;
    freeRBNode(node->left);
    freeRBNode(node->right);
    free(node);
}

void freeRBTree(RBTree* tree) {
    if (!tree) return;
    freeRBNode(tree->root);
    free(tree);
}

int* makeInsertionOrder(int n, int* outLen) {
    Segment *queue = malloc(sizeof(Segment) * (2 * n + 1));
    int *order = malloc(sizeof(int) * n);
    int qs = 0, qe = 0, pos = 0;

    queue[qe++] = (Segment){ .l = 0, .r = n - 1 };
    while (qs < qe) {
        Segment seg = queue[qs++];
        int l = seg.l, r = seg.r;
        if (l > r) continue;

        // длина отрезка
        int size = r - l + 1;
        // размер "левой" половины: при нечётном size
        int leftSize = (size + 1) / 2;
        // индекс медианы (первого элемента правой части)
        int mid = l + leftSize - 1;

        order[pos++] = mid;

        queue[qe++] = (Segment){ .l = l, .r = mid - 1 };
        queue[qe++] = (Segment){ .l = mid + 1, .r = r };
    }
    free(queue);

    *outLen = pos;
    return order;
}
