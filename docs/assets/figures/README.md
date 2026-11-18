# 文档插图规范与生成流程

本目录统一维护草稿与定稿的插图：plans 保存逐篇规划，src 保存绘图代码，gen 保存同名 PNG／SVG。正文定稿时共用同一套材料；实验设计、原始数据和结果分析保留在 lab。本目录保存自绘与外部参考插图；环境、平台及运行结果截图归入 [screenshot](../screenshot/README.md)，品牌横幅与标识归入 [brand](../brand/README.md)。

# 逐篇插图规划

| 篇次 | 规划入口 | 当前范围 |
| --- | --- | --- |
| 01 | [Hello World](plans/01-hello-world.md) | 三张执行关系概念图，含生成入口、来源与历史记录 |
| 02 | [硬件数据流](plans/02-hardware-dataflow.md) | 当前正文图 1—7，架构来源与图注待核对项 |
| 04 | [Tiling](plans/04-tiling.md) | 接收原 02 图 8，作为容量说明候选素材 |
| 09 | [Matmul](plans/09-matmul.md) | 接收原 02 图 9—10，说明输出块、重读和部分和 |
| 11 | [Roofline](plans/11-roofline.md) | 接收原 02 图 11 与尚未生成的图 12 设计 |

只为已有具体图示设计建立规划，不按 16 篇目录预建空文件。每篇的图号、正文位置、画法、来源、证据边界和生成记录放入 plans，本页只维护共用规范与流程。

# 主要规范

| 项目 | 统一要求 |
| --- | --- |
| 输出 | 1920×1080 px，白底、非透明；PNG／SVG 共用布局，不自动紧裁 |
| 标题 | 中文在上 42 px、英文在下 32 px |
| 正文标注 | 18–34 px 的整数层级，默认 28 px；双语标注中文在上、英文在下，同组字号相同，框内整体居中 |
| 字体 | 中文标题用华文中宋，中文标注用微软雅黑，英文与数字默认 Cascadia Code |
| 配色 | 天蓝 #00B0F0 表示主要流程、数据与执行对象；红色 #C00000 标示约束、依赖、等待或重点；其他文字与结构用黑白灰，颜色不独立承担语义 |
| 水印 | 上下居中、18 px、#CFD3D7，文案由 theme.py 的 WATERMARK 统一维护 |
| 坐标与字号 | 直接使用输出像素坐标，DPI=100；传给 Matplotlib 时按 px × 72 / DPI 换算为 pt |
| 命名与引用 | 按正文出现顺序从 fig1 编号，脚本名为“篇次-fig序号-英文主题.py”；正文引用 gen 中的 PNG，图片下放可见图注 |

用图形、任务条和箭头解释关系，长说明留在正文或图注。概念示意、模型预测和实测结果明确区分；图注保留适用架构、单位、输入、模式与必要限制，不用图形暗示未经验证的核数、时序或性能。

GM／HBM、UB／L1／L0、Vector／Cube 分别明确标名，不能因同色视为同一资源。搬运箭头标明方向，同步与等待用文字或线型区分；模型曲线用虚线并标“预测”，实测用点／实线并标模式、统计量与波动。灰度下仍应可辨，不从截图配色反推硬件语义。

共用布局与样式集中在 [src/theme.py](src/theme.py)。单图复用 canvas、bilingual、bilingual_in_box、box、arrow、save，使用整数 size 设置标注层级；具体 API 以源码为准。

# 生成流程

1. 在 plans 明确图示要回答的问题、正文位置、证据和来源边界，再确定图号与脚本。
2. 在 src 编写或修改绘图代码，使用固定依赖与明确字体，不以图片生成结果替代实验数据。
3. 重新生成 PNG／SVG，逐张检查文字、图形和技术语义，更新规划中的文件入口与状态。
4. 核对正文引用、图注和手机预览。代码只检查文字是否超出画布，不能替代遮挡检查、技术审核和来源审核。平台适配可另做分页图卡，不能为缩小版面删去关键单位、证据和限制，也不把内部导出尺寸当作平台上传要求。

在仓库根目录准备 Python 环境并安装[固定依赖](requirements.txt)：

```powershell
python -m venv .local/figures-venv
.local/figures-venv/Scripts/python.exe -m pip install -r docs/assets/figures/requirements.txt
```

使用[批量入口](render.py)生成全部图，或传入脚本名选择单图：

```powershell
.local/figures-venv/Scripts/python.exe docs/assets/figures/render.py
.local/figures-venv/Scripts/python.exe docs/assets/figures/render.py 01-fig2-host-kernel
```

Linux／WSL 将解释器路径换为 .local/figures-venv/bin/python。生成入口从 src 发现编号脚本，辅助模块不单独生成图片；运行后覆盖 gen 中的同名文件。

# 字体与来源

| 字体角色 | 指定字体文件的环境变量 |
| --- | --- |
| 中文标题 | FIGURE_TITLE_CHINESE_FONT |
| 中文标注 | FIGURE_CHINESE_FONT |
| 英文与数字 | FIGURE_ENGLISH_FONT |

字体缺失时明确报错，不自动替换。Cascadia Code 可从本地 .local/figure-fonts/CascadiaCode-Regular.ttf 加载，固定来源为[微软 v2407.24](https://github.com/microsoft/cascadia-code/releases/tag/v2407.24)。仅使用有权使用的字体，字体文件留在本地；SVG 将文字导出为路径，修改文字需回到源码。

每篇规划保留作者／上游、原始链接与固定版本、适用授权、改绘内容、原数据或计算过程、生成命令、引用篇章及实际生成环境。源代码、PNG 与 SVG 一并版本管理；绘图不改写 lab 中的原始实验数据。旧图的对照、来源和历史记录随所属篇章归档，不在本页重复维护；保留记录不代表许可或技术审核已经通过。来源不明、未授权或含私人信息的素材先留本地，不进入公开图包；不自行选择许可证或扩大上游授权。
