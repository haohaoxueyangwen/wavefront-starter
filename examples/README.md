# 实验配置入口

配置只在下面的五个文件中维护；网页表单读取同一份配置。

| 方法 | 配置模板 |
|---|---|
| WXST | [wxst.json](../src/wfs_starter/configs/wxst.json) |
| WSVT | [wsvt.json](../src/wfs_starter/configs/wsvt.json) |
| 光栅 | [grating.json](../src/wfs_starter/configs/grating.json) |
| Hartmann | [hartmann.json](../src/wfs_starter/configs/hartmann.json) |
| Zernike | [zernike.json](../src/wfs_starter/configs/zernike.json) |

复制对应模板到自己的数据目录，填写所有 `null` 标定项并核对路径。光栅与 Hartmann 默认输出直接观测量；换算波前或偏折角的标定说明见 [实验数据说明](../docs/02_real_data.md)。可运行的合成配置由 `demo` 生成。
