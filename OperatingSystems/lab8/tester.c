#include <security/pam_appl.h>
#include <security/pam_misc.h>
#include <stdio.h>

const struct pam_conv conv = {
    misc_conv,
    NULL
};

int main(int argc, char *argv[]) {
    pam_handle_t *pamh = NULL;
    int retval;

    if (argc != 2) {
        printf("Usage: app [username]\n");
        exit(1);
    }

    const char *user = argv[1];

    // Начинаем аутентификацию с нашим PAM-модулем
    retval = pam_start("check_user", user, &conv, &pamh);

    if (retval == PAM_SUCCESS) {
        printf("Credentials accepted.\n");
        retval = pam_authenticate(pamh, 0); // Проверка пароля
    }

    if (retval == PAM_SUCCESS) {
        printf("Account is valid.\n");
        retval = pam_acct_mgmt(pamh, 0); // Проверка доступа к аккаунту
    }

    if (retval == PAM_SUCCESS) {
        printf("Authenticated\n");
    } else {
        printf("Not Authenticated\n");
    }

    if (pam_end(pamh, retval) != PAM_SUCCESS) {
        printf("check_user: failed to release authenticator\n");
        exit(1);
    }

    return retval == PAM_SUCCESS ? 0 : 1;
}
