#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include "verb.h"
#include "verb_structs.h"

int main() {
    int sr = 48000;
    int n = sr * 2;  // 2 seconds

    DattorroVerb* v = DattorroVerb_create();
    // Default params (already set in initialize())

    // Generate impulse response
    double* L = (double*)malloc(n * sizeof(double));
    double* R = (double*)malloc(n * sizeof(double));

    for (int i = 0; i < n; i++) {
        double in = (i == 0) ? 1.0 : 0.0;
        DattorroVerb_process(v, in);
        L[i] = DattorroVerb_getLeft(v);
        R[i] = DattorroVerb_getRight(v);
    }

    DattorroVerb_delete(v);

    // Write WAV (mono, first 500ms only for size)
    int wav_n = 24000; // 500ms @ 48k
    FILE* f = fopen("ir_elvisio.wav", "wb");
    if (!f) { printf("cannot open\n"); return 1; }

    int16_t* buf = (int16_t*)malloc(wav_n * 2 * sizeof(int16_t));
    for (int i = 0; i < wav_n; i++) {
        buf[i*2]   = (int16_t)(L[i] * 32767);
        buf[i*2+1] = (int16_t)(R[i] * 32767);
    }

    // WAV header
    uint32_t data_size = wav_n * 2 * sizeof(int16_t);
    fwrite("RIFF", 1, 4, f);
    uint32_t fs = 36 + data_size; fwrite(&fs, 4, 1, f);
    fwrite("WAVE", 1, 4, f);
    fwrite("fmt ", 1, 4, f);
    uint32_t hdr = 16; fwrite(&hdr, 4, 1, f);
    uint16_t fmt = 1; fwrite(&fmt, 2, 1, f);
    uint16_t ch = 2; fwrite(&ch, 2, 1, f);
    uint32_t sr_l = sr; fwrite(&sr_l, 4, 1, f);
    uint32_t br = sr * 2 * sizeof(int16_t); fwrite(&br, 4, 1, f);
    uint16_t ba = 2 * sizeof(int16_t); fwrite(&ba, 2, 1, f);
    uint16_t bits = 16; fwrite(&bits, 2, 1, f);
    fwrite("data", 1, 4, f);
    fwrite(&data_size, 4, 1, f);
    fwrite(buf, 1, data_size, f);
    fclose(f);

    printf("wrote ir_elvisio.wav\n");
    printf("L peak: %f  R peak: %f\n",
           fabs(L[0]), fabs(R[0]));  // quick check
    // find max
    double lmax = 0, rmax = 0;
    for (int i = 0; i < n; i++) {
        if (fabs(L[i]) > lmax) lmax = fabs(L[i]);
        if (fabs(R[i]) > rmax) rmax = fabs(R[i]);
    }
    printf("L max: %f  R max: %f\n", lmax, rmax);

    // find first non-zero
    for (int i = 0; i < n; i++) {
        if (fabs(L[i]) > 1e-10) {
            printf("First non-zero L[%d] = %f\n", i, L[i]);
            break;
        }
    }

    free(L); free(R); free(buf);
    return 0;
}