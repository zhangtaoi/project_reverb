# Project Reverb

持续迭代高级混响算法，以 MVP 为先、调研先行、模块化复用。

## 目录

- `common/`  —— 公共函数库（音频 I/O、延迟线、参数解析），两算法共享
- `dattorro_reverb/` —— **Dattorro 1997 数字混响**（忠实论文拓扑）
- `fdn_reverb/`      —— **FDN 反馈延迟网络**（理论派，待实现）
- `tests/`           —— 单元测试

## Dattorro 混响（当前 MVP）

**重度参考：** [el-visio/dattorro-verb](https://github.com/el-visio/dattorro-verb)（C, 61★）

### 拓扑

```
pre-delay → pre-filter(LP) → 4× input diffusion(allpass)
  → split into 2 tank halves (cross-feedback):
    decay diff 1 (modulated allpass) → pre-damping delay
    → damping(LP) → decay diff 2 (allpass) → post-damping delay
  → output: weighted sum of 6 delay-line tap points
```

### 使用

```bash
python -m dattorro_reverb.demo "One More Light.wav" output.wav
```

参数统一在 `dattorro_reverb/params.md` 配置，也可 CLI 覆盖：
```bash
python -m dattorro_reverb.demo in.wav out.wav --mix=0.4 --loudn_out=-16
```

### 启动器

`run.bat` — 改顶部 `SRC / DST / MIX / LOUDN` 四行，双击即可。

### 性能

Numba JIT 编译，约 2× 实时。