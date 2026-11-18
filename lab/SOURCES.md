# 实现入口、来源与许可

本页维护各主题的实现入口和来源线索。所有实现、构建配置、运行脚本与实验依据均归入 lab 的对应主题，组织规则与实验编号见 [实验工作区](README.md)。最初曾从原本地代码仓库导入六组样例，包含当时尚未提交的 .cpp 改名和构建配置更新；下表还列出后续新增的硬件数据流和固定 shape Attention 实现。

| 示例 | 入口 |
| --- | --- |
| 第 02 篇 Add 与 Matmul（NPU 已运行，结果待分析） | [hardware_dataflow](hardware-dataflow/README.md) |
| 固定 shape FA 前向（CPU 参考通过；NPU 待验证） | [flash_attention_fixed](flash-attention-fixed/README.md) |
| Hello World | [hello_world](hello-world/src/README.md) |
| 基础 Add | [00_basic](vector-add/src/00_basic/README.md) |
| Host/Device 传输 | [01_host_device_transfer](vector-add/src/01_host_device_transfer/README.md) |
| TPipe/TQue Add | [02_tpipe_tque](vector-add/src/02_tpipe_tque/README.md) |
| 不均匀分核 | [03_uneven_split](vector-add/src/03_uneven_split/README.md) |
| 任意长度尾块 | [04_arbitrary_length](vector-add/src/04_arbitrary_length/README.md) |

导入时，源文件、构建文件和样例 README 曾与原本地工作副本逐文件核对 SHA-256；当时未改写这 18 个文件，也未重新运行样例。后续 Hello World 的源码修改及 CPU／SIM／NPU 功能实测另见[本轮记录](hello-world/README.md)。

后续继续按算子与版本组织，例如 `softmax/`、`matmul/`、`attention/`，有实际实现时再创建对应目录。代码按实验主题归属放在 src，实验代号不随文章标题或物理路径改变。

每个实现保留：源码、必要的 Host 调用与正确性检查、构建配置，以及简短的接口和来源说明。复现步骤、执行脚本、数据和分析报告与实现归属于同一实验主题。

引用或衍生官方、开源代码时，记录原始链接、提交、许可证并保留所需声明。仓库代码与文章的授权范围后续分别确定，本次不代作者选择许可证。

构建输出放入被忽略的 build 目录。不要把从 Markdown 提取出的片段直接视为已验证的完整工程；实现进入这里时，要明确它是否已构建、是否经过 CPU/SIM/真机验证。

# 来源与许可待核对

所属专栏：《AI Kernel 101：从 Hello World 到 FlashAttention》。本次仅调整目录和运行路径，保留算法、CMake 与原始结果，不重新运行技术实验。以下来源线索及许可缺项仍待逐项核对。

| 样例 | 现有来源线索 | 尚待核对 |
| --- | --- | --- |
| hello_world | 第一篇指向 CANN Samples 提交 3a85e824537feaef646bd89eb4d0e799cc2886b5 | 与当前 .cpp／CMake 的差异、适用许可及声明 |
| vector_add/00_basic | 第三篇引用同一固定提交的 Add | 上游到当前实现的修改边界、声明及同步语义 |
| vector_add/01_host_device_transfer | 本项目独立 ACL 传输程序 | 作者确认来源、公开权利和验证范围 |
| vector_add/02_tpipe_tque | README 记载提交 1e8cbde3cebea3e9e4a90c28c00dc6de99614c9a，同时仍有 master 链接 | 固定来源匹配、版权声明、衍生修改与适用许可 |
| vector_add/03_uneven_split | 基础 Add 的尾块衍生练习 | 上游基线、衍生修改与声明 |
| vector_add/04_arbitrary_length | 基础／尾块 Add 的非对齐衍生练习 | 同上；接口和目标 NPU 约束另需验证 |

部分 CMake 写有 CANN Open Software License Agreement Version 2.0 并引用根 LICENSE，但当前根目录没有相应许可文本；一些 .cpp 仅含简短文件说明。这里记录的是声明与归档缺项，不代替逐项授权核验，也不直接认定侵权或许可已完备。许可证暂不选择，不用统一新许可证覆盖上游条款，不改写既有文件头。

技术审查仍需区分：已有 TPipe/TQue 样例深度1且没有双缓冲；已有尾块不是核内多轮Tiling。部分样例 README 对 PipeBarrier 的保证范围与正文待核实说明不一致，须按实际版本、编译模型与设备验证；本轮不据此修改计算逻辑或宣称验证通过。
