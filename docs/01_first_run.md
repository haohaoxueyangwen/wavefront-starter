# 第一遍：从文件到结果

1. 按 README 创建虚拟环境并运行 `check-env`。所有依赖应能导入，NumPy 为 1.26.4、Numba 为 0.60.0。
2. 执行 `demo --output outputs/first_demo`。它在 CPU 上生成 WXST、WSVT、光栅、Hartmann、Zernike 五组已知答案的数据并自动分析。
3. 打开 `outputs/first_demo/report.json`，每个模块应显示 `passed: true`。
4. 各模块的 `data/` 是输入，`config.json` 是操作参数，`results/results.npz` 是数值结果，`metadata.json` 是参数、单位与处理约定，PNG 是预览。
5. 使用 `run 某模块/config.json --output 新目录` 单独复跑。配置内的数据路径相对配置所在目录解析，整个资料包换盘也能使用。

## 看什么结果

| 案例 | 已知答案 | 验收条件 | 本机结果 |
|---|---|---|---|
| WXST | 散斑向左 2 px、向下 1 px | 中位 EPE <0.15 px，P95 <0.5 px | 0.0732 / 0.1586 px |
| WSVT | 32 对独立纹理，相同已知位移 | 同上 | 0.1192 / 0.2485 px |
| 光栅 | 两方向载频编码解析梯度 | 相位 RMSE <1e-4 rad | 1.37e-13 rad |
| Hartmann | Gaussian 光斑向右 0.35 px、向上 0.2 px | 最大位移误差 <1e-6 px | 2.66e-13 px |
| Zernike | 明确的圆瞳和 15 阶系数 | 最大系数误差 <1e-10 rad | 3.33e-16 rad |

EPE 是估计位移与已知位移的二维欧氏距离。散斑求解器先裁去搜索边缘，评估时再排除 5 px；不要拿这组内部区域误差声称整张实验图像的精度。例子使用无噪声/低难度条件。

刚体位移只检查散斑追踪入口与方向。该参考求解器在积分前去除位移均值，因此散斑例子中的倾斜不会体现在最终相位图里。光栅例子用于检查解调与积分链，不是 Talbot 光学传播仿真。

## 保留的失败记录

最初的 8 帧 WSVT 案例，中位 EPE=0.258 px、P95=0.475 px，中位误差未达到 0.15 px 门槛，记录为失败。后续案例改为 32 帧，并固定每种案例的独立随机种子，使 `--case` 与 `all` 的输入一致；门槛保持不变。两组输入不完全相同，这不是单变量的帧数效果实验。原记录保存在 `validation/initial_8frame_failure.json`。

## 常见失败

| 提示 | 处理 |
|---|---|
| NumPy/Numba 不兼容 | 使用锁定的独立环境；不要升级原研究环境 |
| 文件不存在 | 核对相对配置目录的路径和帧对应关系 |
| Flat minus dark must be positive | 在上游确认背景、平场与坏点；本版不会给坏点自动塞极小分母 |
| WSVT temporal variation | 每个像素需要跨帧纹理变化，重复复制同一张图不能充当有效栈 |
| square ROI | 在上游对参考/样品取完全相同的正方形 ROI |
| DC / Sideband outside | 在 fftshift 频谱中重新确认边带中心与窗口 |
| Choose a new output directory | 使用新的目录名以保留旧结果 |

源代码 API 在 Windows 多进程使用时，应放入 `if __name__ == '__main__':` 中调用。推荐先用命令行入口。
