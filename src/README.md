# 算子源码

这里只存可维护的实现与构建配置，不存文章正文、实验结论或生成的二进制文件。已从原本地代码仓库完整导入 6 个样例目录，共 6 份实现、6 份 CMakeLists.txt 与 6 份 README.md，包括原仓库尚未提交的 .cpp 改名和构建配置更新。

| 示例 | 入口 |
| --- | --- |
| 固定 shape FA 前向（CPU 参考通过；NPU 待验证） | [flash_attention_fixed](flash_attention_fixed/README.md) |
| Hello World | [hello_world](hello_world/README.md) |
| 基础 Add | [00_basic](vector_add/00_basic/README.md) |
| Host/Device 传输 | [01_host_device_transfer](vector_add/01_host_device_transfer/README.md) |
| TPipe/TQue Add | [02_tpipe_tque](vector_add/02_tpipe_tque/README.md) |
| 不均匀分核 | [03_uneven_split](vector_add/03_uneven_split/README.md) |
| 任意长度尾块 | [04_arbitrary_length](vector_add/04_arbitrary_length/README.md) |

源文件、构建文件和样例 README 与导入时的原本地工作副本逐文件核对 SHA-256；本次未改写这 18 个文件，也未重新运行样例。历史验证记录见 [lab](../lab/verification-2026-11-05.md)。

后续继续按算子与版本组织，例如 `softmax/`、`matmul/`、`attention/`，有实际实现时再创建对应目录。现有代码路径保留，不随文章篇次调整。

每个实现保留：源码、必要的 Host 调用与正确性检查、构建配置，以及简短的接口和来源说明。具体实验的复现步骤、数据和结果统一放在 [lab](../lab/README.md)。

引用或衍生官方、开源代码时，记录原始链接、提交、许可证并保留所需声明。仓库代码与文章的授权范围后续分别确定，本次不代作者选择许可证。

构建输出放入被忽略的 build 目录。不要把从 Markdown 提取出的片段直接视为已验证的完整工程；实现进入这里时，要明确它是否已构建、是否经过 CPU/SIM/真机验证。

# 来源与许可待核对

所属专栏：《AI Kernel 101：从 Hello World 到 Flash Attention 的 Ascend C 实践》。本轮只更新管理说明，不改六组实现、样例 README 或 CMake，也不重新运行样例。

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
