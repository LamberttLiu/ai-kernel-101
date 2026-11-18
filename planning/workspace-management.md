# 工作区管理说明

本文维护当前目录结构与分工，项目入口见 [README](../README.md)。

# 目录结构

```text
ai-kernel-101/
├── README.md                    # 系列介绍与阅读入口
├── CONTRIBUTING.md              # 内容维护与协作约定
├── docs/
│   ├── README.md                # 文章目录、状态与撰写流程
│   ├── ARTICLE_TEMPLATE.md      # 写作与审核提示
│   ├── drafts/                  # 写作中的正文
│   ├── articles/                # 定稿正文
│   └── assets/
│       ├── figures/             # 文档插图与绘图材料
│       ├── screenshot/          # 环境与实验截图
│       └── brand/               # 品牌素材
├── planning/
│   ├── series-plan.md           # 系列计划与技术依赖
│   ├── workspace-management.md  # 工作区结构与分工
│   ├── obsidian-writing.md      # 多端写作说明
│   ├── outlines/                # 提纲与论证
│   └── inbox/                   # 本地创意、随笔与临时选题
├── lab/                         # 唯一实验工程工作区，按主题组织
│   ├── README.md                # 主题与实验编号索引、组织规则
│   ├── SOURCES.md               # 实现入口、来源与许可待核对项
│   ├── hello-world/             # 源码、验证脚本与 CPU/SIM/NPU 报告
│   ├── hardware-dataflow/       # 实验设计、源码、脚本、结果与报告
│   ├── vector-add/              # 向量加与 Host/Device 传输练习
│   └── flash-attention-fixed/   # 固定 shape 的前向实现与复现说明
├── publishing/                  # 平台适配、发布记录与勘误
├── 00-写作入口.md               # 本地写作导航
├── AGENTS.md                    # 本地 Agent 协作约定
├── .obsidian/                   # 本地 Obsidian 配置
├── .agents/                     # 本地 Agent 配置与技能
├── .vscode/                     # 本地编辑器配置
├── sites/                       # 独立网站项目
└── .local/                      # 本地工具、配置备份与私人材料
```

# 内容放置与维护

- **文章**：`docs/drafts` 保存唯一写作正文，定稿后移入 `docs/articles`。状态与文章目录、首页目录同步，具体缺项写入 `to_do_list`；八阶段流程见 [文章目录](../docs/README.md#统一撰写流程)。
- **规划**：[系列计划](series-plan.md) 保存技术依赖与逐篇论证，提纲放入 `planning/outlines`，临时想法放入 `planning/inbox`。
- **代码与实验**：[lab](../lab/README.md) 是唯一的实验工程工作区。每个主题按需要包含 README、experiment-plan、src、scripts、results、reports；源码与构建入口、设计、数据和分析在同一主题中维护，不创建空文件占位。实验编号与路径解耦，已有编号保持稳定；明确形成复用需求后才建立 lab/common。来源与许可线索见 [实现来源说明](../lab/SOURCES.md)。正文解释知识并引用实验依据，不另存一套实验结果。
- **配图**：按用途归入 `figures`、`screenshot`、`brand`，编号、生成与来源规则见 [配图约定](../docs/assets/README.md)。
- **发布**：平台适配、真实链接、版本与勘误见 [发布管理](../publishing/README.md)；文章定稿与平台发布分别记录。

# 本地与公开边界

项目根目录作为同一 Obsidian 库，手机与桌面编辑同一正文。新笔记进入 `planning/inbox`，新附件默认进入 `docs/assets/screenshot`，操作说明见 [多端写作说明](obsidian-writing.md)。

本地配置、`planning/inbox`、`.local`、独立 `sites` 项目及构建和大型原始输出按 `.gitignore` 管理。账号、认证材料与敏感私人材料仅留本地；公开文档不依赖被忽略的文件。一般草稿是否公开由作者决定。Git 忽略规则不改变同步服务的设置。
