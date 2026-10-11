# 软件、示例数据与原研究仓库

| 入口 | 用途 |
|---|---|
| [本仓库在线操作指南](01_first_run.md) | 五种已知答案的 CPU 合成案例 |
| [本仓库配置模板](../examples/) | 填入实验路径、像元、几何、参考和标定 |
| [本仓库结果与验收摘要](../validation/) | 合成测试门槛、通过报告、最初失败记录 |
| [Spexwavepy 作者仓库](https://github.com/wholingfei/spexwavepy/) | 另一个配套完整的散斑波前工具，结合 L3 阅读 |
| [Spexwavepy 文档](https://spexwavepy.readthedocs.io/) | 数据结构、方法和公开示例操作 |
| [Spexwavepy 示例数据](https://zenodo.org/records/10892838) | 作者论文中的公开实验数据；以记录内的许可和数据说明为准 |
| [WSVT_CPP 更新 PR](https://github.com/haohaoxueyangwen/WSVT_CPP/pull/1) | 已提交原生 C++ 源码快照与构建说明，当前为草稿 |
| [hartmann_V2](https://github.com/haohaoxueyangwen/hartmann_V2) / [文档更新 PR](https://github.com/haohaoxueyangwen/hartmann_V2/pull/1) | 历史完整 Hartmann 仿真/恢复工程与环境说明 |

Spexwavepy 仓库与论文均指向上述 Zenodo 数据记录。它有自己的输入布局、采集几何和方法约定；先按作者文档运行对应示例，再判断能否转换到本仓库接口。数据不会因为同属“散斑”而自动满足 WSVT 的逐帧配对要求。

本仓库的 `demo` 命令负责生成轻量合成数据与配置，生成后可反复用 `run config.json --output 新目录` 复跑；共享仓库链接即可取得完整的生成和操作流程。

仓库当前保持私有。师妹需要获得 GitHub 访问权限，之后从主页面在线读文档，并通过 `git clone` 获取代码。资料阅读和运行步骤都在仓库维护。
