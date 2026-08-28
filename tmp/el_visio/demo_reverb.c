/* Dattorro reverb demo using el-visio engine.
   Reads a WAV file, processes mono->stereo, writes output.
   Usage: demo_reverb.exe <in.wav> <out.wav> [mix]
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "verb.h"
#include "verb_structs.h"
#include "wav_io.h"

int main(int argc, char** argv) {
    if (argc < 3) {
        printf("Usage: demo_reverb <in.wav> <out.wav> [mix]\n");
        return 1;
    }

    float mix = (argc > 3) ? (float)atof(argv[3]) : 0.5f;

    WAVFile in;
    if (wav_read(argv[1], &in)) {
        printf("Error reading %s\n", argv[1]);
        return 1;
    }

    printf("Input: %s  sr=%d ch=%d frames=%d\n", argv[1], in.sr, in.channels, (int)in.frames);
    printf("Mix: %.2f\n", mix);

    /* Convert to mono if stereo */
    float* mono = (float*)malloc(in.frames * sizeof(float));
    if (!mono) { wav_free(&in); return 1; }
    for (size_t i = 0; i < in.frames; i++) {
        if (in.channels == 1) {
            mono[i] = in.data[i];
        } else {
            float s = 0;
            for (int c = 0; c < in.channels; c++)
                s += in.data[i * in.channels + c];
            mono[i] = s / in.channels;
        }
    }

    /* Process through reverb */
    DattorroVerb* v = DattorroVerb_create();
    if (!v) { printf("Failed to create verb\n"); free(mono); wav_free(&in); return 1; }

    float* wetL = (float*)malloc(in.frames * sizeof(float));
    float* wetR = (float*)malloc(in.frames * sizeof(float));
    if (!wetL || !wetR) { printf("malloc failed\n"); return 1; }

    for (size_t i = 0; i < in.frames; i++) {
        DattorroVerb_process(v, mono[i]);
        wetL[i] = (float)DattorroVerb_getLeft(v);
        wetR[i] = (float)DattorroVerb_getRight(v);
    }

    /* Wet RMS match to dry */
    double dry_rms = 0, wet_rms = 0;
    for (size_t i = 0; i < in.frames; i++) {
        dry_rms += mono[i] * mono[i];
        wet_rms += wetL[i] * wetL[i] + wetR[i] * wetR[i];
    }
    dry_rms = sqrt(dry_rms / in.frames);
    wet_rms = sqrt(wet_rms / (in.frames * 2));
    double gain = (wet_rms > 1e-12) ? dry_rms / wet_rms : 1.0;
    printf("Dry RMS: %.4f  Wet RMS: %.4f  Gain: %.4f\n", dry_rms, wet_rms, gain);

    /* Mix dry+wet */
    WAVFile out;
    out.sr = in.sr;
    out.channels = 2;
    out.bits = 32;
    out.frames = in.frames;
    out.data = (float*)malloc(in.frames * 2 * sizeof(float));

    for (size_t i = 0; i < in.frames; i++) {
        float wL = wetL[i] * gain * mix;
        float wR = wetR[i] * gain * mix;
        if (in.channels == 1) {
            out.data[i * 2]     = mono[i] * (1 - mix) + wL;
            out.data[i * 2 + 1] = mono[i] * (1 - mix) + wR;
        } else {
            out.data[i * 2]     = in.data[i * in.channels] * (1 - mix) + wL;
            out.data[i * 2 + 1] = in.data[i * in.channels + 1] * (1 - mix) + wR;
        }
        /* peak normalization guard */
    }

    /* Peak-normalize to prevent clipping */
    double peak = 0;
    for (size_t i = 0; i < out.frames * 2; i++) {
        double a = fabs(out.data[i]);
        if (a > peak) peak = a;
    }
    if (peak > 1.0) {
        for (size_t i = 0; i < out.frames * 2; i++)
            out.data[i] /= (float)peak;
    }

    if (wav_write(argv[2], &out)) {
        printf("Error writing %s\n", argv[2]);
        return 1;
    }
    printf("Wrote %s  (%d frames @ %dHz, peak=%.3f)\n", argv[2], (int)out.frames, out.sr, peak);

    DattorroVerb_delete(v);
    free(mono); free(wetL); free(wetR);
    wav_free(&in); wav_free(&out);
    return 0;
}