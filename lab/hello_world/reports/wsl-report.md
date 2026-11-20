---
experiment_date: "2026-11-15"
experiment_ids:
  - Lab01-CPU
  - Lab01-SIM
  - Lab01-NEG
summary: "WSL 中 CPU 与 SIM 均完成八个 Block 打印和 ACL 状态检查；无设备时的 NPU 模式报告初始化错误并以非零退出码结束。"
---

> 目录迁移说明：报告中的执行命令、历史路径和源码指纹按实际运行时记录保留。当前复现入口见[实验主题页](../README.md)；本次整理未重新运行实验或改写原始结果。

# WSL：CPU、SIM 与失败退出验证

证据类别：已执行功能测试；未测张量精度和性能。

# 环境与实现

| 字段 | 实际值 |
| --- | --- |
| 操作系统 | WSL2，Ubuntu 24.04.3 LTS，x86_64 |
| 物理 NPU | 本地无 NPU，未见 `/dev/davinci*` |
| Toolkit / ops | 安装信息均为 9.1.0；本地安装包为 Toolkit 9.1.0 与 910B ops 9.1.0 |
| CANN 路径 | `/home/lambertt/Ascend/cann-9.1.0` |
| CMake | 3.28.3 |
| 编译目标 | `dav-2201`，CPU 与 SIM 分别构建 |
| SIM 模型 | CMake 明确启用 `tools/simulator/dav_2201/lib`；实际加载 `x86_64-linux/simulator/dav_2201/lib/config_stars.json` |
| 源码 | 本仓库 `src/hello_world/hello_world.cpp`，已加入七项 ACL 返回码及资源清理检查；`LANGUAGE ASC` 编译；启动 8 个 Block |

实际编译器输出：

```text
2026-07-30T20:53:21+08:00 clang version 15.0.5 (clang-5c68a1cb1231 flang-5c68a1cb1231)
Target: x86_64-unknown-linux-gnu
Thread model: posix
InstalledDir: /home/lambertt/Ascend/cann-9.1.0/bin
```

本次读取安装信息，Toolkit 与 ops 的 `version` 均为 `9.1.0`、`arch` 均为 `x86_64`。两个已有安装包的 `--check` 均报告完整性检查通过。本次没有重新安装工具链。

# Lab01-CPU

**CPU 调试能否在无 NPU 的本地执行**

**解决的问题与预期：** 在 CPU 调测模式下运行同一个 Kernel，预期 Block 0—7 各打印一次，Host 的七项 ACL 检查通过，进程退出码为 0。

**过程：** 从 Windows 工作区挂载路径读取当前源码，按 CPU 模式单独配置、编译，再执行验证脚本。

```bash
bash lab/hello-world/verify.sh cpu
```

配置与编译成功，目标为 `demo`。本次原始会话保存在 WSL `/tmp/hello-world-cpu.4wSiWm`。下面保留全部 Block 与 Host 输出，省略 CPU 调测库的文件位置提示和子进程 PID 行，顺序未调整：

```text
[HOST][OK] aclInit: ret=0
[HOST][OK] aclrtSetDevice: ret=0
[HOST][OK] aclrtCreateStream: ret=0
[Block (1/8)]: Hello World!!!
[Block (0/8)]: Hello World!!!
[Block (3/8)]: Hello World!!!
[Block (7/8)]: Hello World!!!
[Block (2/8)]: Hello World!!!
[Block (5/8)]: Hello World!!!
[Block (4/8)]: Hello World!!!
[Block (6/8)]: Hello World!!!
[HOST] Kernel launch call returned; waiting for Stream completion.
[HOST][OK] aclrtSynchronizeStream: ret=0
[HOST][OK] aclrtDestroyStream: ret=0
[HOST][OK] aclrtResetDevice: ret=0
[HOST][OK] aclFinalize: ret=0
process_exit=0
block_counts={0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1}
missing_acl_stages=[]
verification=PASS
```

**结果与预期：** 符合。原始输出还包含 CORE_0—CORE_7 的调测子进程成功消息。

**证明了什么：** 这份代码的核函数入口、Block 编号和打印能在 CPU 调测路径执行。ACL 初始化、设备选择和 Stream 接口在此模式下由调测库适配／打桩，不能证明访问过实际 NPU，也不能据此判断 NPU 吞吐。

**过程中解决的问题：** 首次检查发现创建 Stream 返回成功，但句柄仍为空，导致按指针判断的清理分支没有调用 `aclrtDestroyStream`。脚本因缺少该阶段判为 FAIL，未将退出码 0 视为通过。源码改为记录“创建成功”状态后，得到上方最终 PASS。这是本轮真实发现并修正的 CPU 调测兼容问题。

# Lab01-SIM

**SIM 能否完成目标模型执行**

**解决的问题与预期：** 同一份源码改按 SIM 模式编译，预期目标模型启动，Block 0—7 各打印一次，模型报告正常停止，七项 ACL 状态为 0，进程退出码为 0。

**过程：** 使用独立构建目录执行：

```bash
bash lab/hello-world/verify.sh sim
```

配置输出明确启用 `dav_2201` 模型，编译成功。原始会话保存在 WSL `/tmp/hello-world-sim.9VyffN`。以下省略模型逐核初始化、驱动打桩日志与模型结束时刻，保留完整 Block、Host 和模型结束结果，顺序未调整：

```text
[HOST][OK] aclInit: ret=0
[TmSim]: Run in serial mode.
[HOST][OK] aclrtSetDevice: ret=0
[HOST][OK] aclrtCreateStream: ret=0
[HOST] Kernel launch call returned; waiting for Stream completion.
[AIV Block 0/8] [AIV Block 1/8] [AIV Block 2/8] [AIV Block 3/8] [AIV Block 4/8] [AIV Block 5/8] [AIV Block 6/8] [AIV Block 7/8] [HOST][OK] aclrtSynchronizeStream: ret=0
[HOST][OK] aclrtDestroyStream: ret=0
[Block (0/8)]: Hello World!!!
[Block (1/8)]: Hello World!!!
[Block (2/8)]: Hello World!!!
[Block (3/8)]: Hello World!!!
[Block (4/8)]: Hello World!!!
[Block (5/8)]: Hello World!!!
[Block (6/8)]: Hello World!!!
[Block (7/8)]: Hello World!!!
Model RUN TIME: 1365.08 ms
[INFO] Total tick: 12756
[INFO] Model stopped successfully.
[HOST][OK] aclrtResetDevice: ret=0
[HOST][OK] aclFinalize: ret=0
process_exit=0
model_stopped=True
block_counts={0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1}
missing_acl_stages=[]
verification=PASS
```

**结果与预期：** 符合。模型结束消息直接来自本次输出，最终脚本也把这条消息纳入 SIM 的通过条件。

**证明了什么：** 目标模型执行到了八个逻辑任务的打印位置，Host 调用和仿真结束均通过检查。`1365.08 ms` 是模型报告的运行时间，`12756` 是模型 tick 观察；本次未建立它们与实际设备 Kernel 延时的换算关系，不作为性能数据。`serial mode` 也不能用于推断真机调度。

**日志前缀核对：** 本例源码的格式字符串只有 `[Block (...)]`。已安装 9.1.0 的 `asc_aicore_printf_impl.h` 第210行使用 `scalar_printf_impl` 生成 `[AIV Block %u/%u]`，因此前缀属于工具链的调测输出。上方 SIM 输出显示前缀和正文可分批出现，不能强行按同一行拼成真实输出。

# Lab01-NEG

**无设备时，失败是否反映为非零退出**

**解决的问题与预期：** 为真实 NPU 构建程序后，在没有物理 NPU 的 WSL 中运行，检查失败能否被新代码暴露。预期有 ACL 错误、无 Kernel 打印、进程非零退出，不要求预先指定错误码。

**过程：** 同一份源码使用 `CMAKE_ASC_RUN_MODE=npu` 和 `CMAKE_ASC_ARCHITECTURES=dav-2201` 在独立临时目录构建，再用 `timeout 30s` 执行 `demo`。构建成功，运行现场为 `/tmp/hello-world-no-device.mSRdtN`。

```text
[HOST][ERROR] aclInit: ret=500000
process_exit=1
negative_case=PASS
```

**结果与预期：** 符合，无 Hello World 打印，未超时。这里的 PASS 指失败对照符合预期，不是 NPU 功能成功。

**证明了什么：** 程序检测到了这次初始化失败并以退出码 1 结束，修正了无条件返回 0 的问题。该结果不能证明“无设备”是错误码 500000 的唯一原因；本次没有进一步拆分驱动与初始化失败的具体成因。
