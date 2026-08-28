"""Shared audio processing primitives."""
import numpy as np


def delay_len(sr, n):
    """Scale a delay length `n` (defined @44.1kHz) to another sample rate."""
    return max(1, int(round(n * sr / 44100)))


def load_params(md_path, default=None):
    """Read a `| name | range | default | meaning |` markdown table into a dict.
    Uses the 3rd column (default). Falls back to `default` for missing rows.
    'true'/'false'/'' are mapped to bool/None."""
    params = dict(default or {})
    try:
        with open(md_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("|"):
                    continue
                cells = [c.strip() for c in line.strip("|").split("|")]
                if len(cells) < 3:
                    continue
                if cells[0].startswith("name") or cells[0].startswith("---"):
                    continue
                v = cells[2].strip()
                low = v.lower()
                if low in ("true", "false"):
                    v = low == "true"
                elif low in ("none", "", "null"):
                    v = None
                else:
                    try:
                        v = float(v)
                    except ValueError:
                        pass
                params[cells[0]] = v
    except OSError:
        pass
    return params