> Windows 用户先看 [解压直接运行指南](12_windows_quickstart.md)，下载 **0.6.0 Windows 完整包**即可使用随包 CPU / GPU。以下 Linux 性能、原生构建和开发命令保留为高级说明；Windows 的实际构建和验收另见 [验证记录](13_windows_validation.md)。

# WSVT / WXST 高速版：从安装到处理实验数据

本资料包 0.5.0 固定使用原算法仓库提交 [`3f418aa71771e9d209af0702b742ac7e7a69aa9a`](https://github.com/haohaoxueyangwen/WSVT_CPP/tree/3f418aa71771e9d209af0702b742ac7e7a69aa9a/speckle_four_editions) 的原生 GPU 源码。调度、缓存、匹配、样条与相位 FFT 在 C++/CUDA/cuFFT 中执行，运行 GPU 可执行文件无需 Python / PyTorch。教学网页需要本仓库的 Python 环境。

源码已经包含在本仓库的 `native/speckle/`，下载 GitHub Release 的完整源码包也能构建。无需在电脑上寻找旧目录。原算法仓库继续维护；教学仓库中的副本是有哈希的固定版本，升级时整体审计，避免两边各改一份。

## 1. 选哪一版

| 设备 / 用途 | 建议入口 | 推荐策略 |
|---|---|---|
| Linux RTX 5880 Ada | `native/speckle/gpu_discrete` | WSVT、WXST：`speed / copy` |
| Jetson AGX Orin | `native/speckle/gpu_jetson` | WSVT：`speed / mapped`；WXST：`speed / copy` |
| GPU 内存不足 | 同一个 GPU 程序 | WSVT 改为 `low-memory`，`chunk=16` |
| Windows x64 | 0.6.0 Windows 完整运行包 | CPU / GPU 程序自动定位；没有兼容 NVIDIA GPU 时使用 CPU |
| 需要任意帧数、模板、迭代或暗场算法 | 原 CPU / Python 算法 | 先做小图，再按实际参数运行 |

这里按**已测设备上可部署、返回完整七项结果的速度配置**选默认值。`speed` 是工作区策略，不能保证所有电脑、所有阶段都最快。服务器 WXST 的旧 GPU 纯求解器曾更快，新版返回完整结果更快，详见第 7 节。0.5.0 原生性能验收平台是 Linux Ada SM89、Linux Orin SM87；0.6.0 另以独立 Windows 移植层构建并在 P5000 SM61 实测。其他 Windows 显卡的检测、目标和实测范围见 Windows 指南。

WSVT 是逐位置对应的时间栈，WXST 是一对图的空间模板，不能互相替换输入：

- **WSVT**：`sample.npy` 与 `reference.npy` 都是 `(100,H,W)`；全尺寸实测输入是原始 uint16。每个像素的时间向量需有变化。样品 / 参考第 k 帧必须对应同一个扫描位置。
- **WXST**：两个输入都是 `(H,W)` float32；一个参考图与一个样品图。
- 两边形状、类型、ROI 一致；使用二维灰度图，不能把 RGB 通道当扫描帧。原生文件入口为小端、C 连续 NPY v1/v2，不接收压缩 NPZ / TIFF。
- H/W 均大于 28，且当前实现检查 `H*W*100 <= 2147483647`。2048² 已测；其他尺寸先小规模检查。大图能否运行还取决于可用内存。

## 2. 安装和构建

先按[仓库安装说明](../README.md)安装教学网页。只运行 GPU CLI 时不需要安装教学 Python 依赖。以下在 Linux Bash、仓库根目录执行；CUDA Toolkit 中必须有 nvcc，只有显卡驱动不够。

```bash
# Ada：已测 CUDA 12.8 / GCC 12。按本机实际 Toolkit 路径修改。
cmake -S native/speckle/gpu_discrete -B native/speckle/build_desktop \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.8/bin/nvcc \
  -DCUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda-12.8
cmake --build native/speckle/build_desktop -j2
native/speckle/build_desktop/bin/speckle_gpu --help
ldd native/speckle/build_desktop/bin/speckle_gpu

# Orin：已测 CUDA 11.4 / GCC 9.4。
cmake -S native/speckle/gpu_jetson -B native/speckle/build_jetson \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc \
  -DCUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda
cmake --build native/speckle/build_jetson -j2
native/speckle/build_jetson/bin/speckle_gpu --help
```

GPU 需要 CMake≥3.16、C++17、CUDA、cuFFT；保留 `--fmad=false` 和 SM89 / SM87 设置。`ldd` 中 cuFFT / cudart 不能显示 `not found`；运行时需保留旁边的 `lib/`，不能只拷贝一个 bin 文件。`tools/build_native.py` 是可选构建及编译哈希记录工具；不是求解运行依赖。

CPU 需要 CMake≥3.21、C++20、OpenMP、单精度 FFTW 及线程库；网页 CPU 桥接还需要原生 HDF5 IO。Ubuntu 可通过系统包安装 `build-essential cmake pkg-config libfftw3-dev libhdf5-dev`，然后：

```bash
cmake -S native/speckle/cpu_cpp/source -B native/speckle/build_cpu \
  -DCMAKE_BUILD_TYPE=Release -DWSVT_WITH_OPENCV=OFF \
  -DWSVT_WITH_HDF5=ON -DWSVT_WITH_FFTW=ON \
  -DWSVT_BUILD_TESTS=OFF -DWSVT_BUILD_BENCH=OFF
cmake --build native/speckle/build_cpu --target wsvt_cli -j2
```

确认构建输出含 `HDF5 enabled`、`FFTW3 (single precision) enabled`、`FFTW3 threading support enabled`。CMake 有慢速 DFT 兜底，缺少 FFTW 时即使构建成功也不适合处理大图。Windows 用户使用已经编译的 0.6.0 完整运行包；开发者重建 Windows 程序的方法与实际验证记录另见 docs/13_windows_validation.md。

## 3. 先生成小示例

下面只生成合成数据，不启动 GPU；不会读取实验目录。

```bash
python scripts/make_native_speckle_demo.py --out demo_data/native_small
python native/speckle/tools/convert_inputs.py --mode wxst \
  --npz demo_data/native_small/wxst.npz --out demo_data/native_small/wxst_npy
python native/speckle/tools/convert_inputs.py --mode wsvt \
  --npz demo_data/native_small/wsvt.npz --out demo_data/native_small/wsvt_npy
```

示例为 64²、固定种子；WSVT 为 100 帧 uint16；WXST 为 float32。样品图相对参考图在数组上向右 1 像素、向上 1 像素平移，生成方式和输入哈希写入 `manifest.json`。这是检查输入、方向和输出的练习，不是新的精度验收数据集。移位边界应避开；偏折角和相位先去掉均值，因此常量图像位移不会产生可恢复的绝对倾斜波前。

用真实实验 TIFF 时，一次性转换（需 `numpy`、`tifffile`）：

```bash
python -m pip install numpy==1.26.4 tifffile==2024.9.20
python native/speckle/tools/convert_inputs.py --mode wsvt \
  --sample-glob '/data/sample/frame_*.tif' \
  --reference-glob '/data/reference/frame_*.tif' --out converted_wsvt
```

转换器按**字典序**排列；用补零编号 `000…099`，先核对文件数量和对应关系。网页配对表按自然编号排序，与这个离线工具不同。转换结果有 `input_manifest.json`，原 TIFF 不改动。WXST 的每个 glob 必须只匹配一张图。离线转换器全尺寸 WSVT 入口只接受 100 帧 uint16；暗 / 平场校正后的浮点数据应自行导出 float32 NPY，不能强制转回 uint16。

## 4. 跑一次，检查结果

下面的物理量是**合成示例的几何设置**。实验时必须替换为真实能量、有效像元和传播距离。每次输出选新目录，程序拒绝覆盖已有目录。

```bash
bash native/speckle/gpu_discrete/run.sh --mode wxst \
  --sample demo_data/native_small/wxst_npy/sample.npy \
  --reference demo_data/native_small/wxst_npy/reference.npy \
  --out outputs/native_wxst_first \
  --pixel-m 1.625e-6 --distance-m .4845 --energy-ev 12400 \
  --warmup 0 --repeats 1

bash native/speckle/gpu_jetson/run.sh --mode wsvt \
  --sample demo_data/native_small/wsvt_npy/sample.npy \
  --reference demo_data/native_small/wsvt_npy/reference.npy \
  --out outputs/native_wsvt_first \
  --pixel-m 1.625e-6 --distance-m .4845 --energy-ev 12400 \
  --warmup 0 --repeats 1
```

不要在 Ada 上用 Jetson 命令。服务器 WSVT 换成 `gpu_discrete/run.sh`；Orin WXST 换成 `gpu_jetson/run.sh`。速度启动脚本会按平台选择输入策略，仍可通过命令行覆盖。低内存：加 `--workspace low-memory --chunk 16`。

| 原生输出 | 单位 | 形状 / 坐标 |
|---|---|---|
| `displace_x.npy`、`displace_y.npy` | px | `(H-20,W-20)`；原图起点 `(x,y)=(10,10)` |
| `DPC_x.npy`、`DPC_y.npy` | rad | 相对参考的去均值偏折角，同上 |
| `phase.npy` | rad | 保留原 GPU 符号与 Fourier 积分约定，piston 去除 |
| `transmission.npy` | 无量纲 | `(H,W)`；原图起点 `(0,0)`，不能直接和裁边波前逐点叠加 |
| `match_score_neg_ssd.npy` | 算法分数 | `(H-20,W-20)`；负 SSD，不能当暗场量或相位误差 |
| `report.json` | 元数据 | 实际设备、类型、策略、几何、初始化 / IO / 求解器时间和内存范围 |
| `timing.csv` | s | 每个正式重复的 solver / API / reference / sample / download |

先检查字段齐全、形状、有限值、位移符号和裁边坐标，再看相位。`phase` 是 rad；换算 OPD：`OPD_m = phase_rad * wavelength_m / (2π)`，波长 `1.239841984e-6 / energy_ev` m。绝对 piston 和倾斜依赖额外参考，不能从去均值结果补猜。

## 5. 用散斑网页操作

1. 在**实际装有构建产物的主机**启动 `python -m wfs_starter ui --app speckle`。本地网页调用本机程序，不会自动 SSH 到服务器 / Orin。
2. 选择 WXST 或 WSVT。WXST 浏览选择两张图；WSVT 浏览选择两个文件夹，核对全部 100 行配对。选择 ROI 后两边使用同一裁块。
3. Windows 完整包选择 CPU / GPU 后程序自动定位。Linux 构建后把 `build_desktop/bin/speckle_gpu` 或 `build_jetson/bin/speckle_gpu` 加到 PATH，或启动前设置 `WFS_GPU_EXE`；开发者也可在配置 JSON 中显式指定路径。普通界面不再要求填写 EXE。
4. 填能量 eV、像元 m、距离 m。工作区默认 `speed`，输入策略默认自动；Orin WSVT 自动 mapped，其余 copy。GPU 编号从 0 开始。低内存只用于 WSVT。
5. 核对固定参数，运行并查看日志与结果。导出的配置保存实际选项；结果 `metadata.json` 保留二进制 SHA256 和原生报告，`results.npz` 收齐七项结果。页面中的 `ux_px / uy_px / phase_rad / angle_*_rad_demeaned` 分别对应上述原生字段。

Python / CPU 的原参数仍可修改。新版 GPU 是专项内核，固定半窗10、粗搜索5、精搜索4、WXST7×7、原始层+一次降采样（网页 `pyramid_level=1`）、cut1、I1、小波开启、GPU 样条、无暗场。不能改成任意参数后声称 GPU 已执行；需要任意参数时明确选择 CPU / Python。旧的物化路径、CPU 样条和 `WFS_GPU_SOURCE` 不再是教学前端的 GPU 入口，旧源码仍在原算法仓库保留。

网页读入无校正 uint16 WSVT 时保留原始类型；做暗 / 平场校正后按浮点处理，不量化回 uint16。显式选择 uint16 而数据已是浮点会报错。新版全尺寸实测使用 uint16，float32 WSVT 只做过小图验证。

网页每次任务生成临时 NPY 并启动新 CLI，`warmup=0 / repeats=1 / reference-policy=each-pair`。因此界面总耗时包含 Python 读图、转换、进程启动、初始化和图表输出，**不能等同于下面复用会话的热运行时间**。连续采集要复用 C++ 会话和固定页输入 / 输出，见[原生 API 与所有权](../native/speckle/docs/NATIVE_API.md)。

## 6. 参数字典

| 参数 | 含义与使用规则 |
|---|---|
| `--mode` | wxst 单对 / wsvt 100帧；必填 |
| `--sample / --reference` | 同形状、同类型的原生 NPY；必填 |
| `--out` | 尚不存在的新输出目录；必填 |
| `--pixel-m` | 有效像元 m，正有限值；必填 |
| `--distance-m` | 本实验定义的传播距离 m，正有限值；必填 |
| `--energy-ev` | 光子能量 eV，正有限值；必填 |
| `--platform` | desktop / jetson；构建预设决定默认值 |
| `--workspace` | speed / low-memory；默认 speed，低内存只作为 WSVT 选项 |
| `--input-policy` | copy / mapped；二进制默认 copy，启动脚本为 Orin WSVT 选择 mapped |
| `--chunk` | 1–100 整数，默认16；WSVT low-memory 的空间下采样分块 |
| `--device` | CUDA 设备编号，默认0；不跨 GPU 分摊一个会话 |
| `--warmup` | 不计统计的预热次数，默认1；首次试运行可0 |
| `--repeats` | 正式测量次数，默认5，至少1 |
| `--reference-policy` | each-pair 默认，每对重建参考；cache 仅在参考不变时复用 |

CPU / Python 的参数名和金字塔计数需按对应实现核对，不能直接复制旧 README 的 GPU `L2` 标签当 CLI 数值。教学界面的 `pyramid_level=1` 表示一次降采样，保留原层共两层；CPU 桥接按这个实际数值传递。CPU WSVT 使用 `crop=0`、`n_template=0`，避免原 CLI 默认 crop512 将全图悄悄裁小。

## 7. 为什么选这个默认值

下表从固定提交的原始五次 `timing.csv` 独立重算均值 / 样本标准差，六组与发布统计一致。数据是 BB11：2048²×100 uint16 WSVT；2048² float32 WXST。固定协议见第5节；每组预热1次、正式5次、每对重建参考。服务器为单张 RTX5880 Ada 48GB、EPYC9J14；Orin为AGX Orin64GB共享DRAM。两台没有竞争计算任务，时钟 / 热历史未强制标准化。

| 设备 / 方法 | 速度策略 | 求解器均值±SD s | 七项返回均值±SD s | 显式 CUDA 分配 GiB |
|---|---|---:|---:|---:|
| 服务器 WSVT | speed/copy | 0.160533±0.002983 | 0.164836±0.002987 | 6.478 |
| 服务器 WXST | speed/copy | 0.056215±0.001813 | 0.064156±0.001812 | 1.595 |
| Orin WSVT | speed/mapped | 1.190861±0.000737 | 1.194558±0.000764 | 5.696 |
| Orin WXST | speed/copy | 0.595528±0.000923 | 0.610231±0.003863 | 1.595 |

低内存 WSVT：服务器 0.170445s / 4.258GiB，Orin 1.399078s / 3.476GiB（求解器 / 显式CUDA分配）。默认选 speed，内存不足再改低内存。Orin CUDA 分配由共享 DRAM 支撑，与 RSS 有重叠，不能相加。

服务器 WXST：旧 pageable GPU 纯求解器 0.047337s，新 CLI 0.056215s；完整返回从 0.077971s 到 0.064156s。同主机不同缓冲 / 输出所有权策略的对照保留在[原始报告](../native/speckle/benchmarks/RESULTS.md)，不把这些变化全部归因于 C++ 或内核加速。表格不含文件读写、初始化、固定页分配，不能和 Windows 网页墙钟或不同参数的旧 CPU 时间直接作倍数比较。

新版对保留的旧 GPU 六项非相位字段一致，相位最大差≤1.53e-4rad；两台机器全输出与指定 ROI 的门槛通过。这验证迁移保存数值行为；WXST / WSVT 与 CPU 的逐点一致性及独立物理真值需单独检验。原 GPU 对 CPU 的 WXST 全图差异记录仍保留在原工程，不能因本次 GPU 对 GPU 的通过而消除。

证据：[重算验证](../validation/native_package_050.json)、[每次计时与原生报告](../native/speckle/benchmarks/results/)、[推荐表](../native/speckle/benchmarks/recommended.csv)、[源码哈希](../provenance/native_speckle_050.json)、[完整原实验图与记录](https://github.com/haohaoxueyangwen/WSVT_CPP/tree/3f418aa71771e9d209af0702b742ac7e7a69aa9a/speckle_four_editions/benchmarks)。本次资料包更新没有重新运行全尺寸 GPU 实验；Windows 0.6.0 另外实际执行了小图 CPU / GPU 同图、平移、低内存及浮点输入，并检查了独立运行包与真实浏览器；没有补做 Windows 全尺寸性能实验。

## 8. 常见问题与升级

| 现象 | 检查 / 处理 |
|---|---|
| `no kernel image` / `invalid device function` | SM89 / SM87 与本机是否一致；其他架构需另建并验收 |
| cuFFT / cudart 找不到 | `ldd`、驱动与 Toolkit、bin 旁边的 lib 路径 |
| CUDA 内存不足 | 关闭竞争任务、核对真实可用内存、WSVT low-memory；不用删实验数据解决 |
| 100 帧限制报错 | 核对配对、模式与帧数；任意帧数使用 CPU / Python |
| uint16 错误 | 校正后或浮点输入用 float32；不截断或量化 |
| 参数固定报错 | 本 GPU 接口不会忽略参数；恢复固定值或明确切换后端 |
| 输出目录存在 | 换新目录；输入与历史输出不覆盖 |
| 跨主机路径找不到 | 本机程序只能访问本机文件；在计算主机启动入口 |
| 相位方向 / 数值异常 | 核对样品 / 参考顺序、像元 / 距离 / 能量单位、图像坐标、ROI起点、校正与搜索范围 |

升级先在原算法仓库验证新提交，再更新教学仓库固定来源与 SHA256 清单，重算时间统计并核对输出合同。不要把旧编译产物与新源码混用。GitHub Release 0.6.0 提供 Windows 完整运行包（含程序和依赖）与源码包。0.5.0 原生源码和 Linux 原始记录保留；实验数据、运行历史和本机配置不随包发布。
