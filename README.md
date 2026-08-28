# Project Reverb

持续迭代高级混响算法，以 MVP 为先、调研先行、模块化复用。

## 目录

- `common/`  —— 公共函数库（音频 I/O、延迟线、参数解析），两算法共享
- `dattorro_reverb/` —— **Dattorro 1997 数字混响**（论文忠实版，tank 拓扑）
- `dattorro_comb/`   —— **Dattorro 紧凑变体**（8 梳状简化版）
- `fdn_reverb/`      —— **FDN 反馈延迟网络**（理论派，待实现）
- `tests/`           —— 单元测试
- `references/`      —— 论文与开源项目参考归档
- `output/`          —— 渲染输出（默认目录，.gitignore 排除）
- `tmp/`             —— 临时构建文件（含 C 参考实现源码，.gitignore 排除）

## 算法

| 目录 | 风格 | 拓扑 | 特点 |
|---|---|---|---|
| `dattorro_reverb/` | 论文忠实版 | pre-delay → pre-filter → 4 input diffusion → 2 tank halves(cross-feedback) → 6 tap 输出 | 稠密厚重，论文原味，**参考 C 实现 ** |
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

| 版本 | 性能 |
|---|---|
| `dattorro_reverb/`（tank，13 条延迟线） | ~2× 实时 |
| `dattorro_comb/`（8 梳状，18 条延迟线） | ~4× 实时 |

## C 参考实现

`tmp/el_visio/` 包含 [el-visio/dattorro-verb](https://github.com/el-visio/dattorro-verb) 的源码和编译脚本。
```bash
# 编译并运行 C 版 demo
cmd //c "D:\deepAsh\project_reverb\tmp\el_visio\build_demo.bat"
```

### 对比验证摘要

44.1kHz 下 Correlation 0.87，RMS 一致（0.154 vs 0.154），听感差异不大。
剩余差异来自：采样率缩放策略不同（我们按物理时间缩放，C 代码固定 48kHz）、延迟线缓冲实现方式、浮点累积路径。
详见 [`开发记录.md`](开发记录.md) 第六节。