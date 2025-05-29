#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <security/pam_appl.h>
#include <security/pam_modules.h>
#include <time.h>

PAM_EXTERN int pam_sm_setcred(pam_handle_t *pamh, int flags, int argc, const char **argv) {
    return PAM_SUCCESS;
}

PAM_EXTERN int pam_sm_acct_mgmt(pam_handle_t *pamh, int flags, int argc, const char **argv) {
    return PAM_SUCCESS;
}

PAM_EXTERN int pam_sm_authenticate(pam_handle_t *pamh, int flags, int argc, const char **argv) {
    int retval;
    const char *username;
    
    // Получаем имя пользователя
    retval = pam_get_user(pamh, &username, "Username: ");
    if (retval != PAM_SUCCESS) {
        return retval;
    }

    printf("Welcome %s\n", username);
    
    // Проверяем, что имя пользователя — "kali"
    if (strcmp(username, "kali") != 0) {
        return PAM_AUTH_ERR; // Ошибка аутентификации, если имя пользователя не "kali"
    }

    // Если имя пользователя корректное, генерируем случайные числа для расчета пароля
    long x1, x2, x3, x4, y;
    time_t mytime;
    struct tm *mytm;
    mytime = time(0);
    mytm = localtime(&mytime);

    srandom(mytime + (long int)username);
    x1 = random() % 30;
    x2 = random() % 30;
    x3 = random() % 30;
    x4 = random() % 30;

    // Вычисляем значение пароля y по формуле
    y = x1 * x2 * x3 * x4;

    // Печатаем случайные числа, чтобы пользователь мог ввести правильный пароль
    printf("x1 = %ld, x2 = %ld, x3 = %ld, x4 = %ld\n", x1, x2, x3, x4);
    printf("Введите пароль: ");
    
    long userpwd;
    scanf("%ld", &userpwd);

    // Проверяем введенный пароль
    if (userpwd != y) {
        return PAM_AUTH_ERR; // Ошибка аутентификации
    }

    return PAM_SUCCESS; // Успешная аутентификация
}
