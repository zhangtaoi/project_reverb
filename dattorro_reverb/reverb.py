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
    mod_delay_0 = lens[5] - 1
    mod_delay_1 = lens[6] - 1

    # Running write pointers for all 13 delay lines
    wp = np.zeros(13, dtype=np.int64)

    for i in range(n):
        xin = x[i]

        # ── Pre-delay (delay line 0) ──
        o = offs[0]; d = lens[0]
        v = buf[o + (wp[0] - pd_delay) % d]
        buf[o + wp[0]] = xin
        wp[0] += 1; wp[0] -= d if wp[0] >= d else 0

        # ── Pre-filter (lowpass) ──
        pf_state += pf_amount * (v - pf_state)
        v = pf_state

        # ── Input diffusion: 4 series allpass (delay lines 1-4) ──
        for k in range(4):
            o = offs[1 + k]; d = lens[1 + k]
            g = id1 if k < 2 else id2
            rp = (wp[1+k] - d) % d
            y = buf[o + rp]
            buf[o + wp[1+k]] = v - g * y
            v = y + g * buf[o + wp[1+k]]
            wp[1+k] += 1; wp[1+k] -= d if wp[1+k] >= d else 0

        # ── Modulation: triangle wave excursion ──
        # Compute mod_delay for both decayDiff1 lines (5, 6) up front
        if (i & 0x7ff) == 0:
            if (i // 2048) % 32 < 16:
                mod_acc = min(16, mod_acc + 1)
            else:
                mod_acc = max(-16, mod_acc - 1)
            mod_delay_0 = max(0, min(lens[5] - 1, lens[5] - 1 + mod_acc))
            mod_delay_1 = max(0, min(lens[6] - 1, lens[6] - 1 + mod_acc))

        # ── Tank: cross-feedback from postDampingDelay (lines 11, 12) ──
        cross0 = buf[offs[11] + (wp[11] - lens[11]) % lens[11]]
        cross1 = buf[offs[12] + (wp[12] - lens[12]) % lens[12]]

        # ── Half 0 ──
        # Cross-feedback from other half's postDampingDelay
        vv = v + cross1 * decay

        # Decay diffusion 1 (line 5, modulated allpass, gain = -dd1)
        o = offs[5]; d = lens[5]; g = -dd1
        rp = (wp[5] - int(mod_delay_0)) % d
        y = buf[o + rp]
        buf[o + wp[5]] = vv - g * y
        vv = y + g * buf[o + wp[5]]
        wp[5] += 1; wp[5] -= d if wp[5] >= d else 0

        # Pre-damping delay (line 7)
        o = offs[7]; d = lens[7]
        rp = (wp[7] - d) % d
        pre_damped = buf[o + rp]
        buf[o + wp[7]] = vv
        wp[7] += 1; wp[7] -= d if wp[7] >= d else 0

        # Damping (lowpass)
        damp_state[0] += damp * (pre_damped - damp_state[0])
        vv = damp_state[0] * decay

        # Decay diffusion 2 (line 9, allpass, gain = dd2)
        o = offs[9]; d = lens[9]; g = dd2
        rp = (wp[9] - d) % d
        y = buf[o + rp]
        buf[o + wp[9]] = vv - g * y
        vv = y + g * buf[o + wp[9]]
        wp[9] += 1; wp[9] -= d if wp[9] >= d else 0

        # Post-damping delay (line 11)
        o = offs[11]; d = lens[11]
        buf[o + wp[11]] = vv
        wp[11] += 1; wp[11] -= d if wp[11] >= d else 0

        # ── Half 1 ──
        vv = v + cross0 * decay

        # Decay diffusion 1 (line 6)
        o = offs[6]; d = lens[6]; g = -dd1
        rp = (wp[6] - int(mod_delay_1)) % d
        y = buf[o + rp]
        buf[o + wp[6]] = vv - g * y
        vv = y + g * buf[o + wp[6]]
        wp[6] += 1; wp[6] -= d if wp[6] >= d else 0

        # Pre-damping delay (line 8)
        o = offs[8]; d = lens[8]
        rp = (wp[8] - d) % d
        pre_damped = buf[o + rp]
        buf[o + wp[8]] = vv
        wp[8] += 1; wp[8] -= d if wp[8] >= d else 0

        # Damping (lowpass)
        damp_state[1] += damp * (pre_damped - damp_state[1])
        vv = damp_state[1] * decay

        # Decay diffusion 2 (line 10)
        o = offs[10]; d = lens[10]; g = dd2
        rp = (wp[10] - d) % d
        y = buf[o + rp]
        buf[o + wp[10]] = vv - g * y
        vv = y + g * buf[o + wp[10]]
        wp[10] += 1; wp[10] -= d if wp[10] >= d else 0

        # Post-damping delay (line 12)
        o = offs[12]; d = lens[12]
        buf[o + wp[12]] = vv
        wp[12] += 1; wp[12] -= d if wp[12] >= d else 0

        # ── Output: weighted sum of 6 taps ──
        # Use running pointers for the 6 output delay lines (7,8,9,10,11,12)
        # Tap read: last written position = wp - 1 (wrapped)
        # Left: from half 1 (+) and half 0 (-)
        # Half 1: preDampDelay (line 8), decayDiff2 (line 10), postDampDelay (line 12)
        o = offs[8]; d = lens[8]; w = wp[8] - 1 + d if wp[8] == 0 else wp[8] - 1
        l = buf[o + (w - pdd_off[1, 0]) % d]
        l += buf[o + (w - pdd_off[1, 1]) % d]
        o = offs[10]; d = lens[10]; w = wp[10] - 1 + d if wp[10] == 0 else wp[10] - 1
        l -= buf[o + (w - dd2_off[1, 1]) % d]
        o = offs[12]; d = lens[12]; w = wp[12] - 1 + d if wp[12] == 0 else wp[12] - 1
        l += buf[o + (w - pod_off[1, 1]) % d]
        # Half 0: preDampDelay (line 7), decayDiff2 (line 9), postDampDelay (line 11)
        o = offs[7]; d = lens[7]; w = wp[7] - 1 + d if wp[7] == 0 else wp[7] - 1
        l -= buf[o + (w - pdd_off[0, 2]) % d]
        o = offs[9]; d = lens[9]; w = wp[9] - 1 + d if wp[9] == 0 else wp[9] - 1
        l -= buf[o + (w - dd2_off[0, 0]) % d]
        o = offs[11]; d = lens[11]; w = wp[11] - 1 + d if wp[11] == 0 else wp[11] - 1
        l += buf[o + (w - pod_off[0, 0]) % d]

        # Right: from half 0 (+) and half 1 (-)
        o = offs[7]; d = lens[7]; w = wp[7] - 1 + d if wp[7] == 0 else wp[7] - 1
        r = buf[o + (w - pdd_off[0, 0]) % d]
        r += buf[o + (w - pdd_off[0, 1]) % d]
        o = offs[9]; d = lens[9]; w = wp[9] - 1 + d if wp[9] == 0 else wp[9] - 1
        r -= buf[o + (w - dd2_off[0, 1]) % d]
        o = offs[11]; d = lens[11]; w = wp[11] - 1 + d if wp[11] == 0 else wp[11] - 1
        r += buf[o + (w - pod_off[0, 1]) % d]
        o = offs[8]; d = lens[8]; w = wp[8] - 1 + d if wp[8] == 0 else wp[8] - 1
        r -= buf[o + (w - pdd_off[1, 2]) % d]
        o = offs[10]; d = lens[10]; w = wp[10] - 1 + d if wp[10] == 0 else wp[10] - 1
        r -= buf[o + (w - dd2_off[1, 0]) % d]
        o = offs[12]; d = lens[12]; w = wp[12] - 1 + d if wp[12] == 0 else wp[12] - 1
        r += buf[o + (w - pod_off[1, 0]) % d]

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
        if x.ndim == 1:
            # Mono input -> stereo output (current behavior)
            return self._process_mono(x)
        else:
            # Stereo input -> true stereo (two independent tanks)
            return self._process_stereo(x)

    def _process_mono(self, x):
        offs, lens = _layout(self.sr)
        buf = np.zeros(offs[-1], dtype=np.float64)
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

    def _process_stereo(self, x):
        """Two independent tanks, one per channel."""
        offs, lens = _layout(self.sr)
        pdd_off = np.zeros((2, 3), dtype=np.int64)
        dd2_off = np.zeros((2, 2), dtype=np.int64)
        pod_off = np.zeros((2, 2), dtype=np.int64)
        for h in range(2):
            for t in range(3):
                pdd_off[h, t] = _dl(self.sr, _PDD_TAPS[h][t])
            for t in range(2):
                dd2_off[h, t] = _dl(self.sr, _DD2_TAPS[h][t])
                pod_off[h, t] = _dl(self.sr, _POD_TAPS[h][t])

        buf0 = np.zeros(offs[-1], dtype=np.float64)
        buf1 = np.zeros(offs[-1], dtype=np.float64)

        L0, R0 = _run(x[:, 0], self.pre_delay, self.pre_filter,
                      self.input_diffusion1, self.input_diffusion2,
                      self.decay, self.decay_diffusion, self.damping,
                      self.sr, offs, lens, buf0, pdd_off, dd2_off, pod_off)
        L1, R1 = _run(x[:, 1], self.pre_delay, self.pre_filter,
                      self.input_diffusion1, self.input_diffusion2,
                      self.decay, self.decay_diffusion, self.damping,
                      self.sr, offs, lens, buf1, pdd_off, dd2_off, pod_off)

        # Each channel's tank produces stereo output.
        # Left output = L channel's L + R channel's L
        # Right output = L channel's R + R channel's R
        out = np.empty((len(x), 2), dtype=np.float64)
        out[:, 0] = L0 + L1
        out[:, 1] = R0 + R1
        return out