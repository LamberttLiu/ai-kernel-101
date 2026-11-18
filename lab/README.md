# 实验目录

本目录按主题保存实验说明、复现脚本、必要数据和报告。完整实现与构建配置放在 [src](../src/README.md)。

实验 `.log` 文件用于运行时排错，使用后删除，不上传仓库或在本地存档。需要保留的失败原因写入实验报告，测量数据使用 JSONL、CSV 等结构化文件归档。

| 主题 | 入口 | 内容 |
| --- | --- | --- |
| 第01篇：Hello World | [实验说明](hello-world/README.md) | 四项 CPU、SIM、NPU 与无设备失败对照的功能验证 |
| 第02篇：硬件数据流与性能模型 | [实验报告](hardware-dataflow/npu-report.md) · [实验设计](hardware-dataflow/experiment-plan.md) | 七项 NPU 实验已运行并归档；结果分析待完成 |

# 编号约定

实验使用 `Lab篇次-实验代号` 作为唯一编号，例如 `Lab02-M0`。篇次固定为两位数字，与文章目录一致；代号在同一篇内唯一，已有编号不因文档移动、排序或重复运行而改变，也不重新分配给其他实验。

第01篇用 `CPU`、`SIM`、`NPU` 标识三种功能验证，`NEG` 标识无设备时的失败对照。第02篇保留原有代号，`A1`—`A3` 对应 Add，`M0`—`M3` 对应 Matmul。新增实验沿用所属篇次并分配尚未使用的代号。

实验设计、报告标题、索引与正文引用使用完整编号。设计与报告的 YAML frontmatter 用 `experiment_ids` 列出所含实验；一份文档可以承载多个编号。同一实验后续重跑继续使用原编号，实际执行模式、输入配置、源码版本、日期与结果分别记入报告；编号不代表已执行或已通过，也不能替代 CPU／SIM／NPU 的证据分类。

# 实验索引

| 实验编号      | 研究问题／验证内容             | 当前阶段与模式               | 直接入口                                                  |
| --------- | --------------------- | --------------------- | ----------------------------------------------------- |
| Lab01-CPU | 无 NPU 时能否执行核函数入口与打印   | 已执行功能验证；CPU           | [实验报告](hello-world/wsl-report.md#lab01-cpu)           |
| Lab01-SIM | 目标模型能否执行打印并正常结束       | 已执行功能验证；SIM           | [实验报告](hello-world/wsl-report.md#lab01-sim)           |
| Lab01-NPU | 真实设备能否完成启动、同步与打印      | 已执行功能验证；NPU           | [实验报告](hello-world/npu-report.md#lab01-npu)           |
| Lab01-NEG | 无设备时初始化失败能否以非零退出码暴露   | 已执行失败对照；无设备的 NPU 运行路径 | [实验报告](hello-world/wsl-report.md#lab01-neg)           |
| Lab02-A1  | 向量长度变化与运行时间           | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/npu-report.md#lab02-a1) |
| Lab02-A2  | 固定输入下的任务数与并行度         | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/npu-report.md#lab02-a2) |
| Lab02-A3  | 地址复用、HBM 实际流量与带宽限制    | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/npu-report.md#lab02-a3) |
| Lab02-M0  | 小矩阵正确性、分段累加与精度路径      | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/npu-report.md#lab02-m0) |
| Lab02-M1  | 固定输出块时的矩阵规模扫描         | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/npu-report.md#lab02-m1) |
| Lab02-M2  | 固定矩阵规模时的输出块与重读量对照     | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/npu-report.md#lab02-m2) |
| Lab02-M3  | 计算上限与 HBM Roofline 对照 | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/npu-report.md#lab02-m3) |

本页只提供编号、阶段和入口，不汇总单次实验结果。实验报告在各主题目录单独维护，记录要求见[证据与复现约定](../CONTRIBUTING.md#证据与复现)。
