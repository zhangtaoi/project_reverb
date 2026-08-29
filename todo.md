# Project Reverb — 开发路线图

## 项目宗旨

持续迭代高级混响算法。MVP 优先，调研先行，模块化复用。
不同算法独立文件夹，公共函数放 `common/`，不重复编写。

## 当前状态

### ✅ 已完成：Dattorro 双版本

| 版本 | 目录 | 拓扑 | 特点 |
|---|---|---|---|
| Tank 版（论文忠实） | `dattorro_reverb/` | pre-delay→pre-filter→4 inDiff→2 tank halves(cross-feedback)→6 tap 输出 | 稠密厚重，参考 C 实现 |
| Comb 版（紧凑简化） | `dattorro_comb/` | 8 并联梳状→2×(3 串联全通)→2 梯形全通(LFO)→阻尼 | 轻量明亮，修改自由 |

### 已完成功能清单
- `common/` 公共库：audio I/O、延迟线、YAML 参数解析、软限幅器
- 性能：mono 400× / stereo 23× 实时（Numba JIT）
- 真立体声输入（双路独立 tank）
- 三套预设：plate（板式）/ room（房间）/ hall（大厅）
- 参数系统：`params.yaml` 集中管理，YAML 注释 + 自动类型推断
- 37 条单元测试：冲激响应、参数边界稳定性、mix=0 透明性、YAML 解析
- 参考实现归档：`tmp/el_visio/`（C 源码 + 编译脚本）
- 与 C 参考实现对比验证（44.1kHz 相关性 0.87）
- 一键启动器 `run.bat`（支持 MODEL=reverb|comb 切换）

### 待打磨（低优先级，可穿插 FDN 阶段做）
- 参数边界校验（decay 接近 1.0 时出警告）
- 预设参数听感微调
- 96kHz 采样率验证
- 冲激响应可视化工具

---

## 下一阶段目标：FDN 反馈延迟网络

### 理论基础

FDN（Feedback Delay Network）是 Dattorro 之外的混响算法另一条路线：
- **Stautner & Puckette (1982)** — 首次提出 FDN 框架
- **Jot & Chaigne (1991)** — 引入无损/有损分析、归一化反馈矩阵、频段独立衰减控制
- 论文归档在 `references/paper/` 下

FDN 比 Dattorro 的优势：
- 有严格的频谱控制理论（矩阵特征值决定衰减）
- 参数更少但控制更精确（延迟长度 + 反馈矩阵 + 衰减时间）
- 更自然的房间声（模式密度分布更接近真实声学）

### 研发计划

```
project_reverb/
├── fdn_reverb/           # 新目录
│   ├── reverb.py         # 核心引擎
│   ├── demo.py           # 渲染入口
│   └── params.yaml       # 参数配置
│
├── common/
│   ├── io.py             # 已有
│   ├── delay.py          # 已有（delay_len, load_params, load_presets）
│   └── dsp.py            # 已有（soft_limiter）
│
├── tests/
│   └── test_fdn.py       # 新增测试
```

### 实施步骤

#### Step 1：调研 — 确定 FDN 架构（1-2 天）
- [ ] 深入阅读 `references/paper/stautner-puckette-1982-fdn.md` 和 `jot-chaigne-1991-fdn.md`
- [ ] 搜索开源 FDN 实现（参考 Dattorro 阶段的调研方法）
- [ ] 确定拓扑结构：延迟线条数（4-16）、反馈矩阵类型（Hadamard / Householder）、衰减控制方式
- [ ] 确定参数体系：decay_time / damping / diffuse / modulation / 各频段衰减
- [ ] 决定 mono→stereo 还是 true stereo 方案
- [ ] 更新 `references/` 归档

#### Step 2：公共库扩展（如有需要）
- [ ] 如有 FDN 特有的公共组件，扩展到 `common/`

#### Step 3：核心引擎 MVP（3-5 天）
- [ ] 实现 `N×` 延迟线 + 反馈矩阵的基础结构
- [ ] 实现无损/有损 FDN 的衰减控制
- [ ] 实现输出混合（tap 加权或延迟线直接输出）
- [ ] 实现谱图修饰（per-band damping）
- [ ] 与 Dattorro 引擎一样用 Numba JIT 编译

#### Step 4：Demo 程序
- [ ] 参照 `dattorro_reverb/demo.py` 的架构，实现 `fdn_reverb/demo.py`
- [ ] 复用 `common/` 的 I/O、YAML 参数解析、软限幅器
- [ ] 支持 `--preset`（预设：small_room / medium_hall / large_cathedral）
- [ ] 更新 `run.bat` 支持 `MODEL=fdn`

#### Step 5：测试（与 Step 3 并行）
- [ ] 冲激响应：尾音衰减、无 NaN、无爆炸
- [ ] 参数边界：高/低 decay_time、高/低 damping
- [ ] mix=0 透明性
- [ ] 采样率缩放一致性
- [ ] 输出不削波

#### Step 6：对比验证
- [ ] 与 Dattorro tank 版 A/B 对比（同素材、同 mix）
- [ ] 与开源 FDN 实现对比（参考 C 实现的模式）
- [ ] 冲激响应可视化：RT60 曲线、回声密度、频率响应

### 关键设计决策（待讨论）

1. **延迟线条数**：4 条（最小可行）→ 8 条（推荐）→ 16 条（极致密度）
2. **反馈矩阵**：Hadamard（简单）vs Householder（更均匀）vs 随机正交矩阵
3. **频谱控制**：全局 damping vs 每频段独立衰减 vs 全通滤波器级联
4. **立体声**：两个独立 FDN（true stereo）vs 单 FDN + 交叉混合
5. **调制**：LFO 调制延迟线 vs 调制反馈矩阵系数

### 参考资料

- `references/paper/stautner-puckette-1982-fdn.md` — FDN 起源论文
- `references/paper/jot-chaigne-1991-fdn.md` — FDN 理论完善
- 调研阶段需搜索的开源项目：freeverb（开源标准）、zita-rev1（FDN 实现）、ir.lv2（FDN 实现）

### 代码风格指南

- 保持简洁：能几行实现的不要写一大段
- 公共函数放 `common/`，不重复编写
- 参数用 `params.yaml` 配置，YAML 注释解释含义
- 核心循环用 Numba `@njit` 编译
- 延迟线用扁平 numpy 数组 + 偏移量预计算（参考 `dattorro_reverb/reverb.py` 的模式）
- 测试不依赖外部音频文件（测试信号由代码生成）

### 架构参考

Dattorro 的 `reverb.py` 是 FDN 的代码架构参考：
- `_layout(sr)` — 计算延迟线偏移和长度
- `_run(x, ...)` — Numba JIT 核心循环
- `Reverb` 类 — 薄封装，`process(x)` 入口
- 1D 输入 → stereo 输出，2D 输入 → true stereo