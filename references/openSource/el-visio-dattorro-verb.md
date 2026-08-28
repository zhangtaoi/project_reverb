# el-visio/dattorro-verb — Jon Dattorro reverb in C

- **URL:** https://github.com/el-visio/dattorro-verb
- **Language:** C
- **Stars:** 61

## 关系

`dattorro_reverb/` 以此实现为蓝本，逐行对照论文。这个 C 实现是目前最忠实原文的版本，延迟长度、参数规则、输出 tap 正负号组合均直接引用。

## 差异

- C 实现用 `malloc` 分配 2^n 大小的环形缓冲（位掩码 wrap）
- 本 Python 实现用扁平 numpy 数组 + 预计算偏移，Numba JIT 编译
- 本实现支持任意采样率（延迟长度按 sr/44100 缩放），C 实现固定 48kHz