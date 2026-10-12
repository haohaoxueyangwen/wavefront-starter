# 完整 Zernike 的已知波前示例

`phase_rad.npy` 是解析构造的合成相位；圆瞳外为 NaN。图像 64×64，圆心 `[31.5,31.5]`，半径 28。非零 Noll 系数为：j1=2、j2=0.12、j3=0.08、j4=0.3、j6=0.04、j7=0.07、j11=0.05，单位 rad。

Windows 完整包可双击 `start_wavefront.cmd`，导入本目录的 `config.json`，将数据目录选为本目录，预览并运行，无需安装环境。也可从解压目录运行：

```powershell
.\runtime\python\python.exe -B -m wfs_starter run examples/full_zernike/config.json --output full-zernike-results
```

源码用户使用安装本项目的解释器（例如 `.\.venv\Scripts\python.exe`）代替随包路径。每次输出须为新目录。

`config.json` 为完整入口的 50 项配置，去除径向阶数 0–2。`expected.json` 提供已知系数、预期高阶 RMS、输入 SHA256。15 keV 和 0.65 µm 是这个合成控制的参数，与真实实验无关。

网页导入配置后，将数据目录选为本文件夹；输出目录可另选，每次运行创建新子目录。原始数据没有改写。
