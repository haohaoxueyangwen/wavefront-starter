# 软件、示例数据与原研究仓库

| 入口 | 用途 |
|---|---|
| [本仓库在线操作指南](01_first_run.md) | CRL 实测散斑与光栅 / Hartmann / Zernike 解析控制 |
| [Windows 完整包](https://github.com/haohaoxueyangwen/wavefront-starter/releases/latest) | 随包 Python、CPU / GPU 程序和 CRL 数据，解压启动 |
| [BB11 CRL 实测案例](14_crl_example.md) | 100 对扫描帧、裁剪、历史标定与 Zernike 接续 |
| [本仓库配置模板](../examples/) | 填入实验路径、像元、几何、参考和标定 |
| [本仓库结果与验收摘要](../validation/) | Windows CRL 执行对照及历史解析 / 工程检查 |
| [Spexwavepy 作者仓库](https://github.com/wholingfei/spexwavepy/) | 另一个配套完整的散斑波前工具，结合 L3 阅读 |
| [Spexwavepy 文档](https://spexwavepy.readthedocs.io/) | 数据结构、方法和公开示例操作 |
| [Spexwavepy 示例数据](https://zenodo.org/records/10892838) | 作者论文中的公开实验数据；以记录内的许可和数据说明为准 |
| [WSVT_CPP](https://github.com/haohaoxueyangwen/WSVT_CPP) | 原算法仓库；教学包冻结的源码提交与哈希见 [原生指南](11_speckle_fast.md) |
| [hartmann_V2](https://github.com/haohaoxueyangwen/hartmann_V2) | 完整 Hartmann 仿真 / 恢复研究工程与环境说明；高级桥接需单独准备该工程 |

Spexwavepy 仓库与论文均指向上述 Zenodo 数据记录。它有自己的输入布局、采集几何和方法约定；先按作者文档运行对应示例，再判断能否转换到本仓库接口。数据不会因为同属“散斑”而自动满足 WSVT 的逐帧配对要求。

本仓库的 `demo` 命令为散斑载入真实 CRL 数据，为其他三种方法生成解析控制，并保存可复跑配置。用 `run config.json --output 新目录`复跑；配置内的 CRL 绝对路径属于当前电脑，换电脑后应重新载入示例。

仓库已公开。师妹可直接从主页面在线读文档，通过 Windows 完整包运行；开发者通过 `git clone` 获取代码；资料阅读、网页界面和运行步骤都在仓库维护。
