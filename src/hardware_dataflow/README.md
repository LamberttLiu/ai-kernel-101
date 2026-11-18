# 第 02 篇实验代码

[实验设计与判据](../../lab/hardware-dataflow/experiment-plan.md) · [Ascend C 内核](kernels.cpp) · [分组测量与数值检查](run.py)

本版已在 Ascend910_9362 上构建并运行，七项实验的原始样本与限制见[真机报告](../../lab/hardware-dataflow/npu-report.md)。以下命令用于复现。需要支持 dav-2201 的 CANN／ASC 编译环境、与其匹配的 PyTorch 和 torch-npu，以及 NumPy。实验由 Python 分配 ND 连续张量，Ascend C 内核与框架使用同一设备和 Stream。

从仓库根目录构建，然后先单独运行 M0。每次提供新的输出文件名，保留失败或中断前写出的记录。

```sh
cmake -S src/hardware_dataflow -B .local/build-lab02
cmake --build .local/build-lab02
LIB=.local/build-lab02/liblab02.so
python src/hardware_dataflow/run.py M0 --library "$LIB" --output .local/lab02/M0.jsonl
```

| 入口 | 固定什么，改变什么 | 要看什么 |
| --- | --- | --- |
| A1 | 每块 2048 个 FP32，固定任务数，改变向量长度 | 有效任务数、耗时、逻辑带宽 |
| A2 | 长度固定为 4194304，改变任务数 | 并行度提高后耗时是否继续下降 |
| A3 | 同一长度、任务数和数据类型，重复使用一组地址或轮换多组地址 | 用匹配两读一写的框架 maximum 作独立流式参照，同时记录地址覆盖量 |
| M0 | 对 64、128 阶方阵分别请求 32、64 两种输出块，请求 K 基础块 32，记录接口实际值 | 实际基础块、分段累加、零与单位阵、2049 精度探针、消去与随机数误差 |
| M1 | 优先固定 64 输出块，若仅 32 通过则采用 32；按上限扫描边长 | 规模与吞吐 |
| M2 | 固定 512 阶、核配置、输入输出地址 | 两种 Tile 的时间和请求字节模型 |
| M3 | 相同输入、输出精度和设备；自定义实现与 ACLNN 矩阵乘分别测量 | 核对 FP32 输出与误差，再比较时间 |

Add 和 Matmul 可分别用 `--workers` 限制任务数。每个 Matmul 入口都先在当前设备重做 M0。两种 Tile 都失败时停止；只有一种通过时，M2 无法做成对比较。首次 M0 结束后根据实际接口、容量和误差确定后续规模。M1／M3 的 `--max-n` 支持 64 至 1024 的五个离散边长，默认到 512。M0 的探针可以发现精度损失，最终仍需结合设备与工具链文档确认累加模式。

```sh
python src/hardware_dataflow/run.py A1 --library "$LIB" --output .local/lab02/A1.jsonl
python src/hardware_dataflow/run.py A2 --library "$LIB" --output .local/lab02/A2.jsonl
# L2_BYTES 填目标设备资料中核实的字节数
python src/hardware_dataflow/run.py A3 --l2-bytes "$L2_BYTES" --library "$LIB" --output .local/lab02/A3.jsonl
python src/hardware_dataflow/run.py M1 --max-n 128 --library "$LIB" --output .local/lab02/M1.jsonl
python src/hardware_dataflow/run.py M2 --library "$LIB" --output .local/lab02/M2.jsonl
python src/hardware_dataflow/run.py M3 --max-n 128 --library "$LIB" --output .local/lab02/M3.jsonl
```

A3 在设备上每组数组占 48 MiB，轮换组数至少为 2，并按 L2 容量增加。执行前核对可用显存；NumPy 参考值与回传也需要主机内存。框架 maximum 采用自己的调度，作为相同访问比例的参照。M3 使用 [ACLNN 适配入口](library_matmul.py)，调用 `aclnnMm` 并设置 `cubeMathType=-1`。每次调用重新取得 executor，事件区间可能包含准备造成的空隙，已用 profiler 的单内核时间复核。

纯 Cube 高阶 Matmul 在包含头文件前定义 `ASCENDC_CUBE_ONLY`。输入准备完成后同步设备，运行入口在导入框架前设置 `TASK_QUEUE_ENABLE=0`，保证框架事件与直接 ACL 调用的提交顺序。实际 K 基础块会由接口调整，相关数值已写入结果；比较时需连同输出块一起解释。

每组样本是同一 Stream 上两次设备事件之间的耗时，包含整组提交形成的空隙。预热至少 20 次，测量 5 组，每组至少 50 次，`--reps` 可增加组内次数。JSONL 中 `mean_us` 是每组折算的一次耗时，`q1_us` 至 `q3_us` 描述五组的波动。吞吐 TFLOP/s 用 FLOP 数除以微秒数再除以一百万，逻辑带宽 GB/s 用逻辑字节数除以微秒数再除以一千。

另用目标机支持的 profiler 单独采集 HBM 读写，将同一内核、同一配置的读写计数和调用次数归档，按次折算。JSONL 的 `logical_bytes` 是按显式分块推算的请求量，`hbm_bytes` 留待硬件计数。归档同时记录 SoC、驱动／固件、CANN、编译器、源码版本、实际可用资源及设备占用情况。
