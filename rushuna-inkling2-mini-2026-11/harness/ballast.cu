// Inkling lock I5: hold all but USABLE_MIB of the card so any allocation past ~4 GiB fails ("fits in 4 GiB").
// ballast USABLE_MIB  -> prints "READY free=<MiB> held=<MiB>" once free memory reads USABLE_MIB +/- 64, then sleeps.
#include <cuda_runtime.h>
#include <cstdio>
#include <cstdlib>
#include <unistd.h>
int main(int argc, char **argv) {
    size_t usable = (size_t)atol(argc > 1 ? argv[1] : "4096") << 20;
    size_t fr, tot;
    if (cudaMemGetInfo(&fr, &tot) != cudaSuccess) { printf("FAIL meminfo\n"); fflush(stdout); return 1; }
    size_t hold = fr - usable, held = 0;
    void *p = nullptr;
    // one big block, then top up in 64 MiB pieces if the context ate more than expected
    if (cudaMalloc(&p, hold) == cudaSuccess) { cudaMemset(p, 0xA5, hold); held = hold; }
    for (int i = 0; i < 256; i++) {
        cudaMemGetInfo(&fr, &tot);
        long long diff = (long long)fr - (long long)usable;
        if (diff <= (64ll << 20)) break;
        size_t step = (size_t)diff < (64u << 20) ? (size_t)diff : (64u << 20);
        void *q; if (cudaMalloc(&q, step) != cudaSuccess) break;
        cudaMemset(q, 0xA5, step); held += step;
    }
    cudaDeviceSynchronize();
    cudaMemGetInfo(&fr, &tot);
    long long d = (long long)fr - (long long)usable;
    if (d > (64ll << 20) || d < -(64ll << 20)) { printf("FAIL free=%zu held=%zu\n", fr >> 20, held >> 20); fflush(stdout); return 1; }
    printf("READY free=%zu held=%zu total=%zu\n", fr >> 20, held >> 20, tot >> 20); fflush(stdout);
    for (;;) pause();
}
