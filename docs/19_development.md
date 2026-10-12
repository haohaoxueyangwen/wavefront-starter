# 开发、源码运行与发布

[文档目录](README.md) · [维护位置](09_code_maintenance.md) · [贡献说明](../CONTRIBUTING.md)

## 选择环境

初学者使用Windows完整包。源码开发使用Python3.11–3.12，推荐3.12独立环境；当前开发环境3.12.7、Windows便携解释器3.12.10已分别检查。安装固定依赖后用 `--no-deps` 安装本包，避免无意升级科学计算依赖。

Windows命令见 [README 源码安装](../README.md#从源码安装)。没有 `py` 时用已安装Python3.12执行 `python -m venv .venv`。Linux/macOS：

```bash
git clone https://github.com/haohaoxueyangwen/wavefront-starter.git
cd wavefront-starter
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python -m wfs_starter check-env
.venv/bin/python -m wfs_starter ui --app speckle
```

这些是源码安装指令；macOS没有本包原生二进制验收。源码版可用Python参考算法；C++ / GPU需按 [原生构建指南](11_speckle_fast.md)构建并配置，不能把克隆操作当作本地编译成功。

## CLI 和实例

以下命令在Windows源码环境执行；Linux将解释器路径改为 `.venv/bin/python`，便携包改为 `.\runtime\python\python.exe`。

```powershell
.\.venv\Scripts\python.exe -m wfs_starter demo --case wxst --output outputs\crl_first
.\.venv\Scripts\python.exe -m wfs_starter run outputs\crl_first\wxst\config.json --output outputs\wxst_rerun
.\.venv\Scripts\python.exe -m wfs_starter demo --case grating --output outputs\grating_first
.\.venv\Scripts\python.exe -m wfs_starter demo --case hartmann --output outputs\hartmann_first
.\.venv\Scripts\python.exe -m wfs_starter run examples/full_zernike/config.json --output outputs\full_zernike_first
```

每个输出目录必须是新的。散斑demo默认真实CRL，优先可用C++ CPU，否则Python参考；源码首次需联网下载并校验CRL。`--case all`包含WXST、WSVT、光栅、Hartmann、教学Zernike五个案例，完整50项另按上述配置运行。

## 原工程扩展

Hartmann设计 / 旋转需要设置 `WFS_HARTMANN_PROJECT` 为原工程根目录，内部含 `modes/xray/visualization`；按原工程说明安装依赖。曲率 / 残差与焦点需要包含 `zernike_ui` / `focus_analysis` 的工程，并设置 `WFS_ANALYSIS_SOURCE` 或在页面选择路径；本包附加依赖可用 `python -m pip install -e ".[analysis]"`，仍需核对原工程要求。

`.local_runtime.json` 可设本机解释器、工作区和环境变量，Git忽略；不要提交机器绝对路径。移到另一电脑后重新准备工程与环境。各扩展的作用和输出位置见 [界面总览](08_interfaces.md)。

## 修改后检查

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/check_documentation.py
```

文档检查核对相对链接、标题锚点、模板数、必备入口和当前版本一致性，写到标准输出，不修改历史验证记录。数值修改需要对应解析控制 / 真实数据检查，并记录后端、设备、参数和结果范围。文档修改不用把旧GPU测速重跑或改成新版本测速。

## 发布与同步

源码包从已提交标签 `git archive` 生成；Windows包在同一标签源码外加运行库及CRL数据。更新README、Windows说明、`先看这里.txt`、CHANGELOG、包版本、服务版本和启动版本检查，检查后再建立新标签，不覆盖旧发布文件。

纯文档发布可用 [repack-docs 工作流](../.github/workflows/repack-docs.yml)：先为允许的已检查标签建立草稿Release，手动启动工作流。它调用 [重打包脚本](../scripts/repack_windows_docs.py)，只接受已登记的标签，验证固定v0.6.1基线ZIP SHA256、所有算法源码不变、147个冻结源码及200个CRL裁剪哈希，复用原运行库；上传到草稿，不自行发布。

维护者应检查工作流成功、源码标签、`release_receipt.json`、三个ZIP和 `SHA256SUMS.txt`，再发布草稿，并匿名下载核对文件。算法 / 二进制修改不能使用纯文档重打包冒充新构建，需要新的平台构建和执行记录。Windows运行库来源、许可证与构建证据见 [验证说明](13_windows_validation.md)和 [provenance/](../provenance/)。

`MANIFEST.in` 也包含文档、图片、RIS和入口脚本；Python安装包用于源码开发，不含完整便携运行库或CRL帧。需要完整固定原生来源时使用发布的source ZIP，按各原算法构建说明维护。
