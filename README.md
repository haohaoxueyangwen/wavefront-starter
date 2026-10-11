# wavefront-starter：X 射线波前传感教学工具

面向刚入门的同学：先看懂输入输出，再跑通已知答案的合成数据，最后接入标定完整的实验数据。这里整理了已有研究代码的核心函数，提供统一的配置入口、五个小示例及中文操作文档。

| 模块 | 输入 | 输出 / 范围 |
|---|---|---|
| WXST | 一对参考/样品散斑图 | 空间模板追踪，位移 px、去均值偏折角 rad、相位 rad |
| WSVT | 逐帧对应的参考/样品栈 | 时间向量追踪；教学示例 32 帧 |
| 光栅 | 一对图像、两个人工确认的频域边带 | 差分条纹相位；有显式标定系数后才能积分波前 |
| Hartmann | 同一固定网格内的参考/样品光斑 | 质心位移；有像元和传播距离后可换算偏折角 |
| Zernike | 波前数组、圆瞳位置、输入单位 | 15 个明确阶次的拟合、RMS、PV、残差 |

## Windows 安装与第一遍运行

在解压或克隆后的项目根目录运行。已实际验证 Python 3.12.7；包声明支持 3.11–3.12。使用独立环境，避免旧 Anaconda 中 NumPy/Numba 版本冲突。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -m wfs_starter check-env
.\.venv\Scripts\python.exe -m wfs_starter demo --output outputs\first_demo
```

如果系统没有 `py`，将第一行替换为已安装的 Python 3.12 的 `python -m venv .venv`。每次输出目录必须是新目录，程序不会覆盖已有结果。

Linux/macOS 使用 `python3.12 -m venv .venv`，后续将解释器路径换成 `.venv/bin/python`。

## 单独跑一个示例或接入配置

```powershell
.\.venv\Scripts\python.exe -m wfs_starter demo --case grating --output outputs\grating_demo
.\.venv\Scripts\python.exe -m wfs_starter run outputs\first_demo\wxst\config.json --output outputs\wxst_rerun
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

ZIP 交付版额外附带 `example_data/`，其中包含生成好的合成输入、配置、已知答案和预期输出。GitHub 只保存生成器与小型验证摘要；克隆后运行 `demo` 即可生成相同输入。

离线 ZIP 解压后可以直接执行：

```powershell
.\.venv\Scripts\python.exe -m wfs_starter run example_data\grating\config.json --output outputs\grating_rerun
```

安装仍需要联网获取 Python 依赖；ZIP 不捆绑虚拟环境或解释器。

## 文件导航

| 文件 | 用途 |
|---|---|
| [docs/01_first_run.md](docs/01_first_run.md) | 示例步骤、结果检查、失败排查 |
| [docs/02_real_data.md](docs/02_real_data.md) | 数据组织、单位、坐标、几何与标定要求 |
| [docs/03_methods.md](docs/03_methods.md) | 四类方法的物理量与算法边界 |
| [docs/04_reading.md](docs/04_reading.md) | 9 篇文献与建议阅读顺序 |
| [examples/](examples/) | 实验配置模板，标定项为 null，必须先填写 |
| [src/wfs_starter/core.py](src/wfs_starter/core.py) | 新的教学接口和输入检查 |
| [src/wfs_starter/vendor/](src/wfs_starter/vendor/) | 从已有代码提取的核心实现 |
| [provenance/](provenance/) | 原文件哈希、第三方声明和整理方式 |
| [validation/](validation/) | 通过与失败的合成测试记录、验收门槛 |

## 与原研究仓库的关系

高性能 C++ 算法维护在 [WSVT_CPP](https://github.com/haohaoxueyangwen/WSVT_CPP)，历史完整 Hartmann 仿真与恢复维护在 [hartmann_V2](https://github.com/haohaoxueyangwen/hartmann_V2)。本仓库用于基础学习和轻量 CPU 示例；科研参数、冻结性能结果、深度学习训练与动态多脉冲研究仍在原工程中维护。

2026-10-11：五个 CPU 合成控制通过，13 项接口检查通过。该验证确认代码入口与特定合成案例的数值行为，真实实验精度需要独立标定和验收。当前数据全部为合成数据。

散斑参考实现保留 UChicago Argonne 的版权声明。教学整理为本地修改版，来源与变更见 [NOTICE](provenance/NOTICE.md)。其他提取函数来自作者已有代码；本次未另外授予整个仓库新的开源许可证。
