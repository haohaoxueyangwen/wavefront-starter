# wavefront-starter：X 射线波前传感学习与代码入口

面向刚入门的同学：先看懂输入输出，再跑通已知答案的合成数据，最后接入标定完整的实验数据。这里整理了已有研究代码的核心函数，提供统一的配置入口、五个小示例及中文操作文档。

所有学习资料以本 GitHub 仓库为主入口：在线阅读文献导读与操作文档，克隆后生成示例数据并运行代码。面向刚开始做 X 射线波前传感的同学，原算法仓库分别维护。

## Windows 直接运行 · 0.6.0

给师妹直接分享本仓库链接即可。**下载 [Windows 完整运行包](https://github.com/haohaoxueyangwen/wavefront-starter/releases/tag/v0.6.0)，全部解压，双击 `start_speckle.cmd`，选择数据、实验标定和 CPU / GPU 后运行。** Python、依赖、C++ CPU 和原生 GPU 程序均已随包提供，无需自己找 EXE、安装 Anaconda 或 CUDA Toolkit。

第一次先点“载入 CPU / GPU 示例” → “运行算法”。没有兼容 NVIDIA 显卡就用 CPU；界面自动检测设备。其他显卡的支持范围、显存、驱动和排错写在 [Windows 入门指南](docs/12_windows_quickstart.md)，实际编译与测试范围见 [Windows 验证记录](docs/13_windows_validation.md)。

四个独立入口：`start_speckle.cmd`（WSVT / WXST）、`start_grating.cmd`、`start_hartmann.cmd`、`start_wavefront.cmd`（完整 Zernike 等）。`check_windows.cmd` 检查本机环境，`stop_frontends.cmd` 在任务结束后关闭后台。

## 原生算法与历史性能 · 0.5.0 来源

WSVT / WXST 的原生 C++ / CUDA / cuFFT 速度配置已随仓库打包：Linux Ada 与 Jetson Orin 各自提供构建 / 启动入口，无需 PyTorch。网页 GPU 入口已接入新版，默认速度优先，保留 WSVT 低内存选项；CPU 和完整 Python 参考参数继续保留。

**先看 [高速散斑完整操作文档](docs/11_speckle_fast.md)**：版本选择、依赖与构建、小数据示例、100 帧配对、参数、结果单位和坐标、性能证据及排错。需要一次下载全部代码，使用 [v0.5.0 发布包](https://github.com/haohaoxueyangwen/wavefront-starter/releases/tag/v0.5.0)。完整版包含本资料包全部源码；native 包只含原生部署源码与配套说明。0.5.0 是源码包；0.6.0 另外提供带 Python、依赖和原生程序的 Windows 完整运行包。实验数据不在任何发布包中。

| 实测设备 | WSVT 速度配置 solver / 七项返回 | WXST solver / 七项返回 |
|---|---:|---:|
| RTX5880 Ada | 0.161 / 0.165 s | 0.056 / 0.064 s |
| AGX Orin64GB | 1.191 / 1.195 s | 0.596 / 0.610 s |

BB11 2048²，WSVT100 uint16 / WXST单对float32，固定 half10 / cut1 / 两层 / I1 / 无暗场；预热1次、正式5次、每对重建参考。以上不含文件IO、初始化和网页图表开销。服务器 WXST 纯求解器并非旧 GPU 对照中最快；推荐配置按完整结果返回和部署选取。均值±SD、完整对照和源码哈希见操作文档。

## 先从这里开始

| 想做什么 | 入口 |
|---|---|
| Windows 下载后直接操作 | [解压、选版本、选数据、运行和排错](docs/12_windows_quickstart.md) |
| 最新 WSVT / WXST 高速版 | [安装、示例、全参数和性能证据](docs/11_speckle_fast.md) |
| 从基础了解方向 | [学习路线](docs/06_learning_path.md) |
| 先读几篇重要综述 | [7 篇核心综述与理论总览](docs/05_key_reviews.md) |
| 找完整文献 | [34 条分类文献与专著](docs/04_reading.md) / [BibTeX、RIS](literature/) |
| 用网页界面操作 | [四个独立前端：启动与界面指南](docs/08_interfaces.md) |
| 找唯一代码入口和清理记录 | [代码维护说明](docs/09_code_maintenance.md) |
| 跑通第一套数据 | [五案例操作指南](docs/01_first_run.md) |
| 换成自己的实验数据 | [数据、单位与标定要求](docs/02_real_data.md) |
| 找公开实验数据和原研究代码 | [软件与数据入口](docs/07_resources.md) |

| 模块 | 输入 | 输出 / 范围 |
|---|---|---|
| WXST | 一对参考/样品散斑图 | 空间模板追踪，位移 px、去均值偏折角 rad、相位 rad |
| WSVT | 逐帧对应的参考/样品栈 | 时间向量追踪；教学示例 32 帧 |
| 光栅 | 一对图像、两个人工确认的频域边带 | 差分条纹相位；有显式标定系数后才能积分波前 |
| Hartmann | 同一固定网格内的参考/样品光斑 | 质心位移；有像元和传播距离后可换算偏折角 |
| Zernike | 波前数组、圆瞳位置、输入单位 | 完整圆瞳分析5–50项、曲率、低阶去除、完整报告；保留15项教学示例 |

## 从源码安装 · 开发者与非 Windows 用户

仓库已公开，直接克隆到自己的电脑，在项目根目录运行。已实际验证 Python 3.12.7；包声明支持 3.11–3.12。使用独立环境，避免旧 Anaconda 中 NumPy/Numba 版本冲突。

```powershell
git clone https://github.com/haohaoxueyangwen/wavefront-starter.git
cd wavefront-starter
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -m wfs_starter check-env
.\.venv\Scripts\python.exe -m wfs_starter demo --output outputs\first_demo
```

如果系统没有 `py`，将创建虚拟环境的 `py -3.12 -m venv .venv` 一行替换为已安装的 Python 3.12 的 `python -m venv .venv`。每次输出目录必须是新目录，程序不会覆盖已有结果。

Linux/macOS 使用 `python3.12 -m venv .venv`，后续将解释器路径换成 `.venv/bin/python`。

## 用网页界面操作

完成上面的安装后运行：

```powershell
.\.venv\Scripts\python.exe -m wfs_starter ui
```

浏览器显示四个独立入口：散斑（WSVT / WXST）、光栅、Hartmann、波前分析。Windows 可直接双击 `start_speckle.cmd`、`start_grating.cmd`、`start_hartmann.cmd`、`start_wavefront.cmd`。每个前端单独保存参数和历史；文件、目录通过浏览按钮选择。散斑参数包含小波、金字塔、迭代、线程和 ROI，可明确选择 Python CPU、C++ CPU 或指定的 GPU 优化版。原 Hartmann 设计 / 仿真和原曲率 / 焦点流程通过原工程桥接，配置方法见界面指南。网页在本机运行；GitHub 页面提供资料和代码。

完整操作见 [界面指南](docs/08_interfaces.md)，已有研究界面的本次增量修复见 [维护记录](maintenance/legacy-gui/README.md)。

## 单独跑一个示例或接入配置

```powershell
.\.venv\Scripts\python.exe -m wfs_starter demo --case grating --output outputs\grating_demo
.\.venv\Scripts\python.exe -m wfs_starter run outputs\first_demo\wxst\config.json --output outputs\wxst_rerun
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`demo` 会生成输入、配置、已知答案和结果，克隆后即可使用。每种案例的种子固定，单独运行与 `all` 产生相同输入；无需寻找另外的资料包。真实实验数据入口见 [软件与数据](docs/07_resources.md)。

## 仓库导航

| 文件 | 用途 |
|---|---|
| [docs/01_first_run.md](docs/01_first_run.md) | 示例步骤、结果检查、失败排查 |
| [docs/02_real_data.md](docs/02_real_data.md) | 数据组织、单位、坐标、几何与标定要求 |
| [docs/03_methods.md](docs/03_methods.md) | 四类方法的物理量与算法边界 |
| [docs/04_reading.md](docs/04_reading.md) | 34 条分类文献、正式出版信息与阅读用途 |
| [docs/05_key_reviews.md](docs/05_key_reviews.md) | 7 篇核心综述与理论总览的中文导读 |
| [docs/06_learning_path.md](docs/06_learning_path.md) | 从基础到接入实验数据 |
| [docs/07_resources.md](docs/07_resources.md) | 配套软件、公开实验数据与原仓库 |
| [docs/10_zernike_parity.md](docs/10_zernike_parity.md) | 原 Zernike 两套界面逐项对照、完整参数与已知波前示例 |
| [native/speckle/](native/speckle/PACKAGE_GUIDE.md) | 固定来源的 C++ CPU / CUDA GPU 部署源码与原始计时 |
| [examples/](examples/) | 实验配置模板，标定项为 null，必须先填写 |
| [src/wfs_starter/core.py](src/wfs_starter/core.py) | 新的教学接口和输入检查 |
| [src/wfs_starter/vendor/](src/wfs_starter/vendor/) | 从已有代码提取的核心实现 |
| [provenance/](provenance/) | 原文件哈希、第三方声明和整理方式 |
| [validation/](validation/) | 通过与失败的合成测试记录、验收门槛 |

## 与原研究仓库的关系

高性能 C++ 算法维护在 [WSVT_CPP](https://github.com/haohaoxueyangwen/WSVT_CPP)，历史完整 Hartmann 仿真与恢复维护在 [hartmann_V2](https://github.com/haohaoxueyangwen/hartmann_V2)。本仓库提供学习示例、四个独立前端及原研究算法桥接；科研参数、冻结性能结果、深度学习训练与动态多脉冲研究仍在原工程中维护。

0.4.1：四个独立前端，波前分析默认提供原完整 Zernike（5–50 项、径向低阶去除、曲率、完整报告与 TIFF），手动算法随仓库打包；[完整示例与功能对照](docs/10_zernike_parity.md)。接口、合成案例和原曲率 / 焦点流程的检查见 [独立前端验证](validation/independent_frontends.json)。C++ / CUDA 的执行需要对应平台构建产物；安装网页界面不会自动生成原生算法库。

散斑参考实现保留 UChicago Argonne 的版权声明。教学整理为本地修改版，来源与变更见 [NOTICE](provenance/NOTICE.md)。其他提取函数来自作者已有代码；本次未另外授予整个仓库新的开源许可证。


文献更新于 2026-10-11：34 条文献与专著，其中 10 条为综述、综述型研究论文或理论总览。DOI 与元数据已核对，完整作者引文可导入 Zotero。仓库已公开，可直接把 GitHub 链接发给师妹。
