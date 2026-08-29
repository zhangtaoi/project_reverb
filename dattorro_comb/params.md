# Reverb Parameter Reference (Dattorro Comb)

## Input / Output

| name    | default | meaning |
|---------|---------|---------|
| src     | data/One More Light.wav | input audio file path |
| dst     | output/output.wav | output audio file path |

## Algorithm params

| name    | range    | default | meaning |
|---------|----------|---------|---------|
| decay   | 0.0-0.99 | 0.85    | comb feedback gain. Higher = longer reverb tail. |
| damp    | 0.0-1.0  | 0.4     | damping lowpass coefficient. Higher = darker tail. |
| diffuse | 0.0-1.0  | 0.5     | allpass feedback gain. Higher = faster echo density. |
| width   | 0.0-1.0  | 0.25    | LFO modulation depth (fraction of ladder delay). |
| rate    | 0.01-10  | 0.5     | LFO rate in Hz. |

## Render params

| name    | range  | default | meaning |
|---------|--------|---------|---------|
| mix     | 0-1    | 0.5     | dry/wet blend: out = (1-mix)*dry + mix*wet |
| loudn_out | dBFS 或 none | none | preserve source loudness; set to -14 to force RMS to that level. |
| peak_guard | true/false | true | if the final peak exceeds 1.0, pull it down. |
| limiter_threshold | 0.0-1.0 | none | soft limiter threshold (linear). 0.95 = -0.45 dBFS. |
| limiter_knee | 0.0-0.2 | 0.05 | soft knee width. |
| limiter_attack_ms | 0.1-10.0 | 1.0 | limiter attack time in ms. |
| limiter_release_ms | 10.0-500.0 | 50.0 | limiter release time in ms. |