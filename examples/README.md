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

复制对应模板到自己的数据目录，填写所有 `null` 标定项并核对路径。光栅与 Hartmann 默认输出直接观测量；换算波前或偏折角的标定说明见 [实验数据说明](../docs/02_real_data.md)。运行 `demo`会为散斑生成 CRL 实测配置，为光栅 / Hartmann / 教学 Zernike 生成解析控制配置。完整 Zernike 的已知波前另见 [full_zernike/](full_zernike/README.md)。曲率 / 焦点扩展需要原研究工程，不属于独立运行包的即用功能。
