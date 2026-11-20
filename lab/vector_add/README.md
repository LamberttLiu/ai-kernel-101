---
experiment_date: 未知
summary: 向量加与 Host/Device 传输的五组实现及构建入口；保留各样例既有验证说明，本次目录整理未新增运行证据。
---

# 向量加与 Host/Device 传输

本主题集中保存第 03—05 篇使用的向量加、数据传输与尾块练习。现有五组实现均可独立构建；具体接口、运行命令和已有验证范围见各自说明。

| 实现 | 构建与运行入口 | 用途与边界 |
| --- | --- | --- |
| 基础 Add | [src/00_basic](src/00_basic/README.md) | 静态 Tensor 的搬入、计算、同步与写回 |
| Host/Device 传输 | [src/01_host_device_transfer](src/01_host_device_transfer/README.md) | 页锁定 Host 内存与 Device 内存的传输程序，不含 Ascend C Kernel |
| TPipe/TQue Add | [src/02_tpipe_tque](src/02_tpipe_tque/README.md) | 用队列管理缓冲生命周期；队列深度 1，不是双缓冲 |
| 不均匀分核 | [src/03_uneven_split](src/03_uneven_split/README.md) | 长度对齐但任务分配不均匀的尾核处理 |
| 任意长度尾块 | [src/04_arbitrary_length](src/04_arbitrary_length/README.md) | 非对齐尾块搬运；不代替尚待实现的核内多轮 Tiling |

这些目录承载已有实现与复现说明，历史 CPU、SIM、NPU 的证据范围以各样例和正文中的明确记录为准。目录迁移不补齐未归档的原始证据，也不提升验证状态。现有材料尚未形成新的、具备独立判据的实验设计，因此本次不为五个代码版本直接分配实验编号，不创建空的设计、结果或报告文件。

完整实验编号与维护规则见 [Lab 工作区](../README.md)。
