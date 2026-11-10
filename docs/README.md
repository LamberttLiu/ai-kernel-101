# AI Kernel 101：从 Hello World 到 Flash Attention 的 Ascend C 实践

以 Ascend C 为实践载体，从第一性原理理解 AI Kernel 的设计与性能优化。

本表管理十篇文章的篇次、对外标题、稳定主题和实际材料。标题更新不改变技术验证、定稿或发布状态；没有确认的平台记录，不推断为已发布。

| 篇次 | 对外标题                                           | 稳定主题／材料                                                                                               | 当前状态                                                        |
| ---- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| 01   | 没有昇腾 NPU，真的能写出第一个 Kernel 吗？         | [hello-world](drafts/hello-world.md)                                                                          | 早期草稿；保留 CPU/SIM/NPU 历史叙述，待证据与资料核对           |
| 02   | 同样是计算，NPU 为什么要区分 Vector 和 Cube？ | [hardware-dataflow 草稿](drafts/hardware-dataflow.md)；[原提纲](<../planning/outlines/02-从算子看昇腾 NPU：计算、存储与数据流-提纲.md>) | 初稿已形成；架构资料固定版本、技术与语言审核待完成；未新增实验 |
| 03   | 只做一次加法，为什么还要搬来搬去？                 | [vector-add](drafts/vector-add.md)                                                                            | 早期草稿；含静态 Tensor 与 TPipe/TQue 对照，保留基础版历史验证与五次耗时；队列版真机对照待补          |
| 04   | 数据放不下怎么办？从一个 Kernel 理解 Tiling        | [vector-add-tail](drafts/vector-add-tail.md)                                                                  | 草稿已补覆盖与容量模型；保留尾块素材，核内多轮实现与 NPU 验证待完成 |
| 05 | Double Buffer 一定更快吗？用实验拆解计算流水 | [pipeline 提纲](<../planning/outlines/05-计算流水与双缓冲-提纲.md>) | 提纲已形成；多轮单／双缓冲对照待实现，NPU 验证与性能待完成 |
| 06 | Softmax 为什么难并行？从 Reduction 讲起 | [softmax 提纲](<../planning/outlines/06-归约与稳定Softmax-提纲.md>) | 提纲已形成；独立归约与 Softmax 实现、功能和性能验证待完成 |
| 07 | 矩阵乘为什么快？理解 Cube 的数据复用 | [matmul 提纲](<../planning/outlines/07-矩阵乘与数据复用-提纲.md>) | 提纲已形成；独立 Matmul 基线、NPU 验证与融合接口核对待完成 |
| 08   | Flash Attention 为什么不需要保存注意力矩阵？       | [online-attention 论证](<../planning/outlines/08-Attention 为什么需要分块：从中间矩阵到在线递推-论证提纲.md>) | 论证和前置检查已形成；参考实现未执行                            |
| 09   | 从零拼出分块 Attention：Matmul、Softmax 与状态更新 | tiled-attention，见系列计划                                                                                  | 待接口可行性与目标设备验证                                      |
| 10   | Flash Attention 到底快在哪里？一次完整的性能分析   | attention-performance，见系列计划                                                                            | 待融合实现、性能对照与消融                                      |

完整依赖、逐篇论点、新旧标题映射、8周理想节奏与16周工作量估算见 [系列计划](../planning/series-plan.md)。不为尚未写作的篇章生成空正文。

# 正文与素材

```text
docs/
├── README.md              # 篇次、标题、材料与实际状态
├── ARTICLE_TEMPLATE.md    # 内部写作与审稿提示，不是固定章节模板
├── drafts/                # 当前写作的权威正文
├── articles/              # 实际定稿，由 drafts 移入
└── assets/
    ├── README.md          # 视觉规范、图表与素材来源
    └── images/            # 文稿配图唯一存放位置
```

定稿时移动同一份正文，不另复制平台原稿。修改对外标题优先改标题元数据、别名和目录，保留现有稳定文件名；必要移动时同步修复链接。旧篇次已按本表修正，章节内的“一、二”等章节编号不等于篇次。

正文只保留论证必需的代码；完整实现与构建配置在 src，具体实验方法与结果在 lab。图片和引用采用标准 Markdown 相对链接，带空格路径用尖括号包裹。公开文件不链接到仅本地存在的 inbox、账号配置或原始数据。
