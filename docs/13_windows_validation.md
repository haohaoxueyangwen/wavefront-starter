# Windows 0.6.0 验证记录

Windows CPU / GPU 已编译，前端可以自动定位随包程序。下面把已实测的内容和设备范围列清楚。

## 构建与来源

- 算法源：WSVT_CPP `3f418aa71771e9d209af0702b742ac7e7a69aa9a`，与 0.5.0 的 147 项原始文件哈希一致。
- CPU：MSVC 19.29，C++20，OpenMP，FFTW 3.3.5 单精度 + 线程，HDF5 1.12.1；生成 `wsvt_cli.exe`。
- GPU：CUDA 11.6.124、cuFFT、MSVC 19.29；SM60/61/70/75/80/86 + compute86 PTX，保留 `--fmad=false`；生成 `speckle_gpu.exe` 和 `speckle_native.dll`。
- Windows 的对齐分配、restrict 关键字、HDF5 名称长度类型、DLL 导出、内存统计和启动检测通过 `native/windows/prepare_sources.py` 应用到**构建副本**。CUDA 数值内核和原冻结目录未改。
- Python：官方 3.12.10 embeddable x64，Python Software Foundation 签名有效。所有 Python 依赖和原生运行 DLL 随 Windows ZIP 提供。
- 组件许可证、构建副本改动、二进制哈希：[构建记录](../provenance/windows_native_build.json)、[运行组件说明](../provenance/windows-licenses/README.md)。

维护者重建程序：在已配置 MSVC x64 开发环境中使用 `scripts/build_windows_native.py --help`，分别传入 HDF5、FFTW、可再分发 LLVM OpenMP 和 CUDA 的构建路径，再用 `scripts/assemble_windows_native.py` 收集运行 DLL。**这是开发流程；普通使用者下载 Windows 完整包即可。**

## 实测内容

Windows 实测 GPU：**Quadro P5000，SM61，驱动 582.16，约 15 GiB 显存**。其他显卡有编译目标和运行检测，但尚无本轮 Windows 数值验收。历史 Ada / Orin 性能数据仍属于 Linux，见 [原生指南](11_speckle_fast.md)。

64×64 合成数据，WSVT100 原始 uint16、WXST 单对 float32；half10、模板半窗3、cut1、金字塔参数1、迭代1。

| 检查 | 结果 |
|---|---|
| WSVT / WXST，CPU / GPU，分别运行同图和整数平移 | 8 次原生执行完成，输出有限、形状正确 |
| WSVT GPU 低内存 uint16、速度 float32 | 2 次额外执行完成，与速度 uint16 对照保存在原始记录 |
| CPU / GPU 平移图位移对照 | WXST 最大差异约 9.54e-7 px；WSVT 约 8.82e-6 px |
| CPU / GPU 平移图相位对照 | WXST 最大差异约 4.77e-7 rad；WSVT 约 6.26e-7 rad |
| 前端点击加载示例再运行 | WSVT、WXST 的 CPU / GPU 四条路径完成，并生成图表、数值和配置 |
| Python 回归测试 | 44 项通过，包括原完整 Zernike 分析、数据入口和后端契约 |
| JavaScript | 语法检查通过，真实浏览器确认自动程序发现、设备信息、固定 GPU 参数和结果 |
| 独立运行包 | 在另一处“中文 + 空格”目录，清空 Anaconda / CUDA / 构建工具 PATH，以随包 Python 启动和运行 CPU / GPU；保留 NVIDIA 系统驱动 |

具体数组统计、设备、程序哈希和时间范围保存在 [原生执行记录](../validation/windows_native_060.json)；独立包与界面检查见 [运行包记录](../validation/windows_package_060.json)。小图运行时间受进程启动、数据转换和绘图影响，不用来宣称全尺寸 GPU 加速倍数。

## 同图测试发现的数值现象

最初设“同图中央区域最大位移 <0.05 px”作为检查，CPU WXST 未满足。此失败保留在记录中，没有改成“严格零位移通过”。原二次峰拟合使用非对称邻近代价，即使中心像素匹配完全一致，拟合峰也可能有小偏移：本例同图整张输出中最大约 0.185 px（WXST）、0.242 px（WSVT），中位数很接近零；CPU / GPU 都保留这一行为。

平移例子中间区域中位数接近 `ux=+1, uy=-1`。小图的大搜索窗与反射边界会产生局部异常值，不能把边界上的 ±10 px 当作已知真值。这里验证的是部署能够执行、输出契约和本组合成数据的跨后端一致性；真实实验的物理标定、精度和异常区域仍需要自己的数据验证。

## 分发检查

0.6.0 Windows ZIP 不含本机 `.local_runtime.json`、实验数组、实验记录、运行历史或原目录清理备份。CPU / GPU EXE、运行 DLL、Python、依赖、源码、中文文档和第三方来源说明同时提供。当时的工程示例由按钮按固定 seed 生成。0.6.1 已改为随包 BB11 CRL 实测中央裁剪，另见 [真实数据案例](14_crl_example.md)；本页及旧JSON继续保存0.6.0的原始验证事实。

发布页提供 SHA256SUMS；发布后另以匿名下载校验 ZIP 与记录的哈希。完整运行包与源码包分别命名，防止第一次使用的人下载错包。
