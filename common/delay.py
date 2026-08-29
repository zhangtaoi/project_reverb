"""Shared audio processing primitives."""
import yaml
import numpy as np


def delay_len(sr, n):
    """Scale a delay length `n` (defined @44.1kHz) to another sample rate."""
    return max(1, int(round(n * sr / 44100)))


def load_params(yaml_path, default=None):
    """Read a YAML parameter file into a dict (top-level keys only).

    Falls back to `default` if the file can't be read.
    'true'/'false' are YAML-native bools; 'null' is YAML-native None.
    """
    params = dict(default or {})
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            # Only take top-level keys that aren't structural sections
            for k, v in data.items():
                if k not in ("presets",):
                    params[k] = v
    except Exception:
        pass
    return params


def load_presets(yaml_path):
    """Read presets from a YAML file.

    Format:
        presets:
          plate:
            decay: 0.5
            ...

    Returns dict of {name: {param: value}}.
    """
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict) and "presets" in data:
            return data["presets"]
    except Exception:
        pass
    return {}