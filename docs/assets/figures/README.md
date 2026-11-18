# Matplotlib 绘图工作流

新配图以白色为背景，红色和天蓝色为主题色，其他元素使用黑白灰。统一导出 **1920×1080 PNG** 和声明相同像素尺寸的 SVG，覆盖 `gen` 中的同名文件。所有图直接使用最终画布的像素坐标排版，图形与文字均从源代码重新渲染。优先用干净的纯色块、细线与统一间距塑造图形。概念图、模型预测、实测结果必须在图中区分，不能用示意布局暗示实测时序或物理资源数量。

插图以直观图形为主体：保留标题，用任务条、轨道、箭头、同步线或对象图形表达关系，文字只标识必要对象和动作。不采用分栏文字卡片、重复副标题或长段解释；能力范围与完整技术说明留在正文。异步图参照作者提供的 `cuda_streams.png` 的轨道表达方式，按当前样例重新绘制。

统一排版：标题两行，中文在上 **42 px**、英文在下 **32 px**；正文与标注按上一版的层级恢复为 **18–34 px**，中文在上、英文在下，每组中英使用相同字号。中文标题使用华文中宋，中文正文与标注使用微软雅黑；所有英文及数字使用 Cascadia Code。框内双语文字作为整体垂直居中，按各自字号的实际字形边界计算。页眉、页脚均居中添加浅灰色 `AI Kernel 101 | From Hello World to Flash Attention in Ascend C @LambertLiu` 水印，颜色 `#CFD3D7`，字号 **18 px**。所有字号均为最终输出像素中的整数值，固定 `DPI=100`，仅在调用 Matplotlib 时按 `px * 72 / DPI` 换算为 pt；不额外缩放字号或保留另一套设计坐标。单图脚本通过整数 `size` 明确各处标注字号，标题保留 42／32 px；正文标注恢复的是 `dca0236` 版本最终输出字号，逐项四舍五入取整。

## 插图规划与生成的归属

草稿和定稿的插图规划、生成脚本及图片统一维护在本目录：`plans/` 保存逐篇规划，`src/` 保存绘图代码，`gen/` 保存输出。文章从 drafts 移入 articles 时沿用同一套规划与图片，不复制另一份；实验设计、原始数据和分析报告仍属于 lab，正文图按需要引用其证据。

| 篇章 | 规划与资料入口 | 生成入口 |
| --- | --- | --- |
| 01：Hello World | 本页[来源与证据边界](#本批次来源与证据边界) | `src/01-fig*.py`，由 `render.py` 生成同名 PNG／SVG |
| 02：硬件数据流 | [逐图规划、脚本和图片索引](plans/02-hardware-dataflow.md) | `src/02-fig*.py` 与 `src/dataflow_figures.py` |

后续文章有实际插图规划时，在 plans 中按篇次和稳定主题建立文件；未形成规划时不创建空文档。逐篇规划记录图号、正文位置、解释目标、画法、证据与来源边界，以及实际存在的脚本和输出入口。

## 文件与生成

```text
docs/assets/figures/
├── plans/                             # 草稿与定稿共用的逐篇插图规划
│   └── 02-hardware-dataflow.md
├── src/
│   ├── theme.py                       # 配色、字体、尺寸、布局与导出函数
│   ├── 01-fig1-cpu-npu-dataflow.py      # 异构执行关系；按正文出现顺序从 fig1 编号
│   ├── 01-fig2-host-kernel.py
│   └── 01-fig3-run-paths.py
├── gen/                               # 与绘图脚本同名的 PNG 和 SVG
├── render.py                          # 批量入口，也支持选择单图
└── requirements.txt                   # 本次验证的 Matplotlib 版本
```

在仓库根目录运行（Python 需满足所固定 Matplotlib 的版本要求）：

```powershell
python -m venv .local/figures-venv
.local/figures-venv/Scripts/python.exe -m pip install -r docs/assets/figures/requirements.txt
.local/figures-venv/Scripts/python.exe docs/assets/figures/render.py
```

当前工作区已通过 uv 创建 `.local/figures-venv` 并安装依赖，可以直接运行最后一行。如用 uv 安装依赖，可运行：

```powershell
$env:UV_CACHE_DIR = "$PWD/.local/uv-cache"
uv pip install --python .local/figures-venv/Scripts/python.exe -r docs/assets/figures/requirements.txt
```

选择单图或直接执行绘图脚本：

```powershell
.local/figures-venv/Scripts/python.exe docs/assets/figures/render.py 01-fig2-host-kernel
.local/figures-venv/Scripts/python.exe docs/assets/figures/src/01-fig3-run-paths.py
```

路径按脚本位置解析，换工作目录不改变输出位置。Linux／WSL 环境把解释器路径换为 `.local/figures-venv/bin/python`，并配置下面指定的字体。

正文在 `docs/drafts` 或 `docs/articles` 中这样引用：

```markdown
![从 Host 到 Device 的异步执行路径](../assets/figures/gen/01-fig2-host-kernel.png)

图 2：从 Host 到 Device 的异步执行路径；执行关系示意，非实测时间线。
```

## 调整与检查

主题集中在 [src/theme.py](src/theme.py)：按作者提供的 `color.png` 实心色块取样，天蓝为 **RGB(0, 176, 240)／`#00B0F0`**，红色为 **RGB(192, 0, 0)／`#C00000`**。主要填充使用这两种纯色及深灰 `#3C4650`，浅色由 `tint` 与白色混合生成，不再沿用旧主题色。颜色不独立承担语义，箭头方向、虚实线及标签也应说明含义。布局坐标以像素计，原点在左上角，画布尺寸、标题与正文字号、水印及 DPI 集中配置；导出不使用自动紧裁，保证 PNG 尺寸稳定。

新增单图使用 `篇次-fig序号-英文主题.py` 命名，复用 `canvas(title_zh, title_en)`、`bilingual(ax, x, y, zh, en, color=INK, ha="center", gap=None, size=None)`、`bilingual_in_box(ax, x, y, w, h, zh, en, color=INK, line_gap=12, size=None)`、`box`、`arrow`、`save`。`canvas` 统一生成双语标题和上下水印，`bilingual` 保证中文在上、英文在下，通过 `size` 为每组标注设置相同的中英字号，默认 28 px；字号按上一版最终输出像素值四舍五入取整，`bilingual_in_box` 按两行字形的实际高度与行间距在框内整体居中；图形细节用 Matplotlib 图元绘制。批量入口会发现 `src/??-fig*.py`；辅助模块不生成图片。每次修改后重新生成 PNG／SVG，逐张检查字号、中文、遮挡、箭头、留白和正文含义，再检查 Markdown 相对链接。脚本只自动检查文字是否超出画布，不能替代视觉与技术审核。

图 3 的可执行程序 `demo` 框使用红色 `#C00000` 边框、2 px 线宽，内部填充近白浅灰 `#FAFAFA`，标注使用深色。图 3 的全部流程箭头及分支连接线统一为近黑深灰 `#20262C`。Matplotlib 线宽参数以 pt 计，2 px 按 `2 * 72 / DPI` 转换。

字体固定按文字角色选择：

| 角色 | 字体 | 字体文件覆盖变量 |
| --- | --- | --- |
| 中文标题 | 华文中宋（STZhongsong） | `FIGURE_TITLE_CHINESE_FONT` |
| 中文正文与标注 | 微软雅黑（Microsoft YaHei） | `FIGURE_CHINESE_FONT` |
| 全部英文与数字，含标题、标注和水印 | Cascadia Code | `FIGURE_ENGLISH_FONT` |

中英混排时，英文与数字由 Cascadia Code 渲染，中文按标题／正文角色回退到华文中宋／微软雅黑。字体缺失时明确报错；覆盖变量的值为有权使用的字体文件路径，不自动改用其他字体。Cascadia Code 也会从 `.local/figure-fonts/CascadiaCode-Regular.ttf` 加载，不要求系统安装。当前本地字体取自[微软官方固定版本 v2407.24](https://github.com/microsoft/cascadia-code/releases/tag/v2407.24) 的 `ttf/static/CascadiaCode-Regular.ttf`。

SVG 文字导出为路径，避免阅读端字体缺失；字体文件只留本地，不进入公开图包。修改图中文字应回到 Python 源码。

## 本批次来源与证据边界

三图均为本项目按正文、仓库源码与所列资料生成的概念图，没有嵌入外部位图、没有使用性能数据，仓库整体许可证仍待作者选择。图 2 参考作者提供的 `cuda_streams.png` 的任务轨道、提交箭头与同步线表达，重新绘制为本样例的单 Kernel 流程；参考图的上游来源与许可未提供，不将其收入生成目录或插入正文。

| 图与源码 | 依据／修改内容 | 证据边界与引用 |
| --- | --- | --- |
| [01-fig1-cpu-npu-dataflow.py](src/01-fig1-cpu-npu-dataflow.py) | CPU／主机内存经 PCIe 连接 NPU／设备内存；按作者指定示意 8 个 AI Core，每核展示 Vector／Cube 计算单元；以虚线区分任务提交 | 采用耦合架构抽象，省略 Scalar、片上存储、DMA 与实际片上互连；不表示 A2／A3 分离架构、真实核数、Block 映射或实测芯片布局。数据箭头表示一般算子流程，Hello World 本身没有张量搬运 |
| [01-fig2-host-kernel.py](src/01-fig2-host-kernel.py) | [hello_world.cpp](../../../lab/hello-world/src/hello_world.cpp) 与[01 正文](../../articles/hello-world.md)；Host／NPU Stream 双轨道、提交箭头、纯色任务条和同步等待区 | 真机语境的执行依赖示意；样例提交后立即同步，不虚构其间有 CPU 计算；条长不表示时长，单条 Kernel 不表示 Block 串行执行或物理核映射 |
| [01-fig3-run-paths.py](src/01-fig3-run-paths.py) | 以 [CMakeLists.txt](../../../lab/hello-world/src/CMakeLists.txt) 中的可执行程序 `demo` 为产物；CPU／SIM／NPU 分别使用虚线框；明确 SIM 在主机 CPU 上运行仿真模型，无需本地物理 NPU | 同名 `demo` 分别构建，不表示三种模式共用同一二进制；CPU 为功能调试，SIM 为“目标模型中的功能与性能观察”，NPU 为“真实设备功能验证与性能测量”。仿真耗时不等于真机耗时，图形不对应具体板卡布局 |

依据为本工作区 2026-11-14 的源码与草稿；草稿存在未提交编辑，不把日期当作固定源码版本。外部资料链接沿用正文，不新增未经核对的硬件或软件版本声明。三图均由第 01 篇引用，生成命令如上。

图 3 于 2026-11-15 按作者要求修正为 `demo` 的实际构建运行路径，拆分 SIM／NPU 的观察范围；这次修改仅修正配图，不新增功能或性能测试证据。

新增异构关系图依据为 2026-11-15 的 01 草稿与作者绘图要求，同样由第 01 篇引用。图中 8 核是人为选择的图示数量，不能用来反推具体型号的物理规格。以下来源只用于概念与结构核对，不构成实验设备的软件版本记录：

- [昇腾官方基本架构，CANN 商用版 8.0.RC3](https://www.hiascend.com/doc_center/source/zh/canncommercial/80RC3/developmentguide/opdevg/Ascendcopdevg/atlas_ascendc_10_0008.html)：Vector／Cube 同核部署的耦合架构，以及矩阵核／向量核独立的分离架构。原图未复制，结构由本项目用 Matplotlib 重新绘制。
- [昇腾产品形态说明，60rc1 文档路径](https://www.hiascend.com/doc_center/source/zh/mindcluster/60rc1/description/productform/昇腾产品形态说明.pdf)：Host CPU 与昇腾 Device 通过 PCIe 连接的异构形态；不描述 PCIe 代际、带宽或特定板卡规格。
- [Ascend C 异构系统](https://asc.gitcode.com/guide/programming_guide/programming_model/heterogeneous_system.html)：Host／Device 的职责、独立内存空间、数据复制与 Kernel 下发。查阅日期 2026-11-15，页面标示 master、提交 `b31f8bdaed16`、构建于 2026-11-12 且包含未提交修改；这是开发预览资料，不当作稳定 CANN 版本声明。

单图生成：`.local/figures-venv/Scripts/python.exe docs/assets/figures/render.py 01-fig1-cpu-npu-dataflow`。

本次渲染环境：Python 3.15.2、Matplotlib 3.11.2；实际字体为华文中宋 1.02、微软雅黑 6.31、Cascadia Code 2407.024，版本读取自字体元数据。字体使用与嵌入遵循各自所附产品条款和字体许可；未将字体文件收入仓库，也未另行授予字体许可。跨环境字体版本变化可能改变字宽，需重新目视检查。旧孪生调试参考图片在本轮整理前已从工作区删除，本轮未恢复；其来源与许可仍待核对。

当前三张正文插图统一使用 1920×1080 像素画布与 42／32 px 标题、18–34 px 分层正文标注及 18 px 水印重新生成 PNG／SVG；所有单图脚本直接使用输出像素坐标，尺寸与字号以 `src/theme.py` 为准。该规则适用于正文插图，品牌横幅使用独立的 [VI 规范](../brand/VI-Specification.md)。

## 第 02 篇

图 1—4、8—10 按正文算例重绘；图 7、11 使用正文的假设带宽与计算屋顶。图 5 的 A100 对照只画 SM 内的计算资源，图 6 只画昇腾 2201 的主要数据路径。架构来源、逐图职责与生成入口见[第 02 篇插图规划](plans/02-hardware-dataflow.md)。图 12 待已归档真机结果完成分析与图表数据整理。绘图入口沿用上面的命名规则；本次导出的英文标签使用 Consolas。
