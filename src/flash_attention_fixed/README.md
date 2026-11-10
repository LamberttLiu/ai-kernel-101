# 固定 shape 的 Flash Attention 前向 MVP

一个可独立构建的 Ascend C 示例：`main.cpp` 包含 Kernel、ACL Host 启动、确定性输入、FP64 参考和正确性检查；`CMakeLists.txt` 构建 `fa_fixed`。

固定 B=1、H=1、Nq=Nkv=64、D=Dv=32，Q/K/V 连续 ND（等价于 BNSD=[1,1,64,32]），FP16 输入、FP32 输出和累计，non-causal，无 mask/dropout/PSE/Rope。Q 块和 K/V 块均为 32，形成 2×2 个块任务。不支持通过命令行更改 shape。

这是沿用 m/l/u 递推的**块级 GM 交接功能示例**，不是完整片上融合或高性能实现。没有设备端完整 N×N 分数/概率矩阵；这一点本身不能证明片上融合成立。

## 构建与运行

在已有 CANN 9.1 系列开发环境的 Linux NPU 主机中执行；需要提供 ASC CMake 包、bisheng、ACL、Tiling 库和 C++17。编译目标锁定 dav-2201，运行时检查实际架构；设备号固定 0。是否兼容具体安装版本须以实际构建和运行结果确认，脚本不安装依赖。

```bash
source /path/to/existing/cann/set_env.sh
# 从仓库根目录运行。每次实验使用新的目录标识。
cmake -S src/flash_attention_fixed -B .local/flash-attention-fixed/build-npu-01 \
  -DCMAKE_BUILD_TYPE=Release
cmake --build .local/flash-attention-fixed/build-npu-01 -j2
set -o pipefail
.local/flash-attention-fixed/build-npu-01/fa_fixed \
  .local/flash-attention-fixed/npu-01 2>&1 | tee .local/flash-attention-fixed/npu-01-console.log
```

只有在已存在的驱动库未进入动态库搜索路径时，才为当前进程补充实际驱动目录的 lib64/common、lib64/driver；不要替换系统库。首次失败保留日志并使用新输出目录重试。完整环境元数据按 [lab 记录](../../lab/flash-attention-fixed/README.md)登记。

仅运行 CPU 参考，不依赖 CANN：

```bash
cmake -S src/flash_attention_fixed -B .local/flash-attention-fixed/build-cpu-01 \
  -DFA_REFERENCE_ONLY=ON -DCMAKE_BUILD_TYPE=Release
cmake --build .local/flash-attention-fixed/build-cpu-01 -j2
.local/flash-attention-fixed/build-cpu-01/fa_fixed .local/flash-attention-fixed/cpu-new-01
```

两个模式均只有一个参数：**尚不存在的输出目录**。已有目录立即报错，不改写旧结果。退出码 0 表示所选模式的检查通过，非零表示失败；CPU 模式明确输出 `NPU_NOT_RUN`，不能用来替代 NPU 验证。

## 数据流与简化边界

每个 Q 块依次遍历两个 K/V 块：

1. Cube 计算 QKᵀ，将 FP32 分数块写入 GM；Vector 将其读入 UB。
2. Vector 缩放、求行最大值、计算稳定指数 E，更新 m/l，用 alpha 重缩放已有 u。
3. E 转为 FP16，经 GM 交给第二次 Matmul；EV 结果以 FP32 写回 GM。
4. Vector 读回 EV、累加 u；最后一个 K/V 块后输出 u/l。

第一块将 alpha 显式置零，避免初始化最大值影响全负分数。l 根据 FP32 E 求和，EV 使用量化后的 FP16 E；FP64 参考不模仿 E 的低精度舍入，因此误差检查包含该舍入误差。

同步采用 `IterateAll` / `WaitIterateAll` / `End` 及显式搬运屏障，单个活动 Vector worker 驱动注册的 Cube 服务。刻意不做多核分发、乒乓重叠或性能调优。改变并行度后不能复用当前共享 GM scratch 的假设。

| 存储 | 大小 | 生命周期/作用 |
| --- | ---: | --- |
| Q/K/V，GM | 各 4096 B | 整次运行 |
| 输出 O，GM | 8192 B | 每次运行写满 |
| QK 分数块，GM | 4096 B | 各块串行复用 |
| E 块，GM，FP16 | 2048 B | 各块串行复用 |
| EV 块，GM | 4096 B | 各块串行复用 |
| 调试 m/l/u 快照，GM | 17408 B | 4 组前缀状态；不是分数矩阵，调试开销计入运行 |
| 显式 UB 缓冲 | 19072 B | 分数、EV、E、u、m/l/alpha、归约工作区；不含 Matmul 内部资源 |
| 系统 workspace，GM | 运行时查询 | Matmul 服务所需，记录在 runtime.txt，不假定为零 |
| Matmul 内部 L1/L0 | 未在此独立计量 | 由 Tiling/API 管理，不能把显式 UB 量当作峰值片上占用 |

## 检查与输出

输入由固定种子 20261109 的整数 LCG 产生，为 [-1,1] 中的 1/16 整数倍，精确编码为 FP16。Host 对每个 K/V 前缀独立计算稳定 FP64 Attention，再与 CPU 在线递推或设备状态比较。

预先固定逐元素判据 `abs(got-ref) <= atol + rtol*abs(ref)`：CPU atol=rtol=1e-11；NPU m 为 2e-4，l/u/O 为 3e-3。NaN/Inf 失败，不能以允许失败元素比例放宽判据。另报告最大绝对误差和分母下限 1e-6 的最大相对误差。

NPU 模式每次输出先填 NaN 哨兵，运行 20 次，逐次检查全部前缀 m/l/u 和 O，并与第一次输出逐字节比较。每次先保存输出再判定，失败时保留输入、输出、metrics.csv 和 error.txt；运行时同步失败可能无法取得设备输出。

输出目录包含 q/k/v.bin、reference-output-fp64.bin、reference-states-fp64.bin、metrics.csv、status.txt；NPU 模式另有 runtime.txt、output-0..19.bin、states-0..19.bin。状态按 Q 块外循环、K/V 块内循环排列，每条记录为 m[32]、l[32]、u[32,32]。二进制采用主机原生字节序，目标为常见小端环境。没有性能计时或加速结论。

## 来源与验证状态

参考 ops-transformer 提交 `6f0d3ec620b338cab4f2d00322ff2e0d141419d2` 的 `attention/flash_attention_score/op_kernel/arch22/flash_attention_score_s1s2_bn2gs1.h`，借鉴两次 Matmul、GM 阶段交接和在线累计结构；上游文件声明 CANN Open Software License Agreement Version 2.0。本例未搬入其模板实现或第三方头文件，Kernel 算术以本项目此前归档的 m/l/u 探针为基础，改为固定 shape 和显式 GM scratch，并重新编写自包含 Host 验证。无需依赖本地 ops-transformer 仓库路径。

相较上游，本例把在线 u 留在 UB，使用逐行 Reduce/Exp 展开而非直接移植 SoftmaxFlashV2，不实现 SameAB/TSCM 缓存、异步流水、通用 Tiling、mask 或尾块。不会因参考上游就继承其测试结果。

本轮 CPU 参考模式已构建运行；NPU 分支未构建、未运行，SIM 未运行，性能未测。实际记录见 [lab](../../lab/flash-attention-fixed/README.md)。
