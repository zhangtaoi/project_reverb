# Project Reverb

持续迭代高级混响算法，以 MVP 为先、调研先行、模块化复用。

## 目录

- `common/`  —— 公共函数库（音频 I/O、延迟线、参数解析），两算法共享
- `dattorro_reverb/` —— **经验派** Dattorro 1997 数字混响（手工调优的艺术品）
- `fdn_reverb/`      —— **理论派** FDN 反馈延迟网络（严格频谱控制，待实现）
- `tests/`           —— 单元测试

## Dattorro 混响（当前 MVP）

拓扑：`8×并联梳状 → 2×(3×串联全通) → 2×梯形全通(LFO调制)`。
Mono 入 → 立体声出。

```bash
python -m dattorro_reverb.demo "One More Light.mp3" out.wav
```

参数（decay/damp/diffuse/width/rate/mix/loudn_out…）统一在
`dattorro_reverb/params.md` 配置，也可 CLI 覆盖：`--mix=0.4 --loudn_out=-16`。

性能：纯 Python 逐样本约 1.5× 实时（慢），Numba JIT 后约 4× 实时。
