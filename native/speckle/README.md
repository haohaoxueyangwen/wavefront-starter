# WSVT / WXST 原生速度版源码包

从[中文操作指南](../../docs/11_speckle_fast.md)开始：构建、示例、实验输入、全部参数、输出和性能范围。

本包含固定提交的 C++ CPU、Ada GPU、Orin GPU 源码，默认 speed；WSVT另保留 low-memory。详见[打包边界](PACKAGE_GUIDE.md)、[原生 API](docs/NATIVE_API.md)。原四版本说明按原字节保存为[UPSTREAM_README](UPSTREAM_README.md)，其中 Python reference 和实验图请访问[原算法固定提交](https://github.com/haohaoxueyangwen/WSVT_CPP/tree/3f418aa71771e9d209af0702b742ac7e7a69aa9a/speckle_four_editions)。

这是源码包，GPU需在实际Linux Ada / Orin主机编译；不附跨平台exe、实验输入或完整重构数组。
