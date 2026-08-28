# Reverb Parameter Reference (Dattorro Comb)

Simplified comb-based Dattorro variant. 8 parallel combs -> 2x(3 series allpass) -> 2 ladder allpass.

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
| peak_guard | true/false | true | pull down if peak exceeds 1.0. |