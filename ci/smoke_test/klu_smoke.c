#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "klu.h"

int main(void) {
    klu_common Common;
    klu_symbolic *Symbolic = NULL;
    klu_numeric *Numeric = NULL;

    int n = 3;
    int Ap[] = {0, 2, 4, 6};
    int Ai[] = {0, 2, 0, 1, 1, 2};
    double Ax[] = {2.0, -1.0, 3.0, 4.0, -1.0, 1.0};
    double b[] = {8.0, 5.0, 2.0};
    double expected_x[] = {1.0, 2.0, 3.0};

    printf("Starting KLU smoke test...\n");

    if (!klu_defaults(&Common)) {
        fprintf(stderr, "Error: klu_defaults failed\n");
        return 1;
    }

    Symbolic = klu_analyze(n, Ap, Ai, &Common);
    if (!Symbolic) {
        fprintf(stderr, "Error: klu_analyze failed\n");
        return 1;
    }

    Numeric = klu_factor(Ap, Ai, Ax, Symbolic, &Common);
    if (!Numeric) {
        fprintf(stderr, "Error: klu_factor failed\n");
        klu_free_symbolic(&Symbolic, &Common);
        return 1;
    }

    /* klu_solve overwrites b with the solution vector x */
    if (!klu_solve(Symbolic, Numeric, n, 1, b, &Common)) {
        fprintf(stderr, "Error: klu_solve failed\n");
        klu_free_numeric(&Numeric, &Common);
        klu_free_symbolic(&Symbolic, &Common);
        return 1;
    }

    printf("Solution: x = [%.4f, %.4f, %.4f]\n", b[0], b[1], b[2]);

    double diff = 0.0;
    for (int i = 0; i < n; ++i) {
        diff += fabs(b[i] - expected_x[i]);
    }

    klu_free_numeric(&Numeric, &Common);
    klu_free_symbolic(&Symbolic, &Common);

    if (diff > 1e-6) {
        fprintf(stderr, "Verification failed! diff = %e\n", diff);
        return 1;
    }

    printf("KLU smoke test successfully verified (diff = %e)!\n", diff);
    return 0;
}
