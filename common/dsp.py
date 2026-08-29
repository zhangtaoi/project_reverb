"""Shared DSP utilities for audio processing.

Currently contains:
- soft_limiter: soft-knee look-ahead limiter for musical peak control
"""
import numpy as np


def soft_limiter(out, threshold=0.95, knee=0.05, attack_ms=1.0,
                 release_ms=50.0, sr=44100):
    """Soft-knee limiter with per-sample gain smoothing.

    Only activates when the signal exceeds threshold - knee/2.
    Attack is fast (ms), release is slow (ms) — standard for transparent limiting.

    Parameters
    ----------
    out : (N,) or (N, C) ndarray
        Signal to limit.
    threshold : float, 0-1
        Level at which limiting starts (linear). 0.95 = -0.45 dBFS.
    knee : float, 0-0.2
        Soft knee width (linear). Larger = smoother transition.
    attack_ms : float
        Attack time in milliseconds (how fast gain reduction kicks in).
    release_ms : float
        Release time in milliseconds (how fast gain recovers).
    sr : int
        Sample rate.

    Returns
    -------
    out : ndarray, same shape
        Limited signal in [-1, 1].
    """
    MONO = out.ndim == 1
    x = out.copy() if MONO else out.copy()
    n = x.shape[0] if MONO else x.shape[0]
    c = 1 if MONO else x.shape[1]

    # Convert time constants to per-sample smoothing coefficients
    attack = np.exp(-1.0 / (attack_ms * sr / 1000.0))
    release = np.exp(-1.0 / (release_ms * sr / 1000.0))

    # Knee boundaries
    knee_low = threshold - knee / 2
    knee_high = threshold + knee / 2
    knee_inv = 1.0 / (knee_high - knee_low) if knee > 0 else 0.0

    gain = 1.0  # current smoothed gain

    if MONO:
        for i in range(n):
            level = abs(x[i])
            # Soft-knee gain reduction
            if level <= knee_low:
                gr = 1.0
            elif level < knee_high:
                # Quadratic knee: smooth transition from 1 to threshold/level
                t = (level - knee_low) * knee_inv
                gr = 1.0 - (1.0 - threshold / (level + 1e-12)) * (t * t)
            else:
                gr = threshold / (level + 1e-12)

            # Smooth gain envelope (fast attack, slow release)
            coeff = attack if gr < gain else release
            gain = coeff * gain + (1.0 - coeff) * gr

            x[i] = x[i] * gain
    else:
        for ch in range(c):
            gain = 1.0
            for i in range(n):
                level = abs(x[i, ch])
                if level <= knee_low:
                    gr = 1.0
                elif level < knee_high:
                    t = (level - knee_low) * knee_inv
                    gr = 1.0 - (1.0 - threshold / (level + 1e-12)) * (t * t)
                else:
                    gr = threshold / (level + 1e-12)

                coeff = attack if gr < gain else release
                gain = coeff * gain + (1.0 - coeff) * gr
                x[i, ch] = x[i, ch] * gain

    return x