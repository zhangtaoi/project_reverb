/* Simple WAV reader/writer — no external dependencies.
   Supports: 16-bit PCM, 32-bit float, mono/stereo. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

#pragma pack(push, 1)
typedef struct {
    char     riff[4];        /* "RIFF" */
    uint32_t size;           /* file size - 8 */
    char     wave[4];        /* "WAVE" */
    char     fmt[4];         /* "fmt " */
    uint32_t fmt_size;       /* 16 */
    uint16_t audio_fmt;      /* 1 = PCM, 3 = IEEE float */
    uint16_t channels;
    uint32_t sample_rate;
    uint32_t byte_rate;
    uint16_t block_align;
    uint16_t bits_per_sample;
} WAVHeader;
#pragma pack(pop)

typedef struct {
    uint32_t    sr;
    uint16_t    channels;
    uint16_t    bits;
    size_t      frames;
    float*      data;  /* interleaved, float32 */
} WAVFile;

int wav_read(const char* path, WAVFile* w) {
    FILE* f = fopen(path, "rb");
    if (!f) return -1;
    WAVHeader h;
    fread(&h, sizeof(h), 1, f);
    if (memcmp(h.riff, "RIFF", 4) || memcmp(h.wave, "WAVE", 4)) {
        fclose(f); return -1;
    }
    /* skip to data chunk */
    char chunk[4]; uint32_t csize;
    while (1) {
        if (fread(chunk, 1, 4, f) != 4) { fclose(f); return -1; }
        fread(&csize, 4, 1, f);
        if (!memcmp(chunk, "data", 4)) break;
        fseek(f, csize, SEEK_CUR);
    }
    w->sr = h.sample_rate;
    w->channels = h.channels;
    w->bits = h.bits_per_sample;
    size_t samples = csize / (h.bits_per_sample / 8);
    w->frames = samples / h.channels;
    w->data = (float*)malloc(samples * sizeof(float));
    if (!w->data) { fclose(f); return -1; }

    if (h.bits_per_sample == 16) {
        int16_t* buf = (int16_t*)malloc(csize);
        fread(buf, 1, csize, f);
        for (size_t i = 0; i < samples; i++)
            w->data[i] = buf[i] / 32768.0f;
        free(buf);
    } else if (h.bits_per_sample == 32 && h.audio_fmt == 3) {
        fread(w->data, 1, csize, f);
    } else {
        free(w->data); fclose(f); return -1;
    }
    fclose(f);
    return 0;
}

int wav_write(const char* path, WAVFile* w) {
    FILE* f = fopen(path, "wb");
    if (!f) return -1;
    WAVHeader h;
    memset(&h, 0, sizeof(h));
    memcpy(h.riff, "RIFF", 4);
    memcpy(h.wave, "WAVE", 4);
    memcpy(h.fmt, "fmt ", 4);
    h.fmt_size = 16;
    h.audio_fmt = 3;  /* IEEE float */
    h.channels = w->channels;
    h.sample_rate = w->sr;
    h.bits_per_sample = 32;
    h.block_align = w->channels * 4;
    h.byte_rate = w->sr * h.block_align;
    size_t data_bytes = w->frames * h.block_align;
    h.size = 36 + data_bytes;

    fwrite(&h, sizeof(h), 1, f);
    fwrite("data", 1, 4, f);
    fwrite(&data_bytes, 4, 1, f);
    fwrite(w->data, 1, data_bytes, f);
    fclose(f);
    return 0;
}

void wav_free(WAVFile* w) {
    if (w->data) free(w->data);
    w->data = NULL;
}