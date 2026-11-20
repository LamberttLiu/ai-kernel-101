# 第 01 篇插图规划

对应[第 01 篇定稿正文](hello-world.md)。三张图均已有脚本及 PNG／SVG，按正文出现顺序编号。通用视觉规范与生成流程见[绘图工作流](../README.md)；本文件集中保存本篇的图示职责、生成入口、来源与限制。

# 逐图职责

| 图号 | 正文位置与解释目标 | 画法与必须保留的边界 |
| --- | --- | --- |
| fig1：CPU 与昇腾 NPU 之间的数据流 | “最小的 Kernel”中定义 Host／Device 后，区分内存传输与任务提交 | 主机内存与设备内存以 PCIe 数据箭头连接，任务提交使用虚线；设备侧示意 8 个耦合 AI Core，不表示实验设备布局、物理核数或 8 个 Block 的映射。Hello World 本身没有张量搬运 |
| fig2：从 Host 到 Device 的异步执行路径 | 解释 Stream 同步后，说明提交、等待、任务完成与资源清理的关系 | Host／NPU Stream 双轨道；提交后立即同步，不插入虚构的 CPU 计算。条长不表示耗时，不表示 Block 串行执行；明确为依赖示意、非实测时间线 |
| fig3：CPU／SIM／NPU 三种运行路径 | CPU 调试与 SIM 仿真的对照处，说明同一份源码由谁执行 | 三条路径分别构建同名 demo，不共用一个二进制。SIM 模型运行在主机 CPU 上，无需本地物理 NPU；本篇只验证功能，仿真耗时不等于真机性能 |

# 生成入口与文件

| 图号 | 生成脚本 | 图片 |
| --- | --- | --- |
| fig1 | [01-fig1-cpu-npu-dataflow.py](../src/01-fig1-cpu-npu-dataflow.py) | [PNG](../gen/01-fig1-cpu-npu-dataflow.png) · [SVG](../gen/01-fig1-cpu-npu-dataflow.svg) |
| fig2 | [01-fig2-host-kernel.py](../src/01-fig2-host-kernel.py) | [PNG](../gen/01-fig2-host-kernel.png) · [SVG](../gen/01-fig2-host-kernel.svg) |
| fig3 | [01-fig3-run-paths.py](../src/01-fig3-run-paths.py) | [PNG](../gen/01-fig3-run-paths.png) · [SVG](../gen/01-fig3-run-paths.svg) |

使用批量入口 render.py 并传入脚本文件名（不含扩展名）可生成单图，具体命令见绘图工作流。三图共用 theme.py。

# 本篇的样式细节

图 3 的 demo 框使用红色 #C00000、2 px 边框和近白 #FAFAFA 填充；流程箭头与分支线使用近黑 #20262C。Matplotlib 的线宽需按 px × 72 / DPI 换算为 pt。其余样式遵循通用规范，不在本页维护第二套主题参数。

# 来源、证据边界与历史记录

三图均为本项目按正文、仓库源码与所列资料生成的概念图，没有嵌入外部位图、没有使用性能数据，仓库整体许可证仍待作者选择。图 2 参考作者提供的 `cuda_streams.png` 的任务轨道、提交箭头与同步线表达，重新绘制为本样例的单 Kernel 流程；参考图的上游来源与许可未提供，不将其收入生成目录或插入正文。

| 图与源码 | 依据／修改内容 | 证据边界与引用 |
| --- | --- | --- |
| [01-fig1-cpu-npu-dataflow.py](../src/01-fig1-cpu-npu-dataflow.py) | CPU／主机内存经 PCIe 连接 NPU／设备内存；按作者指定示意 8 个 AI Core，每核展示 Vector／Cube 计算单元；以虚线区分任务提交 | 采用耦合架构抽象，省略 Scalar、片上存储、DMA 与实际片上互连；不表示 A2／A3 分离架构、真实核数、Block 映射或实测芯片布局。数据箭头表示一般算子流程，Hello World 本身没有张量搬运 |
| [01-fig2-host-kernel.py](../src/01-fig2-host-kernel.py) | [hello_world.cpp](../../../../lab/hello-world/src/hello_world.cpp) 与[01 正文](hello-world.md)；Host／NPU Stream 双轨道、提交箭头、纯色任务条和同步等待区 | 真机语境的执行依赖示意；样例提交后立即同步，不虚构其间有 CPU 计算；条长不表示时长，单条 Kernel 不表示 Block 串行执行或物理核映射 |
| [01-fig3-run-paths.py](../src/01-fig3-run-paths.py) | 以 [CMakeLists.txt](../../../../lab/hello-world/src/CMakeLists.txt) 中的可执行程序 `demo` 为产物；CPU／SIM／NPU 分别使用虚线框；明确 SIM 在主机 CPU 上运行仿真模型，无需本地物理 NPU | 同名 `demo` 分别构建，不表示三种模式共用同一二进制；CPU 为功能调试，SIM 为“目标模型中的功能与性能观察”，NPU 为“真实设备功能验证与性能测量”。仿真耗时不等于真机耗时，图形不对应具体板卡布局 |

初始记录依据为本工作区 2026-11-14 的源码与草稿；当时存在未提交编辑，该日期不能当作固定源码版本。外部资料链接沿用正文，不新增未经核对的硬件或软件版本声明。三图均由第 01 篇引用，生成命令如上。

图 3 于 2026-11-15 按作者要求修正为 `demo` 的实际构建运行路径，拆分 SIM／NPU 的观察范围；这次修改仅修正配图，不新增功能或性能测试证据。

新增异构关系图依据为 2026-11-15 的 01 草稿与作者绘图要求，同样由第 01 篇引用。图中 8 核是人为选择的图示数量，不能用来反推具体型号的物理规格。以下来源只用于概念与结构核对，不构成实验设备的软件版本记录：

- [昇腾官方基本架构，CANN 商用版 8.0.RC3](https://www.hiascend.com/doc_center/source/zh/canncommercial/80RC3/developmentguide/opdevg/Ascendcopdevg/atlas_ascendc_10_0008.html)：Vector／Cube 同核部署的耦合架构，以及矩阵核／向量核独立的分离架构。原图未复制，结构由本项目用 Matplotlib 重新绘制。
- [昇腾产品形态说明，60rc1 文档路径](https://www.hiascend.com/doc_center/source/zh/mindcluster/60rc1/description/productform/昇腾产品形态说明.pdf)：Host CPU 与昇腾 Device 通过 PCIe 连接的异构形态；不描述 PCIe 代际、带宽或特定板卡规格。
- [Ascend C 异构系统](https://asc.gitcode.com/guide/programming_guide/programming_model/heterogeneous_system.html)：Host／Device 的职责、独立内存空间、数据复制与 Kernel 下发。查阅日期 2026-11-15，页面标示 master、提交 `b31f8bdaed16`、构建于 2026-11-12 且包含未提交修改；这是开发预览资料，不当作稳定 CANN 版本声明。

单图生成：`.local/figures-venv/Scripts/python.exe docs/assets/figures/render.py 01-fig1-cpu-npu-dataflow`。

初始渲染环境记录（非当前机器环境声明）：Python 3.15.2、Matplotlib 3.11.2；实际字体为华文中宋 1.02、微软雅黑 6.31、Cascadia Code 2407.024，版本读取自字体元数据。字体使用与嵌入遵循各自所附产品条款和字体许可；未将字体文件收入仓库，也未另行授予字体许可。跨环境字体版本变化可能改变字宽，需重新目视检查。旧孪生调试参考图片在本轮整理前已从工作区删除，本轮未恢复；其来源与许可仍待核对。

