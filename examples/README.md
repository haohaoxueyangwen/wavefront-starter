# 实验配置入口

配置统一维护在 `src/wfs_starter/configs/`，网页表单读取同一来源。共有八种运行模式；完整 Zernike 与15项教学 Zernike分开，原工程扩展也单独列出。

| 方法 | 配置模板 |
|---|---|
| WXST | [wxst.json](../src/wfs_starter/configs/wxst.json) |
| WSVT | [wsvt.json](../src/wfs_starter/configs/wsvt.json) |
| 光栅 | [grating.json](../src/wfs_starter/configs/grating.json) |
| Hartmann | [hartmann.json](../src/wfs_starter/configs/hartmann.json) |
| 教学 Zernike | [zernike.json](../src/wfs_starter/configs/zernike.json) |
| 完整 Zernike（默认） | [zernike_full.json](../src/wfs_starter/configs/zernike_full.json) |
| 原工程曲率 / 残差 | [surface.json](../src/wfs_starter/configs/surface.json) |
| 原工程焦点扫描 | [focus.json](../src/wfs_starter/configs/focus.json) |

复制对应模板到自己的数据目录，填写待填字段并核对路径。CLI会拒绝所有未填写的 `null`；光栅恢复和Hartmann角度转换关闭时，标定的0/空字符串占位项不参与计算，开启后必须改成真实数值与来源。光栅与 Hartmann 默认输出直接观测量；换算波前或偏折角的标定说明见 [实验数据说明](../docs/02_real_data.md)。运行 `demo`会为散斑生成 CRL 实测配置，为光栅 / Hartmann / 教学 Zernike 生成解析控制配置。完整 Zernike 的已知波前另见 [full_zernike/](full_zernike/README.md)。曲率 / 焦点扩展需要原研究工程，不属于独立运行包的即用功能。

## 各模板第一次需要填写什么

| 模板 | 首先填写 | 操作教程 |
|---|---|---|
| WXST | 参考 / 样品、能量eV、像元m、距离m、后端和窗口 | [Windows](../docs/12_windows_quickstart.md) |
| WSVT | 逐帧pairs、几何、后端和窗口；GPU恰好100对 | [全参数](../docs/11_speckle_fast.md) |
| 光栅 | 两个边带中心；开启恢复时填梯度系数和采样间距 | [光栅](../docs/15_grating_workflow.md) |
| Hartmann | 网格行 / 列；开启角度转换时填像元和距离 | [Hartmann](../docs/16_hartmann_workflow.md) |
| 教学Zernike | 相位 / OPD、单位、圆心和半径 | [波前](../docs/17_wavefront_workflow.md) |
| 完整Zernike | 相位rad、能量keV、像元µm、圆心 / 半径、项数 / 去除阶数 | [完整分析](../docs/17_wavefront_workflow.md) |
| surface / focus | 原工程路径及对应真实实验字段 | [原工程扩展](../docs/19_development.md#原工程扩展) |

## 路径怎样组织

例如把自己的 `config.json` 与 `data/reference.npy`、`data/sample.npy` 放在同一项目目录。CLI按配置所在目录解析 `data/...`；网页导入配置后，把“数据目录”浏览选择为这个项目目录。绝对路径可直接浏览填入，移到另一电脑后需重新选择。结果另存新目录，详情见 [保存与复跑](../docs/18_results_and_faq.md)。
