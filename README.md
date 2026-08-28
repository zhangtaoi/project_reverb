# Project Reverb

持续迭代高级混响算法，以 MVP 为先、调研先行、模块化复用。

## 目录

- `common/`  —— 公共函数库（音频 I/O、延迟线、参数解析），两算法共享
- `dattorro_reverb/` —— **Dattorro 1997 数字混响**（忠实论文拓扑）
- `fdn_reverb/`      —— **FDN 反馈延迟网络**（理论派，待实现）
- `tests/`           —— 单元测试

## 算法

| 目录 | 风格 | 拓扑 | 特点 |
|---|---|---|---|
| `dattorro_reverb/` | 论文忠实版 | pre-delay → pre-filter → 4 input diffusion → 2 tank halves(cross-feedback) → 6 tap 输出 | 稠密厚重，论文原味 |
| `dattorro_comb/` | 紧凑简化版 | 8 并联梳状 → 2×(3 串联全通) → 2 梯形全通(LFO) → 阻尼 | 轻量明亮，修改自由 |

### 使用

```bash
# 论文忠实版
python -m dattorro_reverb.demo "One More Light.wav" output.wav

# 紧凑简化版
python -m dattorro_comb.demo "One More Light.wav" output.wav
```

参数统一在各自文件夹的 `params.md` 配置，也可 CLI 覆盖：
```bash
python -m dattorro_reverb.demo in.wav out.wav --mix=0.4 --loudn_out=-16
```

### 启动器

`run.bat` — 改顶部 `SRC / DST / MIX / LOUDN` 四行，双击即可。

### 性能

Numba JIT 编译，约 2× 实时。