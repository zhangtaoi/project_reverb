# Project Reverb

持续迭代高级混响算法，以 MVP 为先、调研先行、模块化复用。

## 项目结构

```
project_reverb/
├── common/                  # 公共库（两算法共享）
│   ├── io.py                # WAV/MP3 读写（load / save）
│   ├── delay.py             # 延迟线工具（delay_len / load_params / load_presets）
│   └── dsp.py               # DSP 工具（soft_limiter）
│
├── dattorro_reverb/         # Dattorro 1997 论文忠实版（tank 拓扑）
│   ├── reverb.py            # 核心引擎（Numba JIT）
│   ├── demo.py              # 渲染入口
│   └── params.md            # 参数配置 + 预设
│
├── dattorro_comb/           # Dattorro 紧凑简化版（8 梳状）
│   ├── reverb.py            # 核心引擎
│   ├── demo.py              # 渲染入口
│   └── params.md            # 参数配置
│
├── fdn_reverb/              # FDN 反馈延迟网络（待实现）
│
├── data/                    # 输入音频文件
│   ├── One More Light.wav
│   ├── One More Light-44.1k.wav
│   └── ...
│
├── output/                  # 渲染输出（.gitignore 排除）
│
├── tests/                   # 单元测试
│   ├── test_dattorro.py     # tank 引擎测试（30 条）
│   ├── test_dattorro_comb.py# comb 引擎测试（6 条）
│   └── test_delay.py        # 公共库测试（13 条）
│
├── references/              # 论文与开源项目参考
│   ├── paper/               # 学术论文
│   └── openSource/          # 开源实现
│
├── tmp/el_visio/            # C 参考实现（el-visio/dattorro-verb）
│
├── run.bat                  # 一键启动器
├── todo.md                  # 项目宗旨
├── 开发记录.md               # 核心决策与技术问答
└── README.md                # 本文件
```

## 算法概览

| 目录 | 风格 | 拓扑 | 性能 | 特点 |
|---|---|---|---|---|
| `dattorro_reverb/` | 论文忠实版 | pre-delay → pre-filter → 4 input diffusion → 2 tank halves(cross-feedback) → 6 tap 输出 | ~23× 实时（stereo） | 稠密厚重，论文原味 |
| `dattorro_comb/` | 紧凑简化版 | 8 并联梳状 → 2×(3 串联全通) → 2 梯形全通(LFO) → 阻尼 | ~400× 实时 | 轻量明亮，修改自由 |
| `fdn_reverb/` | 理论派 | FDN 反馈延迟网络（待实现） | — | 严格频谱控制 |

## 快速开始

### 方式一：双击 run.bat

编辑 `run.bat` 顶部参数，双击即可。

### 方式二：命令行

```bash
# 论文忠实版（默认参数）
python -m dattorro_reverb.demo

# 指定预设
python -m dattorro_reverb.demo --preset=hall

# 指定文件
python -m dattorro_reverb.demo data/input.wav output/my_reverb.wav

# 紧凑简化版
python -m dattorro_comb.demo data/input.wav output/output.wav
```

### 预设

| 预设 | 参数特点 | 听感 |
|---|---|---|
| `hall` | decay=0.85, damping=0.95 | 长尾、宽阔大气 |
| `plate` | decay=0.50, diffusion=0.80 | 短促、明亮致密 |
| `room` | decay=0.65, damping=0.85 | 自然、房间感 |

### 参数体系

所有参数统一在 `params.md` 管理，支持：

- **算法参数**：`pre_delay`, `pre_filter`, `input_diffusion1/2`, `decay`, `decay_diffusion`, `damping`
- **渲染参数**：`mix`, `loudn_out`, `peak_guard`, `limiter_*`
- **输入输出路径**：`src`, `dst`（可在 `params.md` 中配置，无需每次敲命令行）
- **预设系统**：`## Preset: plate/room/hall` 区段，`--preset` 切换

CLI 参数可覆盖 `params.md` 中的值：
```bash
python -m dattorro_reverb.demo --preset=hall --mix=0.3 --loudn_out=-14
```

## 单元测试

```bash
python -m unittest discover tests -v
```

测试覆盖：冲激响应验证、参数边界稳定性、mix=0 透明性、WAV 读写一致性、参数解析。

**tests/ 的作用：** 每次改代码后跑一遍，确认没改坏东西。不依赖任何音频文件（测试信号由代码生成）。

## 与 C 参考实现的对比

`tmp/el_visio/` 包含 [el-visio/dattorro-verb](https://github.com/el-visio/dattorro-verb) 的源码和编译脚本。

```bash
# 编译并运行 C 版 demo
tmp\el_visio\build_demo.bat
```

44.1kHz 下相关性 0.87，RMS 一致（0.154 vs 0.154），听感差异不大。详细差异见 `开发记录.md`。

## 数据流

```
输入音频文件 (data/ *.wav)
  → common/io.py::load()
  → 降采样到 mono 或保持立体声
  → Reverb.process() 引擎
  → 输出 wet 信号 (L, R)
  → wet_rms_match 归一化
  → mix 混合 (1-mix)*dry + mix*wet
  → soft_limiter / loudness_match
  → common/io.py::save()
  → 输出文件 (output/ *.wav)
```