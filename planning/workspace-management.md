# 工作区管理说明

所属专栏：《AI Kernel 101：从 Hello World 到 Flash Attention 的 Ascend C 实践》。目录保留，品牌、审核、证据和发布规则以本轮规范为准。

> 整理日期：2026-11-06。首次整理仅调整本地结构；随后按作者要求合并原代码仓库并接续 GitHub 历史。当前状态见文末“代码仓库合并”，不将文件整理视为新的技术验证。

# 目录分工

```text
ai-kernel-101/
├── 00-写作入口.md            # 本地写作导航，通过 Obsidian 多端同步，不纳入 Git
├── docs/                     # 文章
│   ├── drafts/               # 草稿
│   ├── articles/             # 定稿，由草稿移动而来
│   └── assets/images/        # 文稿配图的统一存放位置
├── planning/                 # 内部策划，可随项目管理
│   ├── series-plan.md        # 系列计划
│   ├── outlines/             # 提纲与论证
│   └── inbox/                # 本地创意、随笔与临时想法，不纳入 Git
├── src/                      # 六组样例的实现、CMake 与代码说明
├── lab/                      # 实验设计、复现方法、运行记录与数据
├── publishing/               # 各平台版本、链接与同步状态
├── .obsidian/                # 本地编辑器配置
├── sites/                    # 既有独立网站项目，默认不提交
└── .local/                   # 本地专用材料，默认不提交
    ├── scripts/              # 本地检查工具
    └── maintenance/          # 维护记录与配置备份
```

lab 内按主题组织，每个主题的 README 说明复现方法，runs 归档每次实际运行；不再把方法与结果分到两个顶层目录。详细组织见 [lab 说明](../lab/README.md)。

# 本次迁移

| 原路径 | 新路径 |
| --- | --- |
| 根目录 Hello World 草稿 | docs/drafts/hello-world.md |
| 根目录 Vector Add 草稿 | docs/drafts/vector-add.md |
| 根目录尾块与对齐草稿 | docs/drafts/vector-add-tail.md |
| 系列写作框架与计划.md | [series-plan.md](series-plan.md) |
| 提纲中的两份文件 | planning/outlines，保留原文件名 |
| 早期选题思路 | `planning/inbox/早期选题思路.md`，仅本地保留 |
| 五张既有配图 | docs/assets/images，保留原文件名 |
| 00_阶段性思考中的两篇职业笔记 | .local/personal-notes，保留原文件名 |
| AGENTS.md.md | 根目录 AGENTS.md，修正重复扩展名 |

共迁移 15 个文件。移动后首先逐文件比对 SHA-256，随后只修正文档路径、维护约定与相关引用。原始路径、新路径和移动前哈希记录保存在本地 `.local/maintenance/file-migration-2026-11-06.json`。恢复旧位置时需同时处理后续链接变化，不直接覆盖已经修改的文件。

本次不重写三篇正文，不把旧操作段落自动拆成实验工程，不把草稿改称已发表文章。旧编号仍待编辑整理；新系列编号由 [文章目录](../docs/README.md)统一管理。

# 现有独立项目与编辑器

sites/kernel-lab 包含独立的 Git 目录与网站文件，sites 中另有压缩包；本次保留原位、不更改该项目内容，根目录 Git 忽略整个 sites。

.obsidian 配置和插件留在原位。仅同步 workspace.json 中与本次迁移对应的文件路径，避免打开旧位置；不读取或修改插件账户配置。.openai、.agents 同样保留原位并从默认 Git 提交范围排除。

# 发布边界

本次 .gitignore 只影响未来 Git 跟踪规则，不影响 Obsidian 或其他同步软件的行为，也不能撤回已在其他仓库或平台公开的文件。未来若复用已有仓库，需要另行核对其已跟踪文件。

正文、代码、复现说明与实验结果分别维护，使用相对链接和提交建立对应关系。首次结构整理没有初始化 Git；后续合并在作者明确授权下接续原项目历史并提交推送。GitHub 仓库更新不代表已经发布知乎文章。

# Obsidian 多端写作补充

项目根目录继续作为唯一 Obsidian 库。本地的 `00-写作入口.md` 继续指向唯一正文，只通过 Obsidian 进行多端同步，不纳入 Git，也不作为公开页面的链接目标。planning/inbox 统一接收中途创意、随笔与临时笔记；早期选题思路也在此处。inbox 默认仅本地保存并停止 Git 跟踪，不删除笔记，不改 Obsidian 默认位置，不在公开文档中链接忽略文件。已有公开历史不会因此消失，不重写历史、不强制推送。

当前本地 app.json 统一新笔记、附件和相对链接设置，修改前备份保存在 .local/maintenance。插件、账户、远程同步范围未修改。手机是否接收应用设置，需要根据实际同步方式确认；详情见 [Obsidian 写作说明](obsidian-writing.md)。

# 代码仓库合并

从原本地代码仓库的最新工作副本导入六组样例：Hello World，以及 Vector Add 的 basic、Host/Device transfer、TPipe/TQue、uneven split、arbitrary length。共 18 个实现、构建与说明文件逐一核对 SHA-256，包含原仓库未提交的 .asc→.cpp 改名；原本地目录及其未提交修改保持不动。

工作区接续 GitHub 原 main 历史，保留源码路径。旧文章路径用短入口页链接到唯一正文；所有文稿配图统一存放在 docs/assets/images，正文与 Obsidian 新附件都使用这一位置，不再维护重复图片目录。

原 README 的样例导航、来源与许可、历史 CPU 验证信息分别合入根 README、src 索引与 lab 历史记录。账号设置、个人笔记、已有独立网站项目及生成物继续遵循忽略规则；它们保留在本地，没有进入本次项目提交。

本次不重新验证 Kernel，不把历史记录改写成新实验。合并前快照、源文件哈希和原工作副本差异保存在 .local/integration，避免覆盖或丢弃原工作。

# 本轮规范重构

仅新增文章提示、配图规范、发布与复盘模板三份文件；公开介绍、系列计划、审核、实验和平台规则在现有文件上更新。三篇草稿只调整定位前言、标题元数据与导航，02／08提纲保留推理主体，08—10技术范围不重新设计。源码、CMake、历史记录及五张图片均不改变。

许可证暂不选择，来源与公开素材缺项在 src 和 assets 说明中登记。普通草稿可公开；私人笔记、账号及敏感运营资料只留本地。此轮未授权提交或推送远程，阶段完成状态不等于 GitHub 或社交平台已经更新。
