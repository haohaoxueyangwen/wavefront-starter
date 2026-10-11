# 优先读的 7 篇综述与理论总览

不用先把 34 条全部读完。建议先读 L34/L2 的地图，再按主线深入 L12/L4；有物理基础空缺时补 L10，光栅路线重点读 L13/L32。完整引文见 [分类清单](04_reading.md)。

| 文献 | 适合解决的问题 |
|---|---|
| [Zdora, 2018 · L2](04_reading.md#l2) | 散斑入门的第一篇 |
| [Berujon et al., 2020 · L12](04_reading.md#l12) | 散斑波前计量的核心理论总览 |
| [Celestre et al., 2025 · L4](04_reading.md#l4) | 算法选型与实验比较 |
| [Endrizzi, 2018 · L34](04_reading.md#l34) | 整个相位成像领域的地图 |
| [Paganin & Pelliccia, 2021 · L10](04_reading.md#l10) | 相位、传播与逆问题的基础 |
| [Pfeiffer et al., 2013 · L13](04_reading.md#l13) | 光栅多通道信号的基础综述 |
| [Takeda, 2013 · L32](04_reading.md#l32) | 与光栅代码最直接相连的算法综述 |

## L2 · 散斑入门的第一篇

[State of the Art of X-ray Speckle-Based Phase-Contrast and Dark-Field Imaging](https://www.mdpi.com/2313-433X/4/5/60) · DOI [10.3390/jimaging4050060](https://doi.org/10.3390/jimaging4050060)

它将基本原理、实验采集方式和应用放在同一张研究地图中，适合先建立共同术语。

**第一遍读法**：先读概念与采集模式，再辨认哪些模式使用单对图像、哪些需要扫描或图像栈。

**读完接一个练习**：用自己的话说明相位、透射和暗场三种结果分别来自什么观测。然后运行 WXST 与 WSVT 两个示例。

**适用范围**：波前测量只是它讨论的一部分；应用示例的指标不能自动转成本仓库的验收值。

## L12 · 散斑波前计量的核心理论总览

[X-ray optics and beam characterization using random modulation: theory](https://journals.iucr.org/s/issues/2020/02/00/gb5096/index.html) · DOI [10.1107/s1600577520000491](https://doi.org/10.1107/s1600577520000491)

它直接围绕光学元件表征组织 XST、XSVT、XSS，并区分差分与绝对计量。

**第一遍读法**：优先看 metrology modes 与各类处理方案，画出参考图和样品图的几何位置。

**读完接一个练习**：写出自己实验中 reference 的定义、距离起止面与配对方式，再填写真实数据模板。

**适用范围**：本文属于 research papers 栏目，但内容是理论综述；清单明确标作综述型研究论文。

## L4 · 算法选型与实验比较

[Review and experimental comparison of speckle-tracking algorithms for X-ray phase contrast imaging](https://journals.iucr.org/s/issues/2025/01/00/tv5066/index.html) · DOI [10.1107/s1600577524010117](https://doi.org/10.1107/s1600577524010117)

它在统一术语下介绍常见散斑追踪方法，并以不同实验条件比较结果。

**第一遍读法**：先读 explicit 与 implicit tracking 的分类，再看比较的样品和评价方式。

**读完接一个练习**：选择本仓库的一组位移结果，说明误差区域、参考答案和精度/分辨率/计算时间的差别。

**适用范围**：本文未纳入 AI 方法比较，也把暗场计算放在讨论范围之外；不能当作所有方法的完整排名。

## L34 · 整个相位成像领域的地图

[X-ray phase-contrast imaging](https://discovery.ucl.ac.uk/id/eprint/1570214/) · DOI [10.1016/j.nima.2017.07.036](https://doi.org/10.1016/j.nima.2017.07.036)

它提供 X 射线相位成像路线的总体介绍，适合解释波前研究与样品成像的关系。

**第一遍读法**：先读吸收成像基础，再为不同相位敏感技术写出各自的观测量。

**读完接一个练习**：将散斑、光栅和 Hartmann 放进自己的研究地图，标明每个模块当前输出的单位。

**适用范围**：它覆盖更广的成像领域；光学波前计量需要继续读 L1、L12、L27。

## L10 · 相位、传播与逆问题的基础

[X-ray phase-contrast imaging: a broad overview of some fundamentals](https://arxiv.org/abs/2011.05146) · DOI [10.1016/bs.aiep.2021.04.002](https://doi.org/10.1016/bs.aiep.2021.04.002)

它从波动与复场的基本概念讲到传播、部分相干和相位恢复，适合补数学与物理基础。

**第一遍读法**：第一遍读场的强度/相位含义和 Fresnel scaling，再按需要补 forward/inverse problem。

**读完接一个练习**：写清 OPD 与相位的换算，以及相位梯度和偏折角的联系，检查代码配置中的单位。

**适用范围**：这是理论总览书章。arXiv 首版为 2020；正式书章为 2021，引用时按所用版本记录。

## L13 · 光栅多通道信号的基础综述

[Grating-based X-ray phase contrast for biomedical imaging applications](https://www.sciencedirect.com/science/article/pii/S0939388913000263) · DOI [10.1016/j.zemedi.2013.02.002](https://doi.org/10.1016/j.zemedi.2013.02.002)

它讲解光栅相位对比与暗场的信号形成，并介绍实验室光源与断层成像应用。

**第一遍读法**：先读光栅图像怎样提供吸收、相位和散射信息，记录采集与解调方式。

**读完接一个练习**：运行光栅示例，区分条纹相位、标定后的波前梯度和积分得到的波前相位。

**适用范围**：应用重点是生物医学；XFEL 单光栅测量的具体几何与标定另读 L6、L26。

## L32 · 与光栅代码最直接相连的算法综述

[Fourier fringe analysis and its application to metrology of extreme physical phenomena: a review [Invited]](https://opg.optica.org/ao/abstract.cfm?uri=ao-52-1-20) · DOI [10.1364/ao.52.000020](https://doi.org/10.1364/ao.52.000020)

它总结 Fourier fringe analysis，并讨论极端物理现象的计量应用。

**第一遍读法**：围绕载频、频域边带、复包络与相位提取阅读，先和 L31 的原始方法对照。

**读完接一个练习**：在合成图的频谱上确认两个边带，再对应 FFT → 选带 → 移频 → ifft → angle 的计算链。

**适用范围**：这是通用光学条纹计量综述；将条纹相位换算为 X 射线波前仍需要实验灵敏度标定。

## 另外三篇综述

- [Wilkins et al., 2014 · On the evolution and relative merits of hard X-ray phase-contrast imaging methods](04_reading.md#l11)：比较不同相位成像路线及光源、探测器与动态测量约束。
- [Momose, 2017 · Development toward high-resolution X-ray phase imaging](04_reading.md#l14)：理解定量相位成像与显微成像、断层成像的联系。
- [Zong et al., 2025 · Research Progress of Grating-Based X-Ray Phase-Contrast Imaging and Key Devices](04_reading.md#l15)：了解光栅器件、制造和系统路线的新近进展。

Hartmann 入门另读 [L7 技术总览](04_reading.md#l7)，进阶传播建模读 [L28](04_reading.md#l28)；该仪器论文单列，避免混同于纯文献综述。
