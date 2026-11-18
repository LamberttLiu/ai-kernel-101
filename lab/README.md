# Lab：可复现实验工作区

lab 是 AI Kernel 101 唯一的实验工程工作区，按主题统一管理实验目录、实验设计、源码实现、构建与运行入口、原始数据、结果分析和复现证据。docs 负责知识解释与文章呈现，引用 lab 中的实现和实验依据，不维护另一套独立的实验结果。

实验 `.log` 文件用于运行时排错，使用后删除，不上传仓库或在本地存档。需要保留的失败原因写入实验报告，测量数据使用 JSONL、CSV 等结构化文件归档。

# 实验主题

| 主题 | 入口 | 当前范围 |
| --- | --- | --- |
| Hello World | [主题说明与运行入口](hello-world/README.md) | Lab01 的四项 CPU、SIM、NPU 与无设备失败对照功能验证 |
| 硬件数据流与性能模型 | [主题说明与运行入口](hardware-dataflow/README.md) · [实验设计](hardware-dataflow/experiment-plan.md) · [实验报告](hardware-dataflow/reports/npu-report.md) | Lab02 的七项 NPU 实验已运行并归档；结果分析待完成 |
| 向量加与 Host/Device 传输 | [主题索引](vector-add/README.md) | 五组既有实现及各自复现说明；历史验证范围分别保留 |
| 固定 shape FlashAttention | [实现与复现入口](flash-attention-fixed/README.md) | CPU 参考已有运行记录但原始材料未归档；NPU／SIM 与性能未验证 |

实现来源、原始导入线索及许可待核对项见 [SOURCES.md](SOURCES.md)。

# 目录组织与职责

以实验主题为主要组织单元，不强制使用文章编号命名。每个主题尽可能自包含，源码、脚本、设计、结果和报告归属于同一主题；新增目录时使用稳定的主题名。通用代码只有形成明确复用需求后才抽取至 `lab/common/`，目前不创建空的 common 目录。

以下为按需使用的职责清单；各主题可以处于不同阶段，不要求凑齐所有文件或目录。

| 路径 | 职责 |
| --- | --- |
| `README.md` | 主题说明、实验索引、运行入口与当前验证状态 |
| `experiment-plan.md` | 研究问题、实验假设、变量控制、理论预测和判定标准 |
| `src/` | Kernel、Host 程序与必要构建配置；存在多个实现时保留清楚的子目录 |
| `scripts/` | 实验执行、采集、整理与内部分析脚本；草稿和定稿的插图规划及生成脚本统一放在 docs/assets/figures |
| `results/` | 按日期或批次归档必要原始数据、编译配置与环境信息 |
| `reports/` | 实验结果、模型对照、误差解释、失败记录和结论边界 |

# 复现与证据

每次正式实验必须能够关联源码版本、编译配置、运行环境、输入参数和结果数据。正式报告及承载实验结果的主题 README 使用 YAML frontmatter 的 `experiment_date` 和 `summary`；日期无依据时写未知，不用整理日期替代执行日期。

CPU、SIM、NPU 的功能与性能证据严格区分。理论估计、逻辑访存量、硬件实际计数与性能测量分别记录，不相互代替。实验阶段与文章写作阶段各自按实际证据维护，不能因目录规整提升完成度。

原始实验结果原则上保持不可变，重新运行使用新的输出文件或批次目录，不覆盖旧记录。大型构建产物、临时日志和不适合公开的数据按 .gitignore 约定管理；需要保留的失败原因写入报告，测量数据使用 JSONL、CSV 等结构化文件归档。

# 编号约定

实验使用 `Lab篇次-实验代号` 作为唯一编号，例如 `Lab02-M0`。篇次固定为两位数字，与文章目录一致；代号在同一篇内唯一，已有编号不因文档移动、排序或重复运行而改变，也不重新分配给其他实验。

第01篇用 `CPU`、`SIM`、`NPU` 标识三种功能验证，`NEG` 标识无设备时的失败对照。第02篇保留原有代号，`A1`—`A3` 对应 Add，`M0`—`M3` 对应 Matmul。新增实验沿用所属篇次并分配尚未使用的代号。

实验设计、报告标题、索引与正文引用使用完整编号。设计与报告的 YAML frontmatter 用 `experiment_ids` 列出所含实验；一份文档可以承载多个编号。同一实验后续重跑继续使用原编号，实际执行模式、输入配置、源码版本、日期与结果分别记入报告；编号不代表已执行或已通过，也不能替代 CPU／SIM／NPU 的证据分类。

# 实验索引

| 实验编号      | 研究问题／验证内容             | 当前阶段与模式               | 直接入口                                                  |
| --------- | --------------------- | --------------------- | ----------------------------------------------------- |
| Lab01-CPU | 无 NPU 时能否执行核函数入口与打印   | 已执行功能验证；CPU           | [实验报告](hello-world/reports/wsl-report.md#lab01-cpu)           |
| Lab01-SIM | 目标模型能否执行打印并正常结束       | 已执行功能验证；SIM           | [实验报告](hello-world/reports/wsl-report.md#lab01-sim)           |
| Lab01-NPU | 真实设备能否完成启动、同步与打印      | 已执行功能验证；NPU           | [实验报告](hello-world/reports/npu-report.md#lab01-npu)           |
| Lab01-NEG | 无设备时初始化失败能否以非零退出码暴露   | 已执行失败对照；无设备的 NPU 运行路径 | [实验报告](hello-world/reports/wsl-report.md#lab01-neg)           |
| Lab02-A1  | 向量长度变化与运行时间           | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/reports/npu-report.md#lab02-a1) |
| Lab02-A2  | 固定输入下的任务数与并行度         | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/reports/npu-report.md#lab02-a2) |
| Lab02-A3  | 地址复用、HBM 实际流量与带宽限制    | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/reports/npu-report.md#lab02-a3) |
| Lab02-M0  | 小矩阵正确性、分段累加与精度路径      | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/reports/npu-report.md#lab02-m0) |
| Lab02-M1  | 固定输出块时的矩阵规模扫描         | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/reports/npu-report.md#lab02-m1) |
| Lab02-M2  | 固定矩阵规模时的输出块与重读量对照     | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/reports/npu-report.md#lab02-m2) |
| Lab02-M3  | 计算上限与 HBM Roofline 对照 | 已执行；NPU，待分析             | [实验报告](hardware-dataflow/reports/npu-report.md#lab02-m3) |

本页只提供编号、阶段和入口，不汇总单次实验结果。实验报告在各主题目录单独维护，记录要求见[证据与复现约定](../CONTRIBUTING.md#证据与复现)。

# 路径迁移与历史证据

原根目录 src 已按主题并入 lab，源码和构建配置保持原样，现行复现命令使用以下入口。实验编号与此次迁移无关，全部保持稳定。

| 旧位置（仅供核对历史记录） | 当前入口 |
| --- | --- |
| `src/hello_world/` | [hello-world/src](hello-world/src/README.md) |
| `src/hardware_dataflow/` | [hardware-dataflow/src](hardware-dataflow/src/CMakeLists.txt)；Python 执行与 ACLNN 适配入口在 [scripts](hardware-dataflow/scripts/run.py) |
| `src/vector_add/` | [vector-add/src](vector-add/README.md) |
| `src/flash_attention_fixed/` | [flash-attention-fixed/src](flash-attention-fixed/README.md) |
| `src/README.md` | [实现来源与许可说明](SOURCES.md) |
| `lab/hello-world/verify.sh` | [hello-world/scripts/verify.sh](hello-world/scripts/verify.sh) |
| 主题根目录的 `wsl-report.md`、`npu-report.md` | 对应主题的 reports 目录；结果数据保留原位置 |

历史报告中的执行命令、环境快照与源码指纹清单保留运行时的路径。例如 Lab02 的 final-source-sha256.txt 仍使用旧路径，核对时将 kernels.cpp 对应到 hardware-dataflow/src，将 run.py 和 library_matmul.py 对应到 hardware-dataflow/scripts。迁移没有改写这些文件的内容或校验值，也没有重新运行实验。
