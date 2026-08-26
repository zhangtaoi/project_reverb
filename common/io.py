"""De-interleave audio file into floats in [-1, 1].  Returns (samples, sr)."""
import numpy as np
import soundfile as sf


def load(path):
    data, sr = sf.read(path, dtype="float32")
    if data.ndim == 1:
        data = data[:, None]
    return data, sr


def save(path, data, sr):
    sf.write(path, data, sr)