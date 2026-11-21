# 主题二

**相同的源代码为何能以两种完全不同的机制在 WSL 中执行**？

实验基于原始代码，在 WSL 上运行。**验证两种模式的真实差异**。比较：二进制产物、 gdb 调试追踪、引入错误观察。



# 无卡 WSL 中的 CPU 调试与 SIM 仿真

两种模式都由主机 CPU 提供算力，差别在于 **Kernel 被编成什么，以及谁来解释它的执行语义**。CPU 模式将 Kernel 编成 CPU 域代码，CPU 调测库适配 Ascend C 接口并对部分 ACL 调用打桩。SIM 模式保留面向目标 NPU 的设备编译路径，由运行在主机 CPU 上的 NPU 模型执行设备程序。NPU 模式则由物理设备执行设备代码。

| 模式 | 应观察的对象 | 适用问题 |
| --- | --- | --- |
| CPU | Host 与 CPU 域 Kernel、调测库、可见的 Block 调测进程 | 核函数逻辑、中间数据、功能或数值回归 |
| SIM | Host、设备程序、目标仿真模型及其日志 | 目标架构下的功能与模型支持的执行行为。指令和流水需另用相应仿真采集工具验证 |
| NPU | Host、设备程序、真机运行时与目标设备 | 真机功能和正确性，及独立设计的性能测量 |

依据：[Ascend C CPU 域调试](https://asc.gitcode.com/guide/programming_guide/debug_and_tuning/functional_debug/cpu_twin_debug.html)、[Ascend C 孪生调试](https://www.hiascend.com/zh/developer/techArticles/20231215-2)、[MindStudio 仿真 profiling](https://www.hiascend.com/doc_center/source/en/mindstudio/830/optools/Operatordevelopmenttools/atlasopdev_16_00851.html)。

## 已有记录

2026-11-15 在 WSL2、Ubuntu 24.04.3、x86-64、CANN 9.1.0、目标 `dav-2201` 的条件下做过功能对照。历史报告可从仓库根目录用下列命令查阅。

```text
git show 5396906:lab/hello_world/reports/wsl-report.md
git show 5396906:lab/hello_world/reports/npu-report.md
```

- `Lab01-CPU` 打印了全部 8 个 Block，并报告调测子进程成功。第一次检查中，CPU 调测库创建 Stream 的调用成功返回，句柄仍为空。按句柄判断会跳过销毁调用，改为按创建状态判断后，七项 ACL 检查全部齐全。
- `Lab01-SIM` 加载了 `dav_2201` 模型，8 个 Block 都有打印，模型报告正常停止。模型报告的运行时间、tick 和串行运行提示描述此次仿真过程。
- `Lab01-NEG` 在同一个无卡 WSL 中构建 NPU 模式成功，直接运行时在 `aclInit` 报错并以非零状态退出。云端 `Lab01-NPU` 则在 aarch64、CANN 9.1.0 容器环境中用同一目标配置完成 8 个 Block 的打印与 ACL 状态检查。

## 待验证

在同一 WSL 环境比较三个构建的真实编译命令、动态依赖和执行日志。第一轮优先确认模式选项改变了哪些库和目标，先用已有的无卡 NPU 运行作为失败对照。需要追踪 CPU Kernel 入口时，再带调试信息构建并处理 GDB 的子进程跟随。SIM 中的 Host 断点可观察提交与等待，模型内的执行需要模型日志或专用追踪工具。

本样例的判据是每个 Block 的打印各出现一次，以及对应模式的 Host、模型或设备执行正常结束。数值正确性需要有输入与参考输出的样例，设备性能需要在目标设备上测量。
