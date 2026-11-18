---
experiment_date: "2026-11-18"
summary: 七项历史 NPU 实验保留；第 02 篇按三个场景精选 A1/A2/M0/M1，其余结果供第 04、09、11 篇复用。
---

# 硬件数据流与性能模型实验

[实验设计与判据](experiment-plan.md) · [Ascend C 内核](src/kernels.cpp) · [分组测量与数值检查](scripts/run.py)

本版已在 Ascend910_9362 上构建并运行，七项实验的原始样本与限制见[真机报告](reports/npu-report.md)。以下命令用于复现。需要支持 dav-2201 的 CANN／ASC 编译环境、与其匹配的 PyTorch 和 torch-npu，以及 NumPy。实验由 Python 分配 ND 连续张量，Ascend C 内核与框架使用同一设备和 Stream。

## 文章证据入口

第 02 篇阅读[精选报告](reports/article-02.md)：场景 1 为 Add 数据流，场景 2 为 Matmul 数据流，场景 3 综合比较 Vector／Cube，不新增 Kernel。数据直接来自既有归档，无需为本轮文档重构运行以下命令。

| 历史编号 | 第 02 篇采用范围 | 后续主要归属 |
| --- | --- | --- |
| A1 | 长度 2048／65536／4194304，40 个任务 | 完整记录保留 |
| A2 | 长度 4194304，1／40 个任务 | 第 04 篇：完整任务数扫描 |
| A3 | 不采用 | 第 11 篇：缓存与物理流量 |
| M0 | 输出块 64、64／128 阶的零／单位阵／随机基础检查 | 第 09 篇：扩展正确性及累计精度 |
| M1 | 64／512 阶，20 个任务、输出块 64 | 第 09 篇：完整规模扫描 |
| M2 | 不采用 | 第 09 篇：Matmul 分块对照 |
| M3 | 不采用 | 第 11 篇：库函数对照与性能分析 |

编号仍为 Lab02-A1 等原编号。历史报告的全部结果分析状态与第 02 篇精选证据状态分开维护，详见[当前实验设计](experiment-plan.md)。

## 全部历史实验的复现入口

下面保留完整命令与参数说明，不能将它们当作第 02 篇必须全部运行的清单。

从仓库根目录构建，然后先单独运行 M0。每次提供新的输出文件名，保留失败或中断前写出的记录。

```sh
cmake -S lab/hardware-dataflow/src -B .local/build-lab02
cmake --build .local/build-lab02
LIB=.local/build-lab02/liblab02.so
python lab/hardware-dataflow/scripts/run.py M0 --library "$LIB" --output .local/lab02/M0.jsonl
```

| 入口 | 固定什么，改变什么 | 要看什么 |
| --- | --- | --- |
| Lab02-A1 | 每块 2048 个 FP32，固定任务数，改变向量长度 | 有效任务数、耗时、逻辑带宽 |
| Lab02-A2 | 长度固定为 4194304，改变任务数 | 并行度提高后耗时是否继续下降 |
| Lab02-A3 | 同一长度、任务数和数据类型，重复使用一组地址或轮换多组地址 | 用匹配两读一写的框架 maximum 作独立流式参照，同时记录地址覆盖量 |
| Lab02-M0 | 对 64、128 阶方阵分别请求 32、64 两种输出块，请求 K 基础块 32，记录接口实际值 | 实际基础块、零与单位阵、2049 精度探针、消去与随机数误差；本次 M0 未覆盖多 K 段累计 |
| Lab02-M1 | 优先固定 64 输出块，若仅 32 通过则采用 32；按上限扫描边长 | 规模与吞吐 |
| Lab02-M2 | 固定 512 阶、核配置、输入输出地址 | 两种 Tile 的时间和请求字节模型 |
| Lab02-M3 | 相同输入、输出精度和设备；自定义实现与 ACLNN 矩阵乘分别测量 | 核对 FP32 输出与误差，再比较时间 |

Add 和 Matmul 可分别用 `--workers` 限制任务数。每个 Matmul 入口都先在当前设备重做 M0。两种 Tile 都失败时停止；只有一种通过时，M2 无法做成对比较。首次 M0 结束后根据实际接口、容量和误差确定后续规模。M1／M3 的 `--max-n` 支持 64 至 1024 的五个离散边长，默认到 512。M0 的探针可以发现精度损失，最终仍需结合设备与工具链文档确认累加模式。

```sh
python lab/hardware-dataflow/scripts/run.py A1 --library "$LIB" --output .local/lab02/A1.jsonl
python lab/hardware-dataflow/scripts/run.py A2 --library "$LIB" --output .local/lab02/A2.jsonl
# L2_BYTES 填目标设备资料中核实的字节数
python lab/hardware-dataflow/scripts/run.py A3 --l2-bytes "$L2_BYTES" --library "$LIB" --output .local/lab02/A3.jsonl
python lab/hardware-dataflow/scripts/run.py M1 --max-n 128 --library "$LIB" --output .local/lab02/M1.jsonl
python lab/hardware-dataflow/scripts/run.py M2 --library "$LIB" --output .local/lab02/M2.jsonl
python lab/hardware-dataflow/scripts/run.py M3 --max-n 128 --library "$LIB" --output .local/lab02/M3.jsonl
```

A3 在设备上每组数组占 48 MiB，轮换组数至少为 2，并按 L2 容量增加。执行前核对可用显存；NumPy 参考值与回传也需要主机内存。框架 maximum 采用自己的调度，作为相同访问比例的参照。M3 使用 [ACLNN 适配入口](scripts/library_matmul.py)，调用 `aclnnMm` 并设置 `cubeMathType=-1`。每次调用重新取得 executor，事件区间可能包含准备造成的空隙，已用 profiler 的单内核时间复核。

纯 Cube 高阶 Matmul 在包含头文件前定义 `ASCENDC_CUBE_ONLY`。输入准备完成后同步设备，运行入口在导入框架前设置 `TASK_QUEUE_ENABLE=0`，保证框架事件与直接 ACL 调用的提交顺序。实际 K 基础块会由接口调整，相关数值已写入结果；比较时需连同输出块一起解释。

每组样本是同一 Stream 上两次设备事件之间的耗时，包含整组提交形成的空隙。预热至少 20 次，测量 5 组，每组至少 50 次，`--reps` 可增加组内次数。JSONL 中 `mean_us` 是每组折算的一次耗时，`q1_us` 至 `q3_us` 描述五组的波动。吞吐 TFLOP/s 用 FLOP 数除以微秒数再除以一百万，逻辑带宽 GB/s 用逻辑字节数除以微秒数再除以一千。

后续第 11 篇若要建立 HBM Roofline，需用目标机支持的 profiler 核实同一内核、同一配置的读写计数和调用次数，再按次折算。现有整段 HBM 系统采样不能直接当成单次内核字节量。JSONL 的 `logical_bytes` 是按显式分块推算的请求量，`hbm_bytes` 留待硬件计数。归档同时记录 SoC、驱动／固件、CANN、编译器、源码版本、实际可用资源及设备占用情况。
