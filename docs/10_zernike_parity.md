# 完整 Zernike：原界面逐项对照

波前分析默认入口是 **完整 Zernike · 原手动圆瞳分析**，使用原 `perform_advanced_zernike_analysis`，覆盖原高级 GUI 的参数和结果。此前 15 项教学拟合仍作为明确标注的示例保留。

## 手动圆瞳高级界面

对照原 `zernike_analysis_gui.py`，实际科学函数源码逐字节保存在 `vendor/advanced_zernike_original.py`，来源哈希见 [provenance/zernike_full.json](../provenance/zernike_full.json)。旧研究工程与历史输出没有改写。

| 原参数 / 功能 | 当前入口与行为 |
|---|---|
| 加载二维相位 `.npy` | 本机文件浏览，无需上传；预览显示原数组形状、范围、均值、标准差、有限点数 |
| 像元尺寸 0.001–1000 µm，默认 0.65 | 独立数值输入，完整传给原函数 |
| 光子能量 0.1–100 keV，默认 15 | 独立数值输入；派生波长同时显示 nm 和 µm |
| 拟合项数 5–50，默认 15 | 保留完整范围，不限制为 15 项 |
| 最大去除径向阶数 0–10，默认 2 | 去除 `n <= max_order_remove` 的已拟合项；不是去掉前 N 项 |
| 数值圆心 X、Y 和半径 | 分别输入，可保留小数；使用原图坐标 |
| 鼠标圆瞳选择、缩放和平移 | 拖画圆瞳、移动圆瞳、设半径、滚轮 / 按钮缩放、拖动平移、重置视图 |
| 输出目录浏览与文件名前缀 | 本机文件夹选择；每次创建 `前缀_任务ID` 子目录，原文件不覆盖 |
| 工作线程、进度和日志 | 独立计算子进程、阶段进度、日志、停止及历史；重新启动可恢复外部输出目录的记录 |
| 整体 PV / RMS | 保留原圆瞳内计算；RMS 为标准差，即去 piston 后 RMS |
| 去除低阶后的 PV / RMS | 保留原高阶残差定义，同时显示全部拟合后的残差 PV / RMS |
| Rx、Ry、平均 ROC | 保留原 j4 / j6 曲率公式，单位 mm；零曲率显示 ∞，JSON 用字符串表示 |
| 系数查看 | 展示全部拟合项，而非只列前 10 项；显示 Noll j、(n,m)、rad、waves 及该项是否被去除 |
| 查看完整报告及高阶图 | 原完整报告保留：全图、圆瞳、拟合、高阶、残差、系数、3D 原相位及定量报告；可放大、平移、翻页、重置、下载原图 |
| TIFF 导出 | 五种相位图分别导出带色标 TIFF 和原始 float32 TIFF；同时保存无损数值 NPY / NPZ |
| 打开结果目录 | 日志面板中的“打开结果文件夹”；输出位置可复制，数据可直接下载 |

旧 GUI 调用的函数实际只输出报告 PNG 和高阶 PNG；脚本中还有 TIFF 导出函数。本入口把两类导出一并补全。五种相位图是圆瞳内原相位、全部拟合相位、去除的低阶背景、高阶像差、全部拟合残差，圆瞳外保留 NaN。CSV、JSON 和文本报告同时导出。

默认像元与能量是**旧界面默认值**，不是对实际实验标定的推断。处理实验数据前应替换为真实数值。

## 自动 ROI / 高度、曲率与残差 Zernike

另一套原 `zernike_ui/app.py` 及其 `runner.py` 作为独立选项保留，避免和手动圆瞳流程混淆。

| 原参数 / 功能 | 当前入口 |
|---|---|
| 相位文件、输出目录、运行名称 | 保留；输出目录支持浏览与独立任务子目录 |
| 能量 eV、像元 µm、可选材料 δ | 保留；关闭材料转换时 δ 不参与计算 |
| 自动 / 无 / 自定义阈值 | 保留；仅自定义模式启用数值阈值 |
| 保留低于 / 高于阈值 | 保留 |
| 材料转换、表面数 1–10 | 保留 |
| 重新拟合裁剪后的残差 | 保留 |
| 相位转高度 / 波长、分割及内切圆 | 原 runner 执行 |
| 二次曲面、中心与 ROC、0.9 重裁剪 | 原 runner 执行；0.9 是原程序固定值，未伪装为 GUI 参数 |
| 残差对比、15 项 Zernike、最后残差 | 原 runner 执行；该流程原 GUI 固定 15 项，与手动入口的 5–50 项不同 |
| 展示图、进度、日志、图片翻页缩放 | 原 PDF 保留，增加同一图 PNG 预览及浏览器图像查看器；后台显示替代阻塞式弹窗 |

该选项仍需原分析工程：选择包含 `zernike_ui` 的目录，或设置 `WFS_ANALYSIS_SOURCE`；安装 `pip install -e ".[analysis]"`。手动完整 Zernike 已随仓库打包，克隆后无需寻找原工程。

## 两项明确修正

1. **Noll 索引。** 旧手动函数把 j=1 映射为 `(0,2)`，部分项还重复，无法正确表示 piston / tilt / defocus。新入口给原模块替换为标准 Noll 映射，原拟合、阶数去除、ROC 和绘图函数不改写。[AOtools 的标准 Noll 映射](https://aotools.readthedocs.io/en/latest/_modules/aotools/functions/zernike.html#zernIndex)作为核对来源。
2. **波长单位。** 旧 GUI 的 `1.24/E_keV` 是 nm，却传作 µm，造成约 1000 倍的尺度错误。新入口用 `hc/E` 计算并传 µm；15 keV 对应约 `0.082656132 nm = 0.000082656132 µm`。[NIST 的能量与波长关系](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=920358)用于单位核对。

每次 `metadata.json` 记录输入 / 原科学源码哈希、旧索引列表和修正来源。不能将修正后的结果称作旧错误实现的逐值复现；旧源码仍保留以供历史追溯。

Rx / Ry 沿用原程序由 j4 与 j6 计算的固定轴公式，不将其称作包含旋转像散 j5 的主曲率轴。高阶 RMS 与拟合残差 RMS 是两项不同指标。

## 跑通完整例子

```powershell
python -m pip install -e .
python -m wfs_starter run examples/full_zernike/config.json --output full-zernike-results
python launch_frontend.py --app wavefront
```

浏览器里导入 `examples/full_zernike/config.json`，数据目录选择该示例文件夹；或通过本机文件浏览直接选择 `phase_rad.npy`。示例为 64×64 的已知解析波前，圆心 `[31.5,31.5]`、半径 28、50 项、去除径向阶数 0–2。`expected.json` 包含已知系数、预期高阶 RMS 和输入哈希，完全不包含实验数据。

检查原完整报告、全部系数、拟合残差和高阶波前；拟合残差接近零，高阶 RMS 仍非零，证明两个分析量没有混淆。实际验证见 [validation/zernike_full.json](../validation/zernike_full.json)。
