# 阅读清单

建议先读 L1/L2，跑通本仓库案例，再按路线阅读 L5/L6/L7；L3/L4 用于工具与方法比较，L8/L9 用于进阶。以下延续资料盘点时核查的正式版本；不捆绑出版社 PDF。

## L1 · 全局入门

Seaberg et al. (2019). [Wavefront sensing at X-ray free-electron lasers](https://journals.iucr.org/s/issues/2019/04/00/xl5031/index.html). DOI: `10.1107/S1600577519005721`.

认识散斑与两种光栅测量的实验用途和取舍

## L2 · 散斑基础

Zdora (2018). [State of the Art of X-ray Speckle-Based Phase-Contrast and Dark-Field Imaging](https://www.mdpi.com/2313-433X/4/5/60). DOI: `10.3390/jimaging4050060`.

理解近场散斑、不同采集模式、相位与暗场

## L3 · 第一套实操

Hu, Wang & Sawhney (2024). [Spexwavepy: an open-source Python package for X-ray wavefront sensing using speckle-based techniques](https://journals.iucr.org/s/issues/2024/05/00/xt5025/index.html). DOI: `10.1107/S1600577524005861`.

论文、软件、文档、公开数据四者配套

## L4 · 算法对照

Celestre et al. (2025期刊卷；2024 online). [Review and experimental comparison of speckle-tracking algorithms for X-ray phase contrast imaging](https://journals.iucr.org/s/issues/2025/01/00/tv5066/index.html). DOI: `10.1107/S1600577524010117`.

比较算法条件及数据量，避免只以运行速度选方法

## L5 · 你的散斑工具

Qiao et al. (2020). [Wavelet-transform-based speckle vector tracking method for X-ray phase imaging](https://doi.org/10.1364/OE.404606). DOI: `10.1364/OE.404606`.

连接小波描述子与本机WSVT实现

## L6 · 光栅路线

Liu et al. (2020). [X-ray free-electron laser wavefront sensing using the fractional Talbot effect](https://journals.iucr.org/s/issues/2020/02/00/yi5084/index.html). DOI: `10.1107/S1600577519017107`.

理解自成像、几何放大、条纹与相对/绝对标定

## L7 · Hartmann路线

de La Rochefoucauld et al. (2021). [EUV and Hard X-ray Hartmann Wavefront Sensing for Optical Metrology, Alignment and Phase Imaging](https://www.mdpi.com/1424-8220/21/3/874). DOI: `10.3390/s21030874`.

理解孔阵列、质心、参考标定和斜率重建

## L8 · 进阶深度学习

Qiao et al. (2022). [Real-time X-ray phase-contrast imaging using SPINNet—a speckle-based phase-contrast imaging neural network](https://doi.org/10.1364/OPTICA.453748). DOI: `10.1364/OPTICA.453748`.

原始监督SPINNet与本机后续研究模型分别介绍

## L9 · 进阶传统基线

De Marco et al. (2023). [High-speed processing of X-ray wavefront marking data with the Unified Modulated Pattern Analysis (UMPA) model](https://eprints.soton.ac.uk/473889/). DOI: `10.1364/OE.474794`.

连接透射、位移与暗场联合拟合以及工程实现
