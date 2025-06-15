#include "IDL.h"
#include <stdio.h>

float *add_6_svc(values *argp, struct svc_req *rqstp) {
    static float result;
    result = argp->num1 + argp->num2;
    return &result;
}

float *sub_6_svc(values *argp, struct svc_req *rqstp) {
    static float result;
    result = argp->num1 - argp->num2;
    return &result;
}

float *mul_6_svc(values *argp, struct svc_req *rqstp) {
    static float result;
    result = argp->num1 * argp->num2;
    return &result;
}

float *div_6_svc(values *argp, struct svc_req *rqstp) {
    static float result;
    result = argp->num1 / argp->num2;
    return &result;
}
