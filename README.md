# AI Kernel 101：从 Hello World 到 Flash Attention 的 Ascend C 实践

这是一份面向 AI 工程师的中文技术向文章系列。

# 系列文章定位

> **以 Ascend C 为实践载体，从第一性原理理解 AI Kernel 的设计与性能优化**。

这里的第一性原理，是从**数学语义、数据依赖、硬件资源、存储层级、访存量与性能约束**等角度解释，再用实验检验判断。这一系列专栏文章，囊括了本人 Ascend C 真实学习中的问题、踩坑和失败经历，并将其转化为能够解释其他 Kernel 的工程案例。

本系列从最小 Kernel "Hello World " 出发，逐步讨论**数据流**、**Tiling**、**流水**、**归约**与**矩阵乘**，目标是完成范围明确的 Flash Attention 前向实现，并用模型和实验解释其行为。

这是作者长期研究 AI Kernel 与推理系统性能工程的一个系列文章。本期使用 Ascend C，后续研究可以扩展到 CUDA、Triton、Kernel Performance Modeling 和 AI Inference Systems；本期不增加这些独立专题。

# 目标读者

面向初步接触 Kernel 的 C/C++ 工程师，使用 Ascend C、CUDA、Triton 的算子开发者，以及希望理解性能瓶颈的推理与部署工程师。具备基本 C/C++、矩阵运算和编程经验即可；必要的体系结构和性能模型会在问题出现时解释，不要求预先掌握完整的 GPU 优化知识体系。

当前处于系列规划与草稿整理阶段。文章、代码和实验记录分别维护；已有草稿中的运行记录与尚未验证的内容保留原有状态。

# 专栏目录

| 篇次 | 对外标题                                           | 当前材料                                                                                     |
| ---- | -------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| 01   | 没有昇腾 NPU，真的能写出第一个 Kernel 吗？         | [草稿](docs/drafts/hello-world.md)                                                            |
| 02   | 同样是计算，NPU 为什么要区分 Vector 和 Cube？      | [草稿](docs/drafts/hardware-dataflow.md)；[提纲](<planning/outlines/02-从算子看昇腾 NPU：计算、存储与数据流-提纲.md>) |
| 03   | 只做一次加法，为什么还要搬来搬去？                 | [草稿](docs/drafts/vector-add.md)                                                             |
| 04   | 数据放不下怎么办？从一个 Kernel 理解 Tiling        | [尾块素材草稿，尚需补核内分块](docs/drafts/vector-add-tail.md)                                |
| 05 | Double Buffer 一定更快吗？用实验拆解计算流水 | [提纲](<planning/outlines/05-计算流水与双缓冲-提纲.md>)；实现与实验待完成 |
| 06 | Softmax 为什么难并行？从 Reduction 讲起 | [提纲](<planning/outlines/06-归约与稳定Softmax-提纲.md>)；实现与实验待完成 |
| 07 | 矩阵乘为什么快？理解 Cube 的数据复用 | [提纲](<planning/outlines/07-矩阵乘与数据复用-提纲.md>)；实现与实验待完成 |
| 08   | Flash Attention 为什么不需要保存注意力矩阵？       | [论证提纲](<planning/outlines/08-Attention 为什么需要分块：从中间矩阵到在线递推-论证提纲.md>) |
| 09   | 从零拼出分块 Attention：Matmul、Softmax 与状态更新 | 已规划，待可行性验证                                                                         |
| 10   | Flash Attention 到底快在哪里？一次完整的性能分析   | 已规划，待实现与测量                                                                         |

01 中“没有 NPU”首先指没有本地设备；08 指不保存完整的分数／概率中间矩阵，并不表示总计算量或搬运量变为线性。完整状态见 [文章目录](docs/README.md)，技术依赖和标题映射见 [系列计划](planning/series-plan.md)。

# 阅读与复现

- [文章目录与当前状态](docs/README.md)
- [实验说明、复现与结果记录](lab/README.md)
- [算子源码管理](src/README.md)
- [写作、复现与发布约定](CONTRIBUTING.md)

文章与实验代码都位于同一仓库：[LamberttLiu/ai-kernel-101](https://github.com/LamberttLiu/ai-kernel-101)，包含实验源码、CMake 和样例说明。文稿与实验分区管理。

# 示例代码

| 示例                                  | 内容                      | 代码说明                                                |
| ------------------------------------- | ------------------------- | ------------------------------------------------------- |
| Hello World                           | 最小 Kernel 启动与打印    | [说明](src/hello_world/README.md)                        |
| Vector Add · 00_basic                | 固定长度基础向量加        | [说明](src/vector_add/00_basic/README.md)                |
| Vector Add · 01_host_device_transfer | Host/Device 传输测速      | [说明](src/vector_add/01_host_device_transfer/README.md) |
| Vector Add · 02_tpipe_tque           | TPipe/TQue 缓冲与阶段交接 | [说明](src/vector_add/02_tpipe_tque/README.md)           |
| Vector Add · 03_uneven_split         | 长度不整除的尾块          | [说明](src/vector_add/03_uneven_split/README.md)         |
| Vector Add · 04_arbitrary_length     | 非对齐尾块与命令行长度    | [说明](src/vector_add/04_arbitrary_length/README.md)     |

现有练习以 CANN 9.1.0、`dav-2201` 为原记录基线。内核采用 .cpp 文件，并在对应 CMake 中显式指定 `LANGUAGE ASC`；仍需 CANN 的 ASC 编译工具链。传输测速样例使用 C++ 与 ACL，运行需要实际设备环境。

历史 CPU 验证范围与复现入口见 [2026-11-05 验证记录](lab/verification-2026-11-05.md)。原始日志未随记录归档；本轮规范重构没有重新执行 CPU、SIM 或 NPU 验证。推导、模型、CPU 功能、仿真、真机正确性和真机性能分别标注，不能互相替代。

样例来源为 [CANN Samples](https://gitcode.com/cann/cann-samples/)，上游许可入口为 [CANN Samples LICENSE](https://gitcode.com/cann/cann-samples/blob/master/LICENSE)。现有文件中的声明原样保留；来源、提交与适用许可仍有待逐项核对，见 [源码说明](src/README.md)。暂不为新增文稿或整个仓库统一选择许可证。

# 工作区结构

```text
ai-kernel-101/
├── README.md                       # GitHub 项目入口
├── 00-写作入口.md                  # 仅本地保留，通过 Obsidian 多端同步，不纳入 Git
├── planning/                       # 系列策划
│   ├── series-plan.md              # 总框架与写作计划
│   ├── outlines/                   # 篇章提纲与论证
│   └── inbox/                      # 本地创意与随笔，不纳入 Git
├── docs/                           # 文章与配图
│   ├── README.md                   # 系列目录与文章状态
│   ├── ARTICLE_TEMPLATE.md         # 写作与审稿提示
│   ├── drafts/                     # 写作中的正文
│   ├── articles/                   # 定稿正文
│   └── assets/                     # 视觉与来源规范；images 存配图
├── src/                            # 完整实现、CMake 与代码说明
│   ├── hello_world/
│   └── vector_add/                 # 基础、传输、队列与尾块样例
├── lab/                            # 实验方法、复现步骤、数据与分析
│   ├── README.md                   # 实验索引与组织约定
│   ├── TEMPLATE.md                 # 单次实验记录模板
│   └── verification-2026-11-05.md  # 历史 CPU 验证记录
├── publishing/                     # 知乎、公众号、小红书适配与发布记录
├── AGENTS.md                       # 本地写作协作约定，不纳入 Git
├── CONTRIBUTING.md                 # 内容维护流程
├── .obsidian/                      # Obsidian 配置，仅本地保留
├── sites/                          # 既有独立网站项目，不随本仓库提交
└── .local/                         # 本地专用材料，不纳入 Git
    ├── scripts/                    # 工作区检查工具
    └── maintenance/                # 维护记录与配置备份
```

- `planning/` 中经审查的技术计划与推导可以公开；`planning/inbox/` 默认仅本地保存。一般草稿是否公开由作者决定，不因未定稿自动判为敏感。
- `sites/` 是已有独立网站项目，保留原位，默认不随本系列仓库提交。编辑器配置与个人笔记同样默认排除。

组织规则和本次路径变更见 [工作区管理说明](planning/workspace-management.md)。

