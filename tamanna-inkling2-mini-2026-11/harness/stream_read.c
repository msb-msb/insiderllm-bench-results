// STREAM-style sustained read: sum over a 320 MB double array (past any L3), OpenMP, best of 8.
// Written 2026-10-05 for the Tamanna DOCP check; the 2026-07-30 source was not kept, so its figures are context only.
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#define N (40L * 1000 * 1000)   /* 40M doubles = 320 MB */
int main(void) {
    double *a = malloc(N * sizeof(double)); double best = 0, sink = 0;
    #pragma omp parallel for
    for (long i = 0; i < N; i++) a[i] = (double)(i & 1023);
    for (int k = 0; k < 8; k++) {
        double s = 0, t0 = omp_get_wtime();
        #pragma omp parallel for reduction(+:s)
        for (long i = 0; i < N; i++) s += a[i];
        double t = omp_get_wtime() - t0, gbs = N * sizeof(double) / t / 1e9;
        if (gbs > best) best = gbs; sink += s;
    }
    printf("threads %d read %.2f GB/s (best of 8) sink %.0f\n", omp_get_max_threads(), best, sink);
    return 0;
}
