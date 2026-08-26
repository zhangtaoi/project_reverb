"""Dattorro 1997 digital reverb — mono in, stereo out.

Reference: J. Dattorro, "Effect Design Part 1", JAES 1997.
Topology: 8 parallel combs -> 2x(3 series allpass) -> 2 ladder allpass.

Per-sample loop is numba-jitted. The LFO is precomputed as a numpy array and
the ladder interp is pure integer, so the inner loop has no trig/floor calls.
"""
import numpy as np
from numba import njit

from common.delay import delay_len as _dl

# Delay lengths in samples @44.1kHz
_COMB = (1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617)
_APL = (225, 556, 441)
_APR = (225, 556, 1227)
_LAD = (908, 672)


def _layout(sr):
    """Return (offsets, lens) into a flat buffer for all 8+3+3+2+2=18 delay lines."""
    lens = [_dl(sr, n) for n in _COMB]
    lens += [_dl(sr, n) for n in _APL]
    lens += [_dl(sr, n) for n in _APR]
    lens += [_dl(sr, n) for n in _LAD] * 2
    offs = np.zeros(len(lens) + 1, dtype=np.int64)
    np.cumsum(lens, out=offs[1:])
    return offs, lens


@njit(cache=True)
def _run(x, decay, damp, diffuse, mods, offs, lens, buf):
    """Process all samples. mods: precomputed LFO in [0,width].  buf += state."""
    n = len(x)
    L = np.empty(n)
    R = np.empty(n)
    lp = 0.0
    gain = 0.125  # 1/8 for 8-comb sum

    for i in range(n):
        xin = x[i]

        # 8 parallel combs
        s = 0.0
        for k in range(8):
            off = offs[k]
            d = lens[k]
            p = i % d
            y = buf[off + p]
            buf[off + p] = xin + decay * y
            s += y
        s *= gain

        # L series allpass (3)
        v = s
        for k in range(3):
            off = offs[8 + k]
            d = lens[8 + k]
            p = i % d
            y = buf[off + p]
            buf[off + p] = v + diffuse * y
            v = -diffuse * v + y
        l = v

        # R series allpass (3)
        v = s
        for k in range(3):
            off = offs[11 + k]
            d = lens[11 + k]
            p = i % d
            y = buf[off + p]
            buf[off + p] = v + diffuse * y
            v = -diffuse * v + y
        r = v

        # Ladder allpasses. Modulated delay in [d-1-width, d-1+width] via linear
        # interpolation between the two ring taps d-1 and d samples old.
        m = mods[i]
        for k in range(2):
            off = offs[14 + k]
            d = lens[14 + k]
            i0 = (i + 1) % d
            i1 = i % d
            # L: counter-rotate (first ladder +m, second -m)
            mm = m if k == 0 else -m
            y = (1.0 - mm) * buf[off + i0] + mm * buf[off + i1]
            buf[off + i1] = l + diffuse * y
            l = -diffuse * l + y
            # R: opposite signs
            mm = -m if k == 0 else m
            y = (1.0 - mm) * buf[off + i0] + mm * buf[off + i1]
            buf[off + i1] = r + diffuse * y
            r = -diffuse * r + y

        # Damping lowpass (both channels for balance)
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
        n = len(x)
        r_ = 2 * np.pi * self.rate / self.sr
        mods = self.width * (0.5 + 0.5 * np.sin(r_ * np.arange(n)))
        return _run(x, self.decay, self.damp, self.diffuse, mods, offs, lens, buf)