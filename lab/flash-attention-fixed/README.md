# 固定 shape FA 前向示例：方法与验证记录

源码与构建入口：[main.cpp](../../src/flash_attention_fixed/main.cpp)、[CMakeLists.txt](../../src/flash_attention_fixed/CMakeLists.txt)、[复现说明](../../src/flash_attention_fixed/README.md)。

# 问题、假设与对照

问题：在 DAV_2201 编程模型下，用两次块级 Matmul、显式 GM/UB 搬运和 Vector m/l/u 更新表达一个固定 shape 的前向 Attention。

假设：B=H=1、N=64、D=32、BR=BC=32，两个 Q 块分别遍历两个 K/V 块，最终 O 和每个已处理 K/V 前缀的 m/l/u 满足预先设定误差。对照为独立计算各前缀的 FP64 稳定 Attention，另有 CPU 在线递推。GM 中转不视作目标片上融合通过，不提出提速假设。

# 证据与版本

起始仓库提交：`513f171246307efc3b9d24a3e62f8c0bc642737d`。本例为新增、尚未提交源码，固定版本见 [源码及 CPU 二进制哈希](runs/2026-11-09-cpu/source-binary.sha256)。

参考上游 ops-transformer `6f0d3ec620b338cab4f2d00322ff2e0d141419d2` 的 arch22 S1/S2 分块结构，不移植其完整工程。本项目此前归档 m/l/u 探针用于算术实现基础；本次显式 GM Matmul 输出属于新代码，不能继承旧探针的真机结果。

证据分类：CPU 功能检查已执行成功；NPU 构建、NPU 功能、SIM、性能均未执行。不是旧实验结果迁入或重命名。

# 设备、环境与编译

本次 CPU 执行环境：WSL Linux x86_64，GNU C++ 13.3.0（Ubuntu 13.3.0-6ubuntu2~24.04.1），CMake 3.28.3，C++17，Release。独立交叉检查使用 Windows 已有 Python 3.12 / NumPy 2.3.5。

NPU 目标为 dav-2201；本次未连接设备，所以具体 SoC、驱动、固件、CANN、bisheng 版本与运行状态均为未核对，不从此前实验推断。NPU 程序会记录运行时 SoC、架构检查和系统 workspace 大小；仍需人工补录其余环境。

实际构建选项：`-DFA_REFERENCE_ONLY=ON -DCMAKE_BUILD_TYPE=Release`。见 [configure](runs/2026-11-09-cpu/configure.log)、[build](runs/2026-11-09-cpu/build.log)、[run](runs/2026-11-09-cpu/run.log)。日志中的当前仓库绝对路径替换为 `<REPO>`，原始副本在本地 `.local/flash-attention-fixed/original-logs`。

# 输入、正确性与测量方法

输入固定种子 20261109、整数 LCG、[-1,1] 中的 1/16 整数倍；保存真实 FP16 输入字节。数据布局、状态排列、缓冲清单与执行步骤见源码 README。

预先固定逐元素 `abs(error) <= atol + rtol*abs(reference)`：CPU 1e-11/1e-11，NPU m 为 2e-4/2e-4，NPU l/u/O 为 3e-3/3e-3；非有限值失败。近零相对误差分母下限 1e-6，仅作报告指标，不替代逐元素判据。

NPU 模式设计为 20 次输出/中间状态校验及逐字节重复一致性检查；本次尚未执行。没有性能计时、预热或速度对照。

# 实际结果与数据

[CPU 指标](runs/2026-11-09-cpu/metrics.csv)：共 6400 个数值比较，失败 0。

| 数量 | 比较元素数 | 最大绝对误差 |
| --- | ---: | ---: |
| O | 2048 | 1.3877787807814457e-16 |
| m | 128 | 2.2204460492503131e-16 |
| l | 128 | 1.4210854715202004e-14 |
| u | 4096 | 3.5527136788005009e-15 |

另用 NumPy 解码 q/k/v.bin，与 LCG 数值逐元素精确核对，并重新计算各前缀 FP64 参考：输入 6144 个元素精确一致，O 最大绝对差 1.6653345369377348e-16，前缀状态最大绝对差 1.4210854715202004e-14。[交叉检查结果](runs/2026-11-09-cpu/independent-check.json)。

已有输出目录重跑返回非零，原结果哈希全部保持一致：[防覆盖检查](runs/2026-11-09-cpu/overwrite-check.log)。本地输入、参考输出和完整状态位于 `.local/flash-attention-fixed/cpu01`；数据可由固定输入规则重建。

# 失败、解释与边界

当前仅能确认 Host 参考模式可构建、参考递推在本固定输入上成立及输出目录保护有效。NPU 分支仍可能存在具体 CANN 版本接口/编译差异，不能据 CPU 结果宣称构建成功或 Kernel 正确。

未覆盖：其他输入分布、形状、dtype、causal、非对齐尾块、多核并行、设备资源峰值、性能。这里的普通随机 case 不替代后续最大值增大、相等分数、极值、同步置换等完整验证集。

下一步最小动作：在已有匹配 CANN 的 DAV_2201 主机中构建 NPU 模式，保存源码/二进制哈希及环境，运行到新目录，先检查全部前缀状态与 O；失败时保留目录和 console 日志，修复后用新目录重测。通过后再考虑更多输入和性能实验。

# 双向引用

沿用 [系列计划](../../planning/series-plan.md)的第 08—10 篇 m/l/u 与融合门槛。本次不修改正文、旧实现或历史实验，不提交、推送或发布。
