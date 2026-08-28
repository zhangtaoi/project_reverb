"""Dattorro reverb demo: process a file into a mixed output.

Usage: python -m dattorro_reverb.demo <in> <out>
Params are read from dattorro_reverb/params.md (algorithm + render params),
with each render param also overridable via CLI: --mix=0.4 --loudn_out=-16
"""
import argparse
import os
import sys
from pathlib import Path

# allow `python demo.py` / `python dattorro_reverb/demo.py` to find common/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from common.io import load, save
from common.delay import load_params
from dattorro_reverb.reverb import Reverb

PARAMS = os.path.join(os.path.dirname(__file__), "params.md")


def loudness_match(out, target_db, peak_guard=True):
    """Scale so integrated RMS equals target_db dBFS; pull down only on peak
    overflow (never make a quiet render louder than its peaks allow)."""
    rms = np.sqrt(np.mean(out ** 2))
    if rms <= 0:
        return out
    gain = 10 ** (target_db / 20) / rms
    out = out * gain
    if peak_guard and np.abs(out).max() > 1.0:
        out = out / np.abs(out).max()
    return out


def finalize(out, loudn=None, peak_guard=True):
    """Default: preserve source loudness, only prevent clipping.  If `loudn`
    is an absolute dBFS target, force output to that loudness instead."""
    if loudn is None:
        peak = np.abs(out).max()
        if peak_guard and peak > 1.0:
            out = out / peak
    else:
        out = loudness_match(out, loudn, peak_guard)
    return out


def render(data, sr, p):
    mono = data.mean(axis=1) if data.ndim > 1 else data
    rv = Reverb(sr, pre_delay=p["pre_delay"], pre_filter=p["pre_filter"],
                input_diffusion1=p["input_diffusion1"],
                input_diffusion2=p["input_diffusion2"],
                decay=p["decay"], decay_diffusion=p["decay_diffusion"],
                damping=p["damping"])
    L, R = rv.process(mono)
    wet = np.stack([L, R], axis=1)
    if p.get("wet_rms_match", True):
        # match wet RMS to dry so mix has a stable meaning
        g = np.sqrt(np.mean(mono ** 2)) / np.sqrt(np.mean(wet ** 2) + 1e-12)
        wet = wet * g
    out = (1 - p["mix"]) * data + p["mix"] * wet
    return finalize(out, p.get("loudn_out"), p.get("peak_guard", True))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--params", default=PARAMS)
    ap.add_argument("--mix", type=float)
    ap.add_argument("--loudn_out", type=float)
    a = ap.parse_args()

    p = load_params(a.params, {
        "pre_delay": 0.1, "pre_filter": 0.85,
        "input_diffusion1": 0.75, "input_diffusion2": 0.625,
        "decay": 0.75, "decay_diffusion": 0.70, "damping": 0.95,
        "mix": 0.5, "wet_rms_match": True, "loudn_out": None, "peak_guard": True,
    })
    for k, v in (("mix", a.mix), ("loudn_out", a.loudn_out)):
        if v is not None:
            p[k] = v

    data, sr = load(a.src)
    out = render(data, sr, p)
    save(a.dst, out.astype(np.float32), sr)
    print(f"wrote {a.dst}  ({out.shape[0]} frames @ {sr}Hz, mix={p['mix']}, "
          f"RMS={np.sqrt(np.mean(out**2)):.3f})")


if __name__ == "__main__":
    main()