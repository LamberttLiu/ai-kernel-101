# 第 02 篇插图规划

对应[第 02 篇正文](../../../drafts/hardware-dataflow.md)。本文件与 [绘图源代码](../src/dataflow_figures.py)、生成图片统一放在 docs/assets/figures 下，供草稿和定稿共用，不在 lab 另存插图规划副本。绘图规范、字体、导出及批量生成方法见[绘图工作流](../README.md)。

概念图与理论模型按正文假设绘制；实验结果和原始数据继续以 [Lab02 实验报告](../../../../lab/hardware-dataflow/reports/npu-report.md)及其结果归档为依据。插图规划只管理文章中的图号、放置位置、画法、脚本和素材边界，不维护另一套实验结论。

# 配图规划

以下编号对应正文中的出现顺序。遵循[配图约定](../../README.md)，图 1—11 已按正文推导与所列资料重绘。图 12 待完成已归档真机结果的分析与图表数据整理。

| 图                   | 放置位置与要回答的问题                  | 画法与必须保留的边界                                                                                                                      |
| ------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| fig1：Add 按位置配对 | Add 的逐元素公式后 | 输入与输出按索引对齐成四列，每列只画一次加法，沿列即可读出对应输出。 |
| fig2：Safe Softmax 的共享分母 | 稳定 Softmax 公式后 | 用同一行输入贯穿最大值、平移、指数、求和与归一化。箭头画出整行汇成一个统计量，再由各位置使用的依赖。 |
| fig3：Matmul 的行列点积 | Matmul 的元素公式后 | 在两个输入矩阵中框出一行、一列，把三个乘积连到输出格，再指出横移一个输出格时仍然使用同一输入行。 |
| fig4：四种数据依赖         | 四个公式小节后，为什么公式短却难以同样并行？       | 四个小面板：Add 独立位置、Softmax 共享统计、Matmul 一行一列复用、Attention 中间结果生命周期。只画数据依赖，无实测时序                                                       |
| fig5：计算资源如何组织       | 耦合／分离与 GPU 对照后，分离到底分在哪里？     | 三个有明确标题的面板：耦合 AI Core、2201 分离 AIC／AIV、Ampere A100 SM。虚线表示控制、实线表示已核对的数据关系；不跨产品比较框数量和面积，不画成同等规格                                   |
| fig6：2201 内部数据路径    | 存储与搬运小节，用什么存储向计算单元供数？        | 展开 Scalar、UB、Vector，L1、L0A／L0B、Cube、L0C 与输出；标明 MTE2／MTE3 等已核对路径和 GM 交接。可补注 Fixpipe 结果处理，未核对通路不画；图注说明并非芯片布局或完整拓扑 |
| fig7：两条 Roofline    | Roofline 小节，读懂斜线、屋顶与交点       | Vector／Cube 分面，共享强度刻度，用正文假设参数；标 $I=\frac{1}{12}$ 、理想 Matmul 强度与对应交点。点只作理论位置，不给未测的纵坐标冒充结果                                                   |
| fig8：Add 两本账        | Add 建模后， $12T$ 与 $12L$ 为什么不同？     | $T=2048$ 的三块有效负载与 GM 两读一写并列，标 Byte、每任务与全程范围；容量条不是硬件占用测量                                                                           |
| fig9：矩阵乘法怎样分块 | 第一次引入输出块与求和分段后 | 三个矩阵均为 128 阶。用粗框固定左上角 64 行、32 列的输出块。前两轮分别突出左输入窗口右移和右输入窗口下移，每次移动 32 格。两轮乘积都累加到原输出位置，标注共 4 轮。 |
| fig10：Matmul 的复用与部分和 | Matmul 分块公式后， $Q_{\min}$ 为什么可能达不到？ | 同一 $A$ 输入被不同输出列块读取、 $B$ 被行块读取； $K$ 分段更新同一部分和。用颜色追踪一个数据块，不画“每次换块就清零”                                                                     |
| fig11：方阵乘法的 Cube Roofline | 方阵强度与分块重读推导后 | 采用正文假设的带宽和 Cube 算力，画出带宽斜线与水平屋顶。用空心符号标出理论上限 (16, 16)、(32, 32)、(100, 100)，注明方阵边长 64、128、400。在横轴用箭头标出 32 到 12.8 的变化，旁注“分块重读均经过 HBM”。 |
| fig12：实测与模型对照        | 实验完成后，在哪些输入上预测成立？            | Add 的规模／任务扫描与 Matmul 的分块对照分面，带误差范围；模型线用虚线、实测用点／实线。没有数据就保留正文占位，不生成伪曲线                                                            |

fig5 与 fig6 分开绘制：前者比较组织层级，后者解释内部存储路径，避免把不同厂商的完整微架构塞进一张图。

# 生成入口与文件

各图入口复用 [dataflow_figures.py](../src/dataflow_figures.py) 和 [theme.py](../src/theme.py)。在仓库根目录使用绘图工作流中的批量入口，传入下表脚本的文件名（不含扩展名）即可选择单图。

| 图号 | 生成脚本 | 生成图片 | 当前材料 |
| --- | --- | --- | --- |
| fig1 | [02-fig1-elementwise-add.py](../src/02-fig1-elementwise-add.py) | [PNG](../gen/02-fig1-elementwise-add.png) · [SVG](../gen/02-fig1-elementwise-add.svg) | 已有脚本与图片；来源、技术和发布审核仍按正文要求进行 |
| fig2 | [02-fig2-safe-softmax.py](../src/02-fig2-safe-softmax.py) | [PNG](../gen/02-fig2-safe-softmax.png) · [SVG](../gen/02-fig2-safe-softmax.svg) | 已有脚本与图片；来源、技术和发布审核仍按正文要求进行 |
| fig3 | [02-fig3-matrix-product.py](../src/02-fig3-matrix-product.py) | [PNG](../gen/02-fig3-matrix-product.png) · [SVG](../gen/02-fig3-matrix-product.svg) | 已有脚本与图片；来源、技术和发布审核仍按正文要求进行 |
| fig4 | [02-fig4-dependencies.py](../src/02-fig4-dependencies.py) | [PNG](../gen/02-fig4-dependencies.png) · [SVG](../gen/02-fig4-dependencies.svg) | 已有脚本与图片；来源、技术和发布审核仍按正文要求进行 |
| fig5 | [02-fig5-compute-units.py](../src/02-fig5-compute-units.py) | [PNG](../gen/02-fig5-compute-units.png) · [SVG](../gen/02-fig5-compute-units.svg) | 已有脚本与图片；来源、技术和发布审核仍按正文要求进行 |
| fig6 | [02-fig6-memory-paths.py](../src/02-fig6-memory-paths.py) | [PNG](../gen/02-fig6-memory-paths.png) · [SVG](../gen/02-fig6-memory-paths.svg) | 已有脚本与图片；来源、技术和发布审核仍按正文要求进行 |
| fig7 | [02-fig7-dual-roofline.py](../src/02-fig7-dual-roofline.py) | [PNG](../gen/02-fig7-dual-roofline.png) · [SVG](../gen/02-fig7-dual-roofline.svg) | 已有脚本与图片；来源、技术和发布审核仍按正文要求进行 |
| fig8 | [02-fig8-add-buffers.py](../src/02-fig8-add-buffers.py) | [PNG](../gen/02-fig8-add-buffers.png) · [SVG](../gen/02-fig8-add-buffers.svg) | 已有脚本与图片；来源、技术和发布审核仍按正文要求进行 |
| fig9 | [02-fig9-output-tiling.py](../src/02-fig9-output-tiling.py) | [PNG](../gen/02-fig9-output-tiling.png) · [SVG](../gen/02-fig9-output-tiling.svg) | 已有脚本与图片；来源、技术和发布审核仍按正文要求进行 |
| fig10 | [02-fig10-tile-reuse.py](../src/02-fig10-tile-reuse.py) | [PNG](../gen/02-fig10-tile-reuse.png) · [SVG](../gen/02-fig10-tile-reuse.svg) | 已有脚本与图片；来源、技术和发布审核仍按正文要求进行 |
| fig11 | [02-fig11-cube-roofline.py](../src/02-fig11-cube-roofline.py) | [PNG](../gen/02-fig11-cube-roofline.png) · [SVG](../gen/02-fig11-cube-roofline.svg) | 已有脚本与图片；来源、技术和发布审核仍按正文要求进行 |
| fig12 | 待结果分析与图表数据整理后编写 | 未生成，不创建空图片链接 | 使用通过正确性检查的 NPU 结果，分别标明事件计时、内核时间、逻辑流量与硬件计数 |

# 插图资料与适用边界

- [昇腾基本架构说明](https://www.hiascend.com/doc_center/source/zh/canncommercial/80RC3/developmentguide/opdevg/Ascendcopdevg/atlas_ascendc_10_0008.html)：CANN 8.0.RC3 术语来源，解释同核部署的耦合／分离；不作为本次工具链版本依据。
- [NPU 架构版本 2201](https://asc.gitcode.com/guide/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2201.html)：在线开发文档，已查阅 AIC／AIV、GM 交接及存储说明；发布前保存可追溯版本。实际容量与通路仍需与目标设备／安装文档匹配。
- [NVIDIA A100 架构白皮书](https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/nvidia-ampere-architecture-whitepaper.pdf)：V1.0，第 20—23 页用于 SM 与 Tensor Core 组织对照；仅讨论 A100，不外推全部 NVIDIA 架构。
- [Ampere 调优指南](https://docs.nvidia.com/cuda/ampere-tuning-guide/index.html)：用于核对 Tensor Core 与异步复制能力，在线文档需固定版本。
- [Roofline 原始技术报告](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-134.html)与 [Berkeley Lab 模型说明](https://amcr.lbl.gov/departments/computer-science-department/ppan/roofline-performance-model/)：用于性能包络、强度及模型限制；本文两条计算屋顶与分块流量公式为面向当前问题的建模。
