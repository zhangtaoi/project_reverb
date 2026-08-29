# Reverb Parameter Reference (Dattorro)

All user-tunable parameters live here. `demo.py` reads them from this file.

## Algorithm params

| name    | range    | default | meaning |
|---------|----------|---------|---------|
| pre_delay   | 0.0-1.0  | 0.1     | pre-delay length as fraction of max (100ms @48k). |
| pre_filter  | 0.0-1.0  | 0.85    | pre-reverb lowpass filter amount. Higher = darker input. |
| input_diffusion1 | 0.0-1.0 | 0.75 | input diffusion gain (first 2 of 4 allpasses). |
| input_diffusion2 | 0.0-1.0 | 0.625 | input diffusion gain (last 2 of 4 allpasses). |
| decay   | 0.0-0.99 | 0.75    | feedback gain of the tank. Higher = longer reverb tail. |
| decay_diffusion | 0.0-1.0 | 0.70 | decay diffusion 1 gain (modulated allpass). |
| damping | 0.0-1.0  | 0.95    | tank damping lowpass coefficient. Higher = darker tail. |
| wet_rms_match | true/false | true | normalize wet path RMS to the dry signal. |

Note: `decay` sets `decay_diffusion_2 = clamp(decay + 0.15, 0.25, 0.50)` per Dattorro paper.

## Render params

| name    | range  | default | meaning |
|---------|--------|---------|---------|
| mix     | 0-1    | 0.5     | dry/wet blend: out = (1-mix)*dry + mix*wet |
| loudn_out | dBFS 或 none | none | preserve source loudness; set to -14 to force RMS to that level. |
| peak_guard | true/false | true | if the final peak exceeds 1.0, pull it down. |
| limiter_threshold | 0.0-1.0 | none | soft limiter threshold (linear). 0.95 = -0.45 dBFS. None = disabled. |
| limiter_knee | 0.0-0.2 | 0.05 | soft knee width (linear). Larger = smoother transition. |
| limiter_attack_ms | 0.1-10.0 | 1.0 | limiter attack time in ms. |
| limiter_release_ms | 10.0-500.0 | 50.0 | limiter release time in ms. |

## Preset: plate

Bright, dense plate reverb. Short decay, high diffusion, low damping.

| name    | default |
|---------|---------|
| pre_delay   | 0.05    |
| pre_filter  | 0.70    |
| input_diffusion1 | 0.80 |
| input_diffusion2 | 0.70 |
| decay   | 0.50    |
| decay_diffusion | 0.80 |
| damping | 0.70    |

## Preset: room

Natural room ambience. Moderate decay, higher damping for absorption.

| name    | default |
|---------|---------|
| pre_delay   | 0.15    |
| pre_filter  | 0.90    |
| input_diffusion1 | 0.70 |
| input_diffusion2 | 0.60 |
| decay   | 0.65    |
| decay_diffusion | 0.60 |
| damping | 0.85    |

## Preset: hall

Lush, spacious hall. Long decay, low damping for airy tail.

| name    | default |
|---------|---------|
| pre_delay   | 0.20    |
| pre_filter  | 0.95    |
| input_diffusion1 | 0.75 |
| input_diffusion2 | 0.625 |
| decay   | 0.85    |
| decay_diffusion | 0.70 |
| damping | 0.95    |