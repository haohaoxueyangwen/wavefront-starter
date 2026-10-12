# wavefront-starter：X 射线波前传感入门与工具

给刚开始做 X 射线波前传感的同学：从基础概念、重要综述，到用真实 CRL 数据跑通 WSVT / WXST，再做完整 Zernike 分析。散斑、光栅、Hartmann、波前分析各有独立界面；原算法仓库分别维护。

## Windows 第一次使用

1. 打开 **[v0.6.2 发布页](https://github.com/haohaoxueyangwen/wavefront-starter/releases/tag/v0.6.2)**，下载 **`wavefront-starter-0.6.2-windows-x64.zip`**，右键“全部解压”。GitHub 自动生成的 `Source code (zip)` 不是完整运行包。
2. 进入解压目录，双击 **`start_speckle.cmd`**。Python、依赖、CPU / GPU 程序与示例数据均已随包提供，无需安装 Anaconda 或 CUDA Toolkit。
3. 先选择 **WXST、C++ CPU**，点击 **“载入 CRL 实测示例”**，再点击 **“运行算法”**。
4. 查看位移 px、偏折角 rad、相位 rad。换成 WSVT 后重新载入示例；WXST 用第001对图，WSVT 用全部100对扫描帧。
5. 点击 **“Zernike 分解 →”**，将新页面的能量改为 **12.4 keV**、像元改为 **1.625 µm**，预览并拖画圆瞳后运行。相位和来源会带入，能量 / 像元当前需手动填写。

默认数据来自 **BB11 金刚石 CRL 真实实验**，仅裁取512×512中央区域，保留原始像素值和100对配对；完整包内含数据，可离线载入。数据身份、全景、裁剪、历史标定与结果示意见 **[CRL 实测案例](docs/14_crl_example.md)**。更换自己的实验数据时，也要更换对应的标定参数。

不知道电脑配置也可以先用CPU。兼容的NVIDIA显卡与驱动由程序检测；GPU不可用就用CPU。支持范围、驱动、内存和排错见 **[Windows 操作指南](docs/12_windows_quickstart.md)**。不要把某一台设备的测速当作所有电脑的性能。

## 四个操作入口

| 功能 | 双击入口 | 随包可直接使用 |
|---|---|---|
| 散斑 | `start_speckle.cmd` | WSVT / WXST，C++ CPU、原生 GPU、Python参考 |
| 光栅 | `start_grating.cmd` | 频域边带选择、差分条纹相位；有显式标定后积分波前 |
| Hartmann | `start_hartmann.cmd` | 固定网格光斑质心、位移及标定后的偏折角 |
| 波前分析 | `start_wavefront.cmd` | 完整手动圆瞳 Zernike，5–50项、低阶去除、曲率、报告与数值导出 |

文件与文件夹通过“浏览…”选择。每次运行创建新的结果目录，默认在解压目录的 `local-runs/`；不覆盖输入实验数据。任务结束后双击 `stop_frontends.cmd`关闭后台。启动异常时双击 `check_windows.cmd`生成诊断记录。

Hartmann设计 / 旋转仿真、自动ROI曲率 / 残差、焦点扫描是原研究工程扩展，需要另外准备对应工程与依赖。完整手动Zernike已经随包提供。详见 [界面指南](docs/08_interfaces.md)与 [Zernike完整功能对照](docs/10_zernike_parity.md)。

## 学习资料与操作文档

| 要做什么 | 先看 |
|---|---|
| 第一次下载和运行 | [Windows 指南](docs/12_windows_quickstart.md) → [CRL 实测案例](docs/14_crl_example.md) |
| 从物理概念开始 | [方法与物理量](docs/03_methods.md)、[学习路线](docs/06_learning_path.md) |
| 先读重要综述 | [7篇核心综述与理论总览](docs/05_key_reviews.md) |
| 查完整文献或导入Zotero | [34条分类文献与专著](docs/04_reading.md)、[BibTeX / RIS](literature/README.md) |
| 换成自己的实验数据 | [数据、坐标、单位和标定](docs/02_real_data.md)、[配置模板](examples/README.md) |
| 查看全参数或部署Linux原生算法 | [高速散斑指南](docs/11_speckle_fast.md) |
| 分析真实相位或跑已知Zernike控制 | [完整 Zernike](docs/10_zernike_parity.md) |
| 找软件和公开实验数据 | [资源导航](docs/07_resources.md) |
| 查代码维护及来源 | [维护说明](docs/09_code_maintenance.md)、[来源声明](provenance/NOTICE.md) |
| 查已测试的设备与数值范围 | [Windows 验证记录](docs/13_windows_validation.md) |

文献元数据于2026-10-12复查，共34条，含10条综述、综述型研究论文或理论总览。导读说明每篇适合解决的问题；论文全文通过出版社、作者机构库或预印本入口取得。

## 从源码安装

这一节供开发者使用。Windows初学者按前面的完整包路线即可。源码环境使用Python3.11–3.12，建议独立环境；已分别验证开发环境3.12.7与完整包3.12.10。Windows PowerShell在项目根目录执行：

```powershell
git clone https://github.com/haohaoxueyangwen/wavefront-starter.git
cd wavefront-starter
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -m wfs_starter check-env
.\.venv\Scripts\python.exe -m wfs_starter ui --app speckle
```

没有 `py`时，用已安装的Python3.12执行 `python -m venv .venv`。Linux/macOS用 `python3.12 -m venv .venv`，后续解释器路径改为 `.venv/bin/python`。

**克隆源码不会附带Windows运行库或自动编译原生程序。**源码环境可用Python参考算法；C++ / GPU开发部署按 [原生指南](docs/11_speckle_fast.md)构建。macOS、Windows ARM没有本包原生二进制验收。源码版首次载入CRL需联网下载约79 MiB数据，程序校验后缓存；也可按CRL指南预先放入数据ZIP。

命令行示例：

```powershell
.\.venv\Scripts\python.exe -m wfs_starter demo --case wxst --output outputs\crl_first
.\.venv\Scripts\python.exe -m wfs_starter run outputs\crl_first\wxst\config.json --output outputs\wxst_rerun
.\.venv\Scripts\python.exe -m wfs_starter demo --case grating --output outputs\grating_first
```

每次输出使用新目录。散斑demo使用真实CRL数据，优先选可用C++ CPU，否则用Python参考；光栅、Hartmann、教学Zernike是各自有明确解析答案的控制。结果结构见 [第一遍操作](docs/01_first_run.md)。需要源码回归检查时，设置UTF-8后执行：

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 与原研究仓库的关系

高性能算法维护在 [WSVT_CPP](https://github.com/haohaoxueyangwen/WSVT_CPP)，完整Hartmann研究工程维护在 [hartmann_V2](https://github.com/haohaoxueyangwen/hartmann_V2)。这里提供入门资料、独立界面、可追溯的固定算法来源与桥接；历史Linux Ada / Orin性能证据和固定源码哈希见高速散斑指南。

Windows CPU / GPU已在P5000运行CRL数据；这是该设备上的执行与跨后端对照，不给实测透镜编造精度真值。其他NVIDIA显卡应先跑随包例子。0.6.2更新说明与版本标识，算法、Windows二进制和CRL数据沿用0.6.1。

散斑参考实现保留UChicago Argonne版权声明，第三方组件保留各自许可证；来源见 [NOTICE](provenance/NOTICE.md)。本仓库没有另授予统一覆盖全部组件的新开源许可证。完整包仅含明确选取的CRL裁剪示例，不分发其他实验数据、实验本、运行历史或本机配置。
