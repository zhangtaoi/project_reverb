"""Dattorro 1997 digital reverb — faithful to the original paper.

Reference: https://ccrma.stanford.edu/~dattorro/EffectDesignPart1.pdf
Reference implementation: https://github.com/el-visio/dattorro-verb

Topology:
  pre-delay → pre-filter(LP) → 4× input diffusion(allpass)
  → split into 2 tank halves (cross-feedback):
    decay diff 1 (modulated allpass) → pre-damping delay
    → damping(LP) → decay diff 2 (allpass) → post-damping delay
  → output: weighted sum of 6 delay-line tap points
"""
import numpy as np
from numba import njit, int64

from common.delay import delay_len as _dl

# Delay lengths in samples @44.1kHz (Dattorro paper values)
_PRE_DELAY = 4800
_IN_DIFF = (142, 107, 379, 277)
_DECAY_DIFF1 = (672, 908)
_PRE_DAMP_DELAY = (4453, 4217)
_DECAY_DIFF2 = (1800, 2656)
_POST_DAMP_DELAY = (3720, 3163)

# Output tap delays per half
_PDD_TAPS = ((353, 3627, 1990), (266, 2974, 2111))
_DD2_TAPS = ((187, 1228), (335, 1913))
_POD_TAPS = ((1066, 2673), (121, 1996))


def _layout(sr):
    """Return (offsets, lens) for all 13 delay lines in a flat buffer."""
    lens = [_dl(sr, _PRE_DELAY)]
    for n in _IN_DIFF: lens.append(_dl(sr, n))
    for n in _DECAY_DIFF1: lens.append(_dl(sr, n))
    for n in _PRE_DAMP_DELAY: lens.append(_dl(sr, n))
    for n in _DECAY_DIFF2: lens.append(_dl(sr, n))
    for n in _POST_DAMP_DELAY: lens.append(_dl(sr, n))
    offs = np.empty(len(lens) + 1, dtype=np.int64)
    offs[0] = 0
    for i in range(len(lens)):
        offs[i + 1] = offs[i] + lens[i]
    return offs, lens


@njit(cache=True)
def _run(x, pd_amount, pf_amount, id1, id2, decay, dd1, damp,
         sr, offs, lens, buf, pdd_off, dd2_off, pod_off):
    """Process all samples. buf is delay-line state, modified in-place.
    Layout: 0=preDelay, 1-4=inDiff, 5-6=decayDiff1, 7-8=preDampDelay,
    9-10=decayDiff2, 11-12=postDampDelay."""
    n = len(x)
    L = np.empty(n)
    R = np.empty(n)
    dd2 = max(0.25, min(0.50, decay + 0.15))
    pd_delay = max(1, int(pd_amount * lens[0]))
    pf_state = 0.0
    damp_state = np.zeros(2)
    mod_acc = 0

    # Precompute tap delays
    # (done in process() and passed in) - already allocated

    for i in range(n):
        xin = x[i]

        # ── Pre-delay ──
        o = offs[0]; d = lens[0]
        wp = i % d
        v = buf[o + (wp - pd_delay) % d]
        buf[o + wp] = xin

        # ── Pre-filter (lowpass) ──
        pf_state += pf_amount * (v - pf_state)
        v = pf_state

        # ── Input diffusion: 4 series allpass ──
        for k in range(4):
            o = offs[1 + k]; d = lens[1 + k]
            g = id1 if k < 2 else id2
            wp = i % d
            rp = (wp - d) % d
            y = buf[o + rp]
            buf[o + wp] = v - g * y
            v = y + g * buf[o + wp]

        # ── Modulation: triangle wave excursion ──
        # C code: readOffset-- at t<32768 (delay shortens), readOffset++ at t>=32768 (delay lengthens).
        if (i & 0x7ff) == 0:
            if (i // 2048) % 32 < 16:
                mod_acc = min(16, mod_acc + 1)
            else:
                mod_acc = max(-16, mod_acc - 1)

        # ── Tank with cross-feedback ──
        # cross-feedback from the OTHER half's postDampingDelay
        cross0 = buf[offs[11] + (i - lens[11]) % lens[11]]
        cross1 = buf[offs[12] + (i - lens[12]) % lens[12]]

        for hi in range(2):
            cross = cross1 if hi == 0 else cross0
            vv = v + cross * decay

            # Decay diffusion 1 (modulated allpass, gain = -dd1)
            o = offs[5 + hi]; d = lens[5 + hi]
            g = -dd1
            wp = i % d
            mod_delay = max(0, min(d - 1, d - 1 + mod_acc))
            rp = (wp - int(mod_delay)) % d
            y = buf[o + rp]
            buf[o + wp] = vv - g * y
            vv = y + g * buf[o + wp]

            # Pre-damping delay
            o = offs[7 + hi]; d = lens[7 + hi]
            wp = i % d
            rp = (wp - d) % d
            pre_damped = buf[o + rp]
            buf[o + wp] = vv

            # Damping (lowpass)
            damp_state[hi] += damp * (pre_damped - damp_state[hi])
            vv = damp_state[hi]

            # Decay gain
            vv *= decay

            # Decay diffusion 2 (allpass, gain = dd2)
            o = offs[9 + hi]; d = lens[9 + hi]
            g = dd2
            wp = i % d
            rp = (wp - d) % d
            y = buf[o + rp]
            buf[o + wp] = vv - g * y
            vv = y + g * buf[o + wp]

            # Post-damping delay
            o = offs[11 + hi]; d = lens[11 + hi]
            wp = i % d
            buf[o + wp] = vv

        # ── Output: weighted sum of 6 taps ──
        # Left: from half 1 (+) and half 0 (-)
        o = offs[8]; d = lens[8]; wp = i % d
        l = buf[o + (wp - pdd_off[1, 0]) % d]
        l += buf[o + (wp - pdd_off[1, 1]) % d]
        o = offs[10]; d = lens[10]; wp = i % d
        l -= buf[o + (wp - dd2_off[1, 1]) % d]
        o = offs[12]; d = lens[12]; wp = i % d
        l += buf[o + (wp - pod_off[1, 1]) % d]
        o = offs[7]; d = lens[7]; wp = i % d
        l -= buf[o + (wp - pdd_off[0, 2]) % d]
        o = offs[9]; d = lens[9]; wp = i % d
        l -= buf[o + (wp - dd2_off[0, 0]) % d]
        o = offs[11]; d = lens[11]; wp = i % d
        l += buf[o + (wp - pod_off[0, 0]) % d]

        # Right: from half 0 (+) and half 1 (-)
        o = offs[7]; d = lens[7]; wp = i % d
        r = buf[o + (wp - pdd_off[0, 0]) % d]
        r += buf[o + (wp - pdd_off[0, 1]) % d]
        o = offs[9]; d = lens[9]; wp = i % d
        r -= buf[o + (wp - dd2_off[0, 1]) % d]
        o = offs[11]; d = lens[11]; wp = i % d
        r += buf[o + (wp - pod_off[0, 1]) % d]
        o = offs[8]; d = lens[8]; wp = i % d
        r -= buf[o + (wp - pdd_off[1, 2]) % d]
        o = offs[10]; d = lens[10]; wp = i % d
        r -= buf[o + (wp - dd2_off[1, 0]) % d]
        o = offs[12]; d = lens[12]; wp = i % d
        r += buf[o + (wp - pod_off[1, 0]) % d]

        L[i] = l
        R[i] = r

    return L, R


class Reverb:
    def __init__(self, sr, pre_delay=0.1, pre_filter=0.85,
                 input_diffusion1=0.75, input_diffusion2=0.625,
                 decay=0.75, decay_diffusion=0.70, damping=0.95):
        self.sr = sr
        self.pre_delay = pre_delay
        self.pre_filter = pre_filter
        self.input_diffusion1 = input_diffusion1
        self.input_diffusion2 = input_diffusion2
        self.decay = decay
        self.decay_diffusion = decay_diffusion
        self.damping = damping

    def process(self, x):
        x = np.ascontiguousarray(x, dtype=np.float64)
        offs, lens = _layout(self.sr)
        buf = np.zeros(offs[-1], dtype=np.float64)
        # Precompute tap delays
        pdd_off = np.zeros((2, 3), dtype=np.int64)
        dd2_off = np.zeros((2, 2), dtype=np.int64)
        pod_off = np.zeros((2, 2), dtype=np.int64)
        for h in range(2):
            for t in range(3):
                pdd_off[h, t] = _dl(self.sr, _PDD_TAPS[h][t])
            for t in range(2):
                dd2_off[h, t] = _dl(self.sr, _DD2_TAPS[h][t])
                pod_off[h, t] = _dl(self.sr, _POD_TAPS[h][t])
        return _run(x, self.pre_delay, self.pre_filter,
                    self.input_diffusion1, self.input_diffusion2,
                    self.decay, self.decay_diffusion, self.damping,
                    self.sr, offs, lens, buf, pdd_off, dd2_off, pod_off)