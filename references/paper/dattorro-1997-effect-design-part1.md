# Dattorro, J. "Effect Design — Part 1: Reverberator and Other Filters"

Journal of the Audio Engineering Society, Vol. 45, No. 9, 1997.

## 链接

- [Stanford CCRMA 存档](https://ccrma.stanford.edu/~dattorro/EffectDesignPart1.pdf)

## 核心贡献

定义了"figure-of-eight"混响槽拓扑结构，包含：
- pre-delay + pre-filter (LPF)
- 4 级 input diffusion（串联全通）
- 2 条对称 tank 路径，cross-feedback 互连
- 调制全通（decay diffusion 1）+ 阻尼（LPF）+ 全通（decay diffusion 2）
- 多 tap 加权求和输出

## 参数体系

论文给出了具体的延迟长度（@44.1kHz）、增益系数和调制方案，本实现直接引用。

## 关系

- 论文忠实实现见 `dattorro_reverb/`
- 紧凑变体见 `dattorro_comb/`
- 参考的开源实现见 `references/openSource/el-visio-dattorro-verb.md`