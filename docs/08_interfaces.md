# 四个独立前端

完成 [安装步骤](../README.md) 后，Windows 双击以下入口，或运行相应命令：

| 前端 | Windows 入口 | 命令 | 页面 |
|---|---|---|---|
| WSVT / WXST | `start_speckle.cmd` | `python -m wfs_starter ui --app speckle` | `/speckle` |
| 光栅 | `start_grating.cmd` | `python -m wfs_starter ui --app grating` | `/grating` |
| Hartmann | `start_hartmann.cmd` | `python -m wfs_starter ui --app hartmann` | `/hartmann` |
| 波前分析 | `start_wavefront.cmd` | `python -m wfs_starter ui --app wavefront` | `/wavefront` |

命令中的 `python` 应为安装本包的虚拟环境解释器。四个页面各自保存表单与任务历史；共享的本机服务一次只运行一个任务。根页面只保留入口卡片，旧统一工作台已替换。服务仅监听 `127.0.0.1`，数据读取在本机进行。

## 文件和目录选择

点击路径旁的“浏览…”查看本机磁盘、进入目录、选择文件或选择当前目录。无需手写文件夹名称。相对路径仍可用于导入配置，以数据基准目录为起点。

WSVT 可分别选择参考 / 样品文件夹，按自然文件名顺序生成配对表；必须检查每行是否是同一实验位置，程序不推断物理对应关系。也可以逐行选取文件。

## 散斑

WXST 与 WSVT 在同一散斑前端中切换。完整设置包含搜索半窗、WXST 模板半窗、精搜索半窗、小波开关与裁剪、金字塔层数、迭代次数、线程 / 进程、内存分组、能量、像元、传播距离、ROI 边长和中心。输入预览可点击 ROI 中心；0 表示全图。

计算版本明确区分：

- **Python CPU**：随本仓库安装，完整设置传入参考求解器。
- **C++ CPU**：选择原 `WSVT_CPP` 构建的可执行文件，或设置 `WFS_CPP_EXE`。通过原 CLI 执行，固定 `use_gpu=false`。
- **GPU 优化版**：设置 `WFS_GPU_SOURCE` 为包含 `edge_runtime.py` 与平台原生库的目录；运行环境还需 PyTorch / CUDA。当前接入已验证的固定协议：搜索半窗10、WXST模板7×7、金字塔1、裁剪1、迭代1；WSVT必须100帧原生uint16。WXST融合 / 物化路径和CPU / GPU样条可选择。WSVT采用原运算顺序，未通过门槛的重排版本不提供。

后端不可用时明确报错，不自动转用其他算法。界面找到源码不等于本机已有可执行的 CUDA 库。配置文件保存实际后端与参数，结果元数据保存来源。

## 光栅

选择参考 / 样品图，点击输入预览查看 FFT 频谱。选择 X / Y，再点击对应边带中心；窗口尺寸、相位展开均可修改。默认输出差分条纹相位。开启梯度积分后必须填写有来源的有符号梯度系数、X / Y像元尺寸和标定来源。

## Hartmann

主页面提供固定网格质心分析，可修改行 / 列数并预览网格。开启角度转换后填写像元和传播距离。

“设计 / 仿真与恢复”和“旋转参数”进入独立子页面，保留原完整前端参数和原计算服务。启动时设置 `WFS_HARTMANN_PROJECT` 指向包含 `modes/xray/visualization` 的原研究工程，安装其依赖。子页面中的运行操作调用原工程，记录和结果保存在原工程规定的位置。

## 波前分析

- **Zernike**：选择相位 / OPD文件及单位，在预览上点圆心与瞳孔边缘，修改项数。散斑或有标定的光栅恢复相位可通过结果按钮送到此独立页面，保留来源和rad单位。
- **高度 / 曲率与残差**：调用原 `zernike_ui.runner`，保留能量、像元µm、材料δ / 表面数、阈值方式与方向、残差重新裁剪拟合。原PDF输出保留，增加同一图的PNG预览。
- **焦点扫描**：调用原 `focus_analysis.run_analysis`，提供图像分组数、扫描起点 / 步长、参考坐标 / 距离、暗 / 平场目录与开关、阈值、质心、ROI、形态学ROI及工作进程数。

后两项选择包含 `zernike_ui` / `focus_analysis` 的原工程目录，或设置 `WFS_ANALYSIS_SOURCE`。安装附加依赖：`python -m pip install -e ".[analysis]"`。原程序的结果写入新的任务目录，输入目录保持原样。

## 本机启动配置

入口脚本读取项目根目录可选的 `.local_runtime.json`（Git忽略）。可设置 `python`、`workspace` 和 `environment`，后者填写上面列出的环境变量。四个入口复用已启动的同版本服务。端口被另一服务占用时，使用 `python launch_frontend.py --app speckle --port 8791`。

## 结果与停止

每次任务创建新目录。结果图、JSON / NPZ / NPY / CSV / PDF / XLSX、日志可查看或下载；失败和取消记录保留。停止按钮终止该任务进程树。原Hartmann旋转试验的控制使用原服务页面。

先用合成示例检查坐标、单位与参数，再处理实际数据；所需标定见 [数据指南](02_real_data.md)。
