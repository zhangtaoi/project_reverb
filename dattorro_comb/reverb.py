"""Dattorro-inspired comb reverb — simplified topology.

Topology:
  8 parallel combs -> 2x(3 series allpass) -> 2 ladder allpass (LFO) -> damping

This is a simplified/compact variant of the 1997 Dattorro topology.
It uses fewer delay lines and a lighter signal path than the paper-faithful
tank version in dattorro_reverb/, while preserving the characteristic dense
echo tail and stereo modulation.
"""
import numpy as np
from numba import njit, int64

from common.delay import delay_len as _dl

# Delay lengths in samples @44.1kHz
_COMB = (1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617)
_APL = (225, 556, 441)
_APR = (225, 556, 1227)
_LAD = (908, 672)


def _layout(sr):
    """Return (offsets, lens) for all 8+3+3+2+2=18 delay lines in a flat buffer."""
    lens = [_dl(sr, n) for n in _COMB]
    lens += [_dl(sr, n) for n in _APL]
    lens += [_dl(sr, n) for n in _APR]
    lens += [_dl(sr, n) for n in _LAD] * 2
    offs = np.empty(len(lens) + 1, dtype=np.int64)
    offs[0] = 0
    for i in range(len(lens)):
        offs[i + 1] = offs[i] + lens[i]
    return offs, lens


@njit(cache=True)
def _run(x, decay, damp, diffuse, width, rate, sr, offs, lens, buf):
    """Process all samples.  buf is delay-line state, modified in-place."""
    n = len(x)
    L = np.empty(n)
    R = np.empty(n)
    rate_ = 2 * np.pi * rate / sr
    phase = 0.0
    lp = 0.0
    gain = 0.125  # 1/8 for 8-comb sum

    for i in range(n):
        xin = x[i]

        # ── 8 parallel comb filters ──
        s = 0.0
        for k in range(8):
            o = offs[k]; d = lens[k]
            p = i % d
            y = buf[o + p]
            buf[o + p] = xin + decay * y
            s += y
        s *= gain

        # ── L 3× series allpass ──
        v = s
        for k in range(3):
            o = offs[8 + k]; d = lens[8 + k]
            p = i % d
            y = buf[o + p]
            buf[o + p] = v + diffuse * y
            v = -diffuse * v + y
        l = v

        # ── R 3× series allpass ──
        v = s
        for k in range(3):
            o = offs[11 + k]; d = lens[11 + k]
            p = i % d
            y = buf[o + p]
            buf[o + p] = v + diffuse * y
            v = -diffuse * v + y
        r = v

        # ── LFO ──
        m = width * (0.5 + 0.5 * np.sin(phase))
        phase += rate_

        # ── L 2× ladder allpass (LFO-modulated) ──
        v = l
        for k in range(2):
            o = offs[14 + k]; d = lens[14 + k]
            mod = m if k == 0 else -m
            rp = (i - (d - 1) - mod)
            i0 = int(np.floor(rp)) % d
            fr = rp - np.floor(rp)
            y = (1 - fr) * buf[o + i0] + fr * buf[o + (i0 + 1) % d]
            p = i % d
            buf[o + p] = v + diffuse * y
            v = -diffuse * v + y
        l = v

        # ── R 2× ladder allpass (counter-rotated) ──
        v = r
        for k in range(2):
            o = offs[16 + k]; d = lens[16 + k]
            mod = -m if k == 0 else m
            rp = (i - (d - 1) - mod)
            i0 = int(np.floor(rp)) % d
            fr = rp - np.floor(rp)
            y = (1 - fr) * buf[o + i0] + fr * buf[o + (i0 + 1) % d]
            p = i % d
            buf[o + p] = v + diffuse * y
            v = -diffuse * v + y
        r = v

        # ── damping lowpass ──
        lp += damp * (l - lp)
        L[i] = lp
        R[i] = r

    return L, R


class Reverb:
    def __init__(self, sr, decay=0.85, damp=0.4, diffuse=0.5, width=0.25, rate=0.5):
        self.sr = sr
        self.decay = decay
        self.damp = damp
        self.diffuse = diffuse
        self.width = width
        self.rate = rate

    def process(self, x):
        x = np.ascontiguousarray(x, dtype=np.float64)
        offs, lens = _layout(self.sr)
        buf = np.zeros(offs[-1], dtype=np.float64)
        return _run(x, self.decay, self.damp, self.diffuse,
                    self.width, self.rate, self.sr, offs, lens, buf)