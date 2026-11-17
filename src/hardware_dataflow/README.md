# 第 02 篇实验代码

[实验设计与判据](../../lab/hardware-dataflow/experiment-plan.md) · [Ascend C 内核](kernels.cpp) · [分组测量与数值检查](run.py)

当前版本尚未构建或运行。以下命令供作者确认后在目标 NPU 主机上使用。需要支持 dav-2201 的 CANN／ASC 编译环境、与其匹配的 PyTorch 和 torch-npu，以及 NumPy。实验由 Python 分配 ND 连续张量，Ascend C 内核与框架使用同一设备和 Stream。

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
| M0 | 对 64、128 阶方阵分别请求 32、64 两种输出块，沿 K 每段 32 | 实际基础块、分段累加、零与单位阵、2049 精度探针、消去与随机数误差 |
| M1 | 优先固定 64 输出块，若仅 32 通过则采用 32；按上限扫描边长 | 规模与吞吐 |
| M2 | 固定 512 阶、核配置、输入输出地址 | 两种 Tile 的时间和请求字节模型 |
| M3 | 相同输入、输出精度和设备；自定义实现与框架矩阵乘分别测量 | 两条吞吐曲线；若框架不支持 FP32 输出则该对照不可用 |

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

A3 在设备上每组数组占 48 MiB，轮换组数至少为 2，并按 L2 容量增加。执行前核对可用显存；NumPy 参考值与回传也需要主机内存。框架 maximum 采用自己的调度，作为相同访问比例的参照。M3 的库对照需要后端实现 `torch.mm(..., out_dtype=torch.float32, out=...)`；缺少接口时保留错误记录及已经取得的自定义内核记录，另行核实同精度的库入口。

每组样本是同一 Stream 上两次设备事件之间的耗时，包含整组提交形成的空隙。预热至少 20 次，测量 5 组，每组至少 50 次，`--reps` 可增加组内次数。JSONL 中 `mean_us` 是每组折算的一次耗时，`q1_us` 至 `q3_us` 描述五组的波动。吞吐 TFLOP/s 用 FLOP 数除以微秒数再除以一百万，逻辑带宽 GB/s 用逻辑字节数除以微秒数再除以一千。

另用目标机支持的 profiler 单独采集 HBM 读写，将同一内核、同一配置的读写计数和调用次数归档，按次折算。JSONL 的 `logical_bytes` 是按显式分块推算的请求量，`hbm_bytes` 留待硬件计数。归档同时记录 SoC、驱动／固件、CANN、编译器、源码版本、实际可用资源及设备占用情况。
