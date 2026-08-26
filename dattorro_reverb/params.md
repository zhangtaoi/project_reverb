# Reverb Parameter Reference (Dattorro)

All user-tunable parameters live here. `demo.py` reads them from this file.

## Algorithm params (Dattorro 1997)

| name    | range    | default | meaning |
|---------|----------|---------|---------|
| decay   | 0.0-0.99 | 0.85    | feedback gain of the 8 parallel comb filters. Higher = longer reverb tail. Its usable range is 0.7-0.95. |
| damp    | 0.0-1.0  | 0.4     | damping lowpass coefficient (on the left wet channel). Higher = darker/harsher tail; Dattorro uses a damping offset interplay with decay. |
| diffuse | 0.0-1.0  | 0.5     | allpass feedback gain (input and series/ladder allpasses). Higher = faster echo density / smoother tail. |
| width   | 0.0-1.0  | 0.25    | maximum modulation depth (fraction of the ladder allpass delay) for the LFO chorus/flutter. |
| rate    | 0.01-10 | 0.5     | LFO rate in Hz that sweeps the ladder allpasses (chorus-like movement). |
| wet_rms_match | true/false | true | normalize wet path RMS to the dry signal, so mix has a consistent "how much reverb vs dry" meaning. |

## Render params (demo.py)

| name    | range  | default | meaning |
|---------|--------|---------|---------|
| mix     | 0-1    | 0.5     | dry/wet blend of the final output: out = (1-mix)*dry + mix*wet |
| loudn_out | dBFS 或 none | none | **default: preserve source loudness** (only pull down if peak would clip). Set to a value like -14 to force output RMS to that loudness. |
| peak_guard | true/false | true | if the final peak exceeds 1.0, pull it down (prevents clipping). |

Note: `decay` and `damp` interact (higher decay needs a higher damp to keep the tail dark/stable).