![AI Kernel 101：从 Hello World 到 Flash Attention，Ascend C · First Principles · Performance](docs/assets/brand/github-banner/ai-kernel-101_github-hero_brand-c_1600x600.png)

# AI Kernel 101：从 Hello World 到 Flash Attention 的 Ascend C 实践

<p align="center">
  <strong>从第一个 Kernel 出发，用模型与实验理解 AI 计算。</strong>
</p>

<p align="center">
  <a href="https://www.zhihu.com/people/270623d0990881c613d2b01b984a4302"><img src="https://img.shields.io/badge/知乎-0084FF?style=for-the-badge&amp;logo=zhihu&amp;logoColor=white" alt="作者知乎主页" /></a>
  <a href="https://xhslink.cn/o/IjuNqBlyYL"><img src="https://img.shields.io/badge/小红书-FF2442?style=for-the-badge&amp;logo=xiaohongshu&amp;logoColor=white" alt="作者小红书主页" /></a>
  <img src="https://img.shields.io/badge/微信公众号-柠檬沙棘-07C160?style=for-the-badge&amp;logo=wechat&amp;logoColor=white" alt="微信公众号：柠檬沙棘，请在微信内搜索" title="微信内搜索公众号：柠檬沙棘" />
</p>
<p align="center">
  <a href="docs/articles/hello-world.md">开始阅读</a> ·
  <a href="docs/README.md">文章目录</a> ·
  <a href="src/README.md">示例代码</a> ·
  <a href="lab/README.md">实验记录</a>
</p>

# 系列文章定位

> **以 Ascend C 为实践载体，从第一性原理理解 AI Kernel 的设计与性能优化**。

这里的第一性原理，是从**数学语义、数据依赖、硬件资源、存储层级、访存量与性能约束**等角度解释，再用实验检验判断。这一系列专栏文章，囊括了本人 Ascend C 真实学习中的问题、踩坑和失败经历，并将其转化为能够解释其他 Kernel 的工程案例。

本系列从最小 Kernel Hello World 出发，逐步讨论**数据流**、**Tiling**、**流水**、**归约**与**矩阵乘**，目标是完成范围明确的 Flash Attention 前向实现，并用模型和实验解释其行为。

本系列是作者对 AI Kernel 与推理系统性能工程的长期研究，当前十篇以 Ascend C 为实践载体。

# 目标读者

面向初步接触 Kernel 的 C/C++ 工程师，使用 Ascend C、CUDA、Triton 的算子开发者，以及希望理解性能瓶颈的推理与部署工程师。具备基本 C/C++、矩阵运算和编程经验即可；必要的体系结构和性能模型会在问题出现时解释，不要求预先掌握完整的 GPU 优化知识体系。

当前各篇处于不同撰写阶段，具体进度见下表。文章、代码和实验记录分别维护；已有草稿中的运行记录与尚未验证的内容保留原有状态。

# 专栏目录

| 篇次  | 标题                                    | 当前材料                                                                                           | 撰写阶段       |
| --- | ------------------------------------- | ---------------------------------------------------------------------------------------------- | ---------- |
| 01  | 没有昇腾 NPU，真的能写出第一个 Kernel 吗？           | [正文](docs/articles/hello-world.md)                                                             | 已完成        |
| 02  | 同样是计算，NPU 为什么要区分 Vector 和 Cube？       | [草稿](docs/drafts/hardware-dataflow.md)；[提纲](<planning/outlines/02-从算子看昇腾 NPU：计算、存储与数据流-提纲.md>) | 初稿完成，实验待设计 |
| 03  | 只做一次加法，为什么还要搬来搬去？                     | [草稿](docs/drafts/vector-add.md)                                                                | 初稿完成中      |
| 04  | 数据放不下怎么办？从一个 Kernel 理解 Tiling         | [尾块素材草稿，尚需补核内分块](docs/drafts/vector-add-tail.md)                                               | 初稿完成中      |
| 05  | Double Buffer 一定更快吗？用实验拆解计算流水         | [提纲](planning/outlines/05-计算流水与双缓冲-提纲.md)；实现与实验待完成                                             | 提纲         |
| 06  | Softmax 为什么难并行？从 Reduction 讲起         | [提纲](planning/outlines/06-归约与稳定Softmax-提纲.md)；实现与实验待完成                                         | 提纲         |
| 07  | 矩阵乘为什么快？理解 Cube 的数据复用                 | [提纲](planning/outlines/07-矩阵乘与数据复用-提纲.md)；实现与实验待完成                                             | 提纲         |
| 08  | Flash Attention 为什么不需要保存注意力矩阵？        | [论证提纲](<planning/outlines/08-Attention 为什么需要分块：从中间矩阵到在线递推-论证提纲.md>)                            | 提纲         |
| 09  | 从零拼出分块 Attention：Matmul、Softmax 与状态更新 | 已规划，待可行性验证                                                                                     | —          |
| 10  | Flash Attention 到底快在哪里？一次完整的性能分析      | 已规划，待实现与测量                                                                                     | —          |

01 中“没有 NPU”首先指没有本地设备；08 指不保存完整的分数／概率中间矩阵，并不表示总计算量或搬运量变为线性。完整状态见 [文章目录](docs/README.md)，技术依赖和标题映射见 [系列计划](planning/series-plan.md)。

# 项目导航

| 入口 | 内容 |
| --- | --- |
| [文章目录](docs/README.md) | 十篇文章的材料与当前状态 |
| [实验记录](lab/README.md) | 实验设计、复现方法与结果证据 |
| [示例代码](src/README.md) | 样例索引、构建要求、验证范围与来源许可 |
| [撰写流程](docs/README.md#统一撰写流程) | 文章阶段与状态维护规则 |
| [系列计划](planning/series-plan.md) | 技术依赖与逐篇论证规划 |
| [工作区管理](planning/workspace-management.md) | 目录结构、文档分工与本地／公开边界 |
| [协作约定](CONTRIBUTING.md) | 内容维护、复现与发布要求 |
