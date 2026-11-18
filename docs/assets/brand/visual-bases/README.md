# AI Kernel 101 · 数字粒子视觉素材

基于横幅母图的代码文字排版结果单独存放于 [digital-banner](../digital-banner/README.md)。本目录继续保留未经改动的纯基底和竖幅原图。

GitHub 版微调现采用 [v2 安全留白母图](ai-kernel-101-digital-banner-base-master-v2.png) 与 [1600 × 600 纯基底](ai-kernel-101-digital-banner-base-1600x600-v2.png)。粒子安全边距由图像工具在基底层调整，保存为独立 v2，不覆盖 v1；标题与其他文字仍由代码单独生成。编辑提示词见 [digital-banner-base-v2.prompt.txt](digital-banner-base-v2.prompt.txt)。

作者确认保留横幅纯基底与竖幅海报两种构图，供后续设计使用。此前的 Kernel Core、Compute Matrix、Dataflow 候选及对应预览、提示词已清理，不再作为后续方案。

## 保留的素材

| 文件 | 尺寸 | 用途 |
| --- | --- | --- |
| [横幅纯基底](ai-kernel-101-digital-banner-base-1600x600-v1.png) | 1600 × 600，8:3 | 大号 101、二进制粒子、冷白蓝光，左侧黑色留白。没有标题、定位语、标语或水印，供后续代码排版。 |
| [横幅高清母图](ai-kernel-101-digital-banner-base-master-v1.png) | 2048 × 768，8:3 | 横幅生成原图，固定保存。1600 × 600 版由它等比缩小，不拉伸、不裁切数字。 |
| [竖幅海报](ai-kernel-101-digital-poster-v1.png) | 1086 × 1448，3:4 | 保留完整 AI Kernel 101 标题、定位语、技术关键词、英文标语与作者水印。 |

横幅 v2 已由作者确认作为 GitHub 品牌横幅的固定基底，竖幅继续保留为已认可的风格素材。其他平台适配尚未完成，不从本记录自动推断发布状态。

## 生成记录

使用内置 `image_gen.imagegen` 工具生成，日期为 2026-11-18；工具未提供具体模型版本。竖幅根据作者提供的 GLM-5 数字粒子海报截图作风格参考，未保留原品牌标识、原文案或截图界面。横幅以竖幅的粒子 101 为参考，重新构图并去除排版文字。

- [竖幅生成提示词](ai-kernel-101-digital-poster-v1.prompt.txt)
- [横幅生成提示词与导出说明](digital-banner-base-v1.prompt.txt)
- [原图尺寸、导出方式与 SHA-256](assets.json)

横幅主文件通过 Pillow 13.0.0 的 LANCZOS 等比缩小为 1600 × 600，并嵌入 sRGB ICC。生成母图与竖幅原图保持原样。AI 再次生成不保证像素一致，后续排版应引用保存的素材，不反复生成基底。

`previews/` 保存横幅的 320 px、160 px 等比缩略图，供辨识度检查，不是额外平台模板。此前其他方向的候选已按作者要求删除；项目首页现在直接引用 `digital-banner` 中的 v2 文字合成版。旧网格横幅目录与旧颜色 Token 已清理。本次没有提交、推送或发布，也没有修改项目许可证。
