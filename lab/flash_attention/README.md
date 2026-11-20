# Prefill FlashAttention 实现目标

独立实现一个范围明确、可解释、可验证的 Ascend C Prefill FlashAttention 前向 Kernel，作为系列第 14–16 篇的实验主线。首轮聚焦固定形状的稠密自注意力，采用 FP16 输入、BNSD 布局、单批次单头，先验证无掩码路径。因果掩码留到基础路径通过后单独验证。最终融合路径按 K/V 块更新每个查询行的状态 `m/l/u`（最大值、指数和、未归一化输出累加），最后计算 `u/l`，避免向全局内存（GM）写回完整的分数或概率矩阵。交付边界见[系列规划](../../planning/series-plan.md)。

## 参考选择与理由

- **主参考采用 PromptFlashAttention（PFA）。** 它面向全量推理，与 Prefill 的实验范围直接对应。用设计文档对照在线 Softmax、Cube/Vector 分块、流水和中间数据生命周期，用 `aclnnPromptFlashAttentionV3` 建立官方对照。自研实现聚焦固定形状下的核心数据流，官方工程的多场景分发与专用优化留作源码参考。[算子说明](https://github.com/hicann/ops-transformer/blob/master/attention/prompt_flash_attention/README.md) · [设计文档](https://github.com/hicann/ops-transformer/blob/master/attention/prompt_flash_attention/docs/PFA_design.md) · [arch22 同步源码](https://github.com/hicann/ops-transformer/blob/master/attention/prompt_flash_attention/op_kernel/arch22/prompt_flash_attention_base_api.h)
- **补充参考采用 FusedInferAttentionScoreV4（FIA V4）。** 它覆盖 Prefill 和 Decode，用于研究统一接口、Tiling 分发和跨计算单元同步。公开源码为 Cube/Vector 协同提供实现参考，目标设备上自研代码的 Matmul 输出路径、工作区（Workspace）、同步和接口可用性仍须实测。[FIA 源码目录](https://gitcode.com/cann/ops-transformer/tree/master/attention/fused_infer_attention_score) · [V4 接口文档](https://github.com/hicann/ops-transformer/blob/master/attention/fused_infer_attention_score/docs/aclnnFusedInferAttentionScoreV4.md)

## FA-PoC 验证路线

| 阶段 | 任务与验收 |
| --- | --- |
| P0 官方基线 | 在目标环境跑通 `aclnnPromptFlashAttentionV3` 的 FP16 Prefill，用显式计算的 Attention 参考结果检查误差。 |
| P1 最小跨单元数据流 | 自研 Cube `QKᵀ` → Vector 缩放与 Softmax → Cube `PV`，验证输出正确性、工作区和同步。这一阶段聚焦数据交接。 |
| P2 在线分块 | 加入 K/V 分块循环和在线状态更新，确认至少处理两个 K/V 块、结果满足误差要求，且融合路径不写出完整的分数或概率矩阵。 |

候选输入为 `B=N=1`、`D=64`、`S_Q=S_KV=128` 或 `1024`。短序列用于基础正确性，长序列用于多块验证。以实际切块和更新次数判断是否覆盖多块路径。

第 14 篇验证在线递推，第 15 篇验证最小交接与分块实现，第 16 篇在正确性通过后，对比分离基线与融合实现的中间存储、搬运和耗时，用 PFA V3 补充性能对照。

本文记录技术选型和待验证目标。PFA 算子说明列出了 Atlas A2/A3 支持情况，具体设备、CANN 版本与所选源码分支的对应关系待确认。
