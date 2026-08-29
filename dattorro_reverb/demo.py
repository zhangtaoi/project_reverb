"""Dattorro reverb demo: process a file into a mixed output.

Usage: python -m dattorro_reverb.demo <in> <out> [--preset=hall] [--mix=0.5]
Params are read from dattorro_reverb/params.md (algorithm + render params),
with each render param also overridable via CLI.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from common.io import load, save
from common.delay import load_params, load_presets
from common.dsp import soft_limiter
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


def finalize(out, loudn=None, peak_guard=True, limiter_params=None):
    """Default: preserve source loudness, only prevent clipping.  If `loudn`
    is an absolute dBFS target, force output to that loudness instead."""
    if loudn is not None:
        out = loudness_match(out, loudn, peak_guard)
    if limiter_params:
        out = soft_limiter(out, **limiter_params)
    elif peak_guard:
        # Fallback: only if no limiter configured
        peak = np.abs(out).max()
        if peak > 1.0:
            out = out / peak
    return out


def render(data, sr, p):
    rv = Reverb(sr, pre_delay=p["pre_delay"], pre_filter=p["pre_filter"],
                input_diffusion1=p["input_diffusion1"],
                input_diffusion2=p["input_diffusion2"],
                decay=p["decay"], decay_diffusion=p["decay_diffusion"],
                damping=p["damping"])
    wet = rv.process(data)
    if p.get("wet_rms_match", True):
        dry_rms = np.sqrt(np.mean(data ** 2))
        wet_rms = np.sqrt(np.mean(wet ** 2) + 1e-12)
        wet = wet * (dry_rms / wet_rms)
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
    ap.add_argument("--preset", default=None, help="preset name: plate, room, hall")
    ap.add_argument("--mix", type=float)
    ap.add_argument("--loudn_out", type=float)
    a = ap.parse_args()

    p = load_params(a.params, {
        "src": "data/One More Light.wav",
        "dst": "output/output.wav",
        "pre_delay": 0.1, "pre_filter": 0.85,
        "input_diffusion1": 0.75, "input_diffusion2": 0.625,
        "decay": 0.75, "decay_diffusion": 0.70, "damping": 0.95,
        "mix": 0.5, "wet_rms_match": True, "loudn_out": None, "peak_guard": True,
        "limiter_threshold": None, "limiter_knee": 0.05,
        "limiter_attack_ms": 1.0, "limiter_release_ms": 50.0,
    })
    # Apply preset if given
    if a.preset:
        presets = load_presets(a.params)
        if a.preset in presets:
            p.update(presets[a.preset])
            print(f"Preset: {a.preset}")
        else:
            print(f"Warning: unknown preset '{a.preset}', using defaults")
    # CLI overrides
    for k, v in (("mix", a.mix), ("loudn_out", a.loudn_out)):
        if v is not None:
            p[k] = v

    src = a.src if a.src else p["src"]
    dst = a.dst if a.dst else p["dst"]

    data, sr = load(src)
    out = render(data, sr, p)
    save(dst, out.astype(np.float32), sr)
    print(f"wrote {dst}  ({out.shape[0]} frames @ {sr}Hz, mix={p['mix']}, "
          f"RMS={np.sqrt(np.mean(out**2)):.3f})")


if __name__ == "__main__":
    main()