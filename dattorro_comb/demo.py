"""Dattorro Comb reverb demo: process a file into a mixed output.

Usage: python -m dattorro_comb.demo <in> <out>
Params are read from dattorro_comb/params.md (algorithm + render params),
with each render param also overridable via CLI: --mix=0.4 --loudn_out=-16
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from common.io import load, save
from common.delay import load_params
from common.dsp import soft_limiter
from dattorro_comb.reverb import Reverb

PARAMS = os.path.join(os.path.dirname(__file__), "params.yaml")
DEFAULT = {
    "decay": 0.85, "damp": 0.4, "diffuse": 0.5,
    "width": 0.25, "rate": 0.5, "mix": 0.5,
    "wet_rms_match": True, "loudn_out": None, "peak_guard": True,
}


def loudness_match(out, target_db, peak_guard=True):
    rms = np.sqrt(np.mean(out ** 2))
    if rms <= 0:
        return out
    gain = 10 ** (target_db / 20) / rms
    out = out * gain
    if peak_guard and np.abs(out).max() > 1.0:
        out = out / np.abs(out).max()
    return out


def finalize(out, loudn=None, peak_guard=True, limiter_params=None):
    if loudn is not None:
        out = loudness_match(out, loudn, peak_guard)
    if limiter_params:
        out = soft_limiter(out, **limiter_params)
    elif peak_guard:
        peak = np.abs(out).max()
        if peak > 1.0:
            out = out / peak
    return out


def render(data, sr, p):
    mono = data.mean(axis=1) if data.ndim > 1 else data
    rv = Reverb(sr, decay=p["decay"], damp=p["damp"], diffuse=p["diffuse"],
                width=p["width"], rate=p["rate"])
    L, R = rv.process(mono)
    wet = np.stack([L, R], axis=1)
    if p.get("wet_rms_match", True):
        g = np.sqrt(np.mean(mono ** 2)) / np.sqrt(np.mean(wet ** 2) + 1e-12)
        wet = wet * g
    sig = (1 - p["mix"]) * data + p["mix"] * wet

    limiter_params = None
    if p.get("limiter_threshold") is not None:
        limiter_params = {
            "threshold": p["limiter_threshold"],
            "knee": p.get("limiter_knee", 0.05),
            "attack_ms": p.get("limiter_attack_ms", 1.0),
            "release_ms": p.get("limiter_release_ms", 50.0),
            "sr": sr,
        }
    return finalize(sig, p.get("loudn_out"), p.get("peak_guard", True), limiter_params)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?", default=None,
                    help="input audio file (default: from params.md)")
    ap.add_argument("dst", nargs="?", default=None,
                    help="output audio file (default: from params.md)")
    ap.add_argument("--params", default=PARAMS)
    ap.add_argument("--mix", type=float)
    ap.add_argument("--loudn_out", type=float)
    a = ap.parse_args()

    p = load_params(a.params, DEFAULT)
    for k, v in (("mix", a.mix), ("loudn_out", a.loudn_out)):
        if v is not None:
            p[k] = v

    src = a.src if a.src else p.get("src", "data/One More Light.wav")
    dst = a.dst if a.dst else p.get("dst", "output/output.wav")
    data, sr = load(src)
    out = render(data, sr, p)
    save(dst, out.astype(np.float32), sr)
    print(f"wrote {dst}  ({out.shape[0]} frames @ {sr}Hz, mix={p['mix']}, "
          f"RMS={np.sqrt(np.mean(out**2)):.3f})")


if __name__ == "__main__":
    main()