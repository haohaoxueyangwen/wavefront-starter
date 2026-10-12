# 文档导航

[项目主页](../README.md) · [下载完整运行包](https://github.com/haohaoxueyangwen/wavefront-starter/releases/latest)

第一次使用： **Windows 指南 → CRL 案例 → 对应算法操作 → 保存结果**。文献学习可以与操作并行；源码安装和原工程扩展放在开发路径。

## 操作与数据

| 文档 | 解决的问题 |
|---|---|
| [12 Windows 直接运行](12_windows_quickstart.md) | 下载、CPU / GPU、未知电脑、完整包启动、标定与排错 |
| [01 第一遍操作](01_first_run.md) | 从实测输入到结果；命令行与网页目录的区别 |
| [14 CRL 实测案例](14_crl_example.md) | 金刚石透镜数据身份、原始全景、裁剪、历史标定与接续 |
| [08 四个界面总览](08_interfaces.md) | 启动入口、本机浏览、独立页面与原工程扩展 |
| [11 散斑完整参数与原生部署](11_speckle_fast.md) | WSVT / WXST、CPU / GPU、固定协议、参数字典与历史性能 |
| [15 光栅逐步操作](15_grating_workflow.md) | 选边带、展开相位、梯度标定与波前积分 |
| [16 Hartmann 逐步操作](16_hartmann_workflow.md) | 网格、质心、位移、偏折角与高级工程入口 |
| [17 波前 / Zernike 逐步操作](17_wavefront_workflow.md) | 输入单位、圆瞳、全部参数、指标与导出 |
| [10 原 Zernike 功能对照](10_zernike_parity.md) | 原功能保留、Noll / 波长修正和两个分析入口的差别 |
| [02 自己的实验数据](02_real_data.md) | 文件格式、坐标、单位、配对、暗 / 平场与标定 |
| [18 结果、复跑与常见问题](18_results_and_faq.md) | 结果文件、迁移、升级、停止与故障定位 |
| [八种配置模板](../examples/README.md) | 一份模板一份来源；哪些字段必须填写 |
| [完整 Zernike 已知答案](../examples/full_zernike/README.md) | 50项解析控制与 expected.json |

## 基础与文献

| 文档 | 内容 |
|---|---|
| [03 方法与物理量](03_methods.md) | 相位、OPD、偏折角、梯度与不同测量模型 |
| [06 学习路线](06_learning_path.md) | 按学习成果从概念走到第一组实验数据 |
| [05 核心综述](05_key_reviews.md) | 优先读的7条综述与理论总览及阅读问题 |
| [04 分类文献](04_reading.md) | 34条论文、专著和章节，按方法组织 |
| [07 软件与数据资源](07_resources.md) | 官方项目、公开数据与进阶路线 |
| [文献文件](../literature/README.md) | BibTeX / RIS / JSON、编号与元数据核验 |

## 维护与证据

| 文档 / 目录 | 用途 |
|---|---|
| [19 开发、构建与发布](19_development.md) | 源码环境、CLI、回归、文档检查与发布同步 |
| [09 代码维护](09_code_maintenance.md) | 唯一修改位置、旧代码与重复清理历史 |
| [贡献说明](../CONTRIBUTING.md) | 问题反馈、修改参数、来源保留与提交 |
| [更新记录](../CHANGELOG.md) | 每个版本的实际变化 |
| [13 Windows 验证范围](13_windows_validation.md) | 已测设备、执行和数值对照；历史记录含其原版本号 |
| [来源声明](../provenance/NOTICE.md) | 保留的算法与组件来源、许可证 |
| [provenance/](../provenance/) | 固定源码、二进制、数据裁剪及哈希来源 |
| [validation/](../validation/) | 已完成检查的原始记录；不作为新版本的重新测速 |

Windows 包中的本目录与对应发布标签同步。在线 `main` 文档可能先于你的本地包；需要完全对应时，在 GitHub 切换到包的版本标签，或者下载最新完整包到新目录。
