# Reverb Parameter Reference (Dattorro)

All user-tunable parameters live here. `demo.py` reads them from this file.

## Algorithm params (Dattorro 1997)

| name    | range    | default | meaning |
|---------|----------|---------|---------|
| pre_delay   | 0.0-1.0  | 0.1     | pre-delay length as fraction of max (100ms @48k). |
| pre_filter  | 0.0-1.0  | 0.85    | pre-reverb lowpass filter amount. Higher = darker input. |
| input_diffusion1 | 0.0-1.0 | 0.75 | input diffusion gain (first 2 of 4 allpasses). Echo density. |
| input_diffusion2 | 0.0-1.0 | 0.625 | input diffusion gain (last 2 of 4 allpasses). |
| decay   | 0.0-0.99 | 0.75    | feedback gain of the tank. Higher = longer reverb tail. |
| decay_diffusion | 0.0-1.0 | 0.70 | decay diffusion 1 gain (modulated allpass). Smear/movement. |
| damping | 0.0-1.0  | 0.95    | tank damping lowpass coefficient. Higher = darker tail. |
| wet_rms_match | true/false | true | normalize wet path RMS to the dry signal, so mix has a consistent "how much reverb vs dry" meaning. |

Note: `decay` sets `decay_diffusion_2 = clamp(decay + 0.15, 0.25, 0.50)` per Dattorro paper.

## Render params (demo.py)

| name    | range  | default | meaning |
|---------|--------|---------|---------|
| mix     | 0-1    | 0.5     | dry/wet blend of the final output: out = (1-mix)*dry + mix*wet |
| loudn_out | dBFS 或 none | none | **default: preserve source loudness** (only pull down if peak would clip). Set to a value like -14 to force output RMS to that loudness. |
| peak_guard | true/false | true | if the final peak exceeds 1.0, pull it down (prevents clipping). |