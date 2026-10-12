# 贡献与维护

先查 [文档目录](docs/README.md)、[开发指南](docs/19_development.md)与 [唯一维护位置](docs/09_code_maintenance.md)。

## 提交问题

用 [问题模板](https://github.com/haohaoxueyangwen/wavefront-starter/issues/new/choose)填写包版本、算法 / 后端、系统 / 设备、操作步骤、报错及期望。配置文件比截图更有助于复现；上传前检查其中的本机路径与未公开实验信息。实验文件可用最小可分享样例替代，不需要上传整个数据集。

## 修改代码或文档

在分支中做范围明确的修改；参数模板只维护 `src/wfs_starter/configs/` 一份，网页共用。新文献补齐标题、年份、DOI与分类，同步JSON、BibTeX、RIS和导读，核对原始出版来源。

数值改动应说明触发条件、参数和单位，使用有意义的解析控制或固定真实数据验证。分清执行、跨后端一致性和有真值的误差；记录实际设备，保留失败信息。运行检查命令见开发指南。

`native/speckle/` 固定原生来源和 `vendor/advanced_zernike_original.py` 供追溯，不能直接改写后继续沿用旧哈希。算法升级先在原算法工程维护，再明确引入提交和新验证；本机原始实验数据、记录与历史输出不属于代码清理对象。

提交前检查相对链接、入口文档与包版本，运行相应测试。不要提交 `.local_runtime.json`、运行目录、生成缓存、自己的实验输入或凭据。保留各来源版权与许可证；本项目没有新授予覆盖所有组件的统一许可证，见 [NOTICE](provenance/NOTICE.md)。
