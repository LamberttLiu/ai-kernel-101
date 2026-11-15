---
experiment_date: "2026-11-15"
summary: "云端容器中 NPU 模式完成八个 Block 打印，七项 ACL 检查成功并正常退出；宿主机与固件信息受平台可见性限制。"
---

# 云端 NPU：真实设备启动与打印验证

证据类别：已执行真机功能测试；未测张量精度和性能。

# 解决的问题与预期

本地 CPU/SIM 可以执行，不代表实际设备上的运行路径已经通过。本实验将同一份源码在远端 `/mnt/workspace/ai-kernel-101` 重新编译，预期物理 NPU 执行 8 个 Block，Block 0—7 各打印一次，七项 ACL 返回码为 0，进程退出码为 0。

# 环境：分别记录查询结果

实验运行于线上云主机提供的容器。平台未开放宿主机、固件等信息，以下操作系统、架构与软件字段均为容器内查询结果，不代表已核实宿主机配置。这是本实验固定的环境可见性边界，不列作待补任务。

| 字段 | 实际查询结果／来源 |
| --- | --- |
| 容器环境 | 用户态系统 Ubuntu 20.04.5 LTS，`uname -m` 返回 aarch64；宿主机操作系统与硬件配置不可获取 |
| 工程路径 | `/mnt/workspace/ai-kernel-101` |
| NPU 工具显示名 | `npu-smi info` 显示 `Ascend910`，健康状态 OK |
| 可见物理设备 | NPU ID 5，Chip 0、1；程序使用逻辑 Device 0，不据此等同物理 NPU ID 0 |
| 板卡查询 | `npu-smi info -t board -i 5 -c 1`：NPU Name `9362`，Chip Name `Ascend910`，Chip Version `V1`，Board ID `0xb3` |
| Runtime SoC | `aclrtGetSocName()` 返回 `Ascend910_9362`；查询前的 `aclInit`、`aclrtSetDevice(0)` 均返回 0，查询后的重置和结束也返回 0 |
| 完整商用产品系列 | 仅记录容器可见的设备标识，不从这些标识反推 A3、910C、910B 等宿主机产品配置 |
| 容器可见驱动信息 | `/usr/local/Ascend/driver/version.info`：`Version=25.5.5`，`package_version=25.5.5`，`ascendhal_version=7.35.23` |
| npu-smi | 25.5.5，独立于 CANN 版本记录 |
| 固件 | **平台未开放查询**。`npu-smi ... -t board` 返回 `Firmware Version: NA`；容器内 `/usr/local/Ascend/firmware/version.info` 和 `ascend_install.info` 均不可读取或不存在，不推断宿主机固件版本 |
| Toolkit / ops | 两份安装信息均为 9.1.0、aarch64；CANN 路径 `/home/developer/Ascend/cann-9.1.0` |
| CMake | 3.20.5 |
| 编译配置 | `CMAKE_ASC_RUN_MODE=npu`，`CMAKE_ASC_ARCHITECTURES=dav-2201`；不把编译目标名当作商用产品名 |

实际编译器输出：

```text
2026-07-30T20:53:21+08:00 clang version 15.0.5 (clang-5c68a1cb1231 flang-5c68a1cb1231)
Target: aarch64-unknown-linux-gnu
Thread model: posix
InstalledDir: /home/developer/Ascend/cann-9.1.0/bin
```

# 实现与执行过程

先检查远端 `src/hello_world/hello_world.cpp`，确认仍是未检查 ACL 返回码的样例，再同步本轮修改后的同一份源码。远端已有 `lab/hello-world/scripts` 未修改；本次只增加公共验证脚本 `lab/hello-world/verify.sh`。没有执行 Git 拉取、提交、重置或推送。

从远端仓库根目录运行：

```bash
bash lab/hello-world/verify.sh npu
# 只补查环境与 Runtime SoC，不重新编译运行：
HELLO_PROBE_ONLY=1 bash lab/hello-world/verify.sh npu
```

驱动与板卡字段另用以下只读查询取得：

```bash
source "$HOME/Ascend/cann/set_env.sh"
cat /usr/local/Ascend/driver/version.info
npu-smi info -t common -i 5
npu-smi info -t board -i 5 -c 1
```

配置及编译成功，CMake 使用 CANN 9.1.0 的 aarch64 工具链。实际执行二进制为 `/tmp/hello-world-npu.dnysBb/build/demo`，原始会话和运行输出留在同目录上一级。没有回传二进制或整棵构建树。

# 结果

以下保留本次完整运行输出；末尾附脚本记录的进程退出状态和自动核对结果：

```text
[HOST][OK] aclInit: ret=0
[HOST][OK] aclrtSetDevice: ret=0
[HOST][OK] aclrtCreateStream: ret=0
[HOST] Kernel launch call returned; waiting for Stream completion.
[HOST][OK] aclrtSynchronizeStream: ret=0
[HOST][OK] aclrtDestroyStream: ret=0
[AIV Block 6/8] [Block (6/8)]: Hello World!!!
[AIV Block 7/8] [Block (7/8)]: Hello World!!!
[AIV Block 0/8] [Block (0/8)]: Hello World!!!
[AIV Block 1/8] [Block (1/8)]: Hello World!!!
[AIV Block 2/8] [Block (2/8)]: Hello World!!!
[AIV Block 3/8] [Block (3/8)]: Hello World!!!
[AIV Block 4/8] [Block (4/8)]: Hello World!!!
[AIV Block 5/8] [Block (5/8)]: Hello World!!!
[HOST][OK] aclrtResetDevice: ret=0
[HOST][OK] aclFinalize: ret=0
process_exit=0
block_counts={0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1}
missing_acl_stages=[]
verification=PASS
```

# 与预期对照，以及证明了什么

结果符合功能预期：真实设备环境下，按 NPU 模式构建并执行的程序完成了 8 个逻辑 Block 的打印；初始化、设备选择、Stream 创建、同步与清理均返回成功，进程正常结束。环境、实际二进制与输出一起记录，支持本次“真机执行成功”的结论。

打印先后不是调度时间线；部分打印出现在 Host 同步成功消息之后，也不能据此推断 Kernel 尚未完成。这里能观察到的是调测信息在主机端被输出的顺序，没有测量设备执行与打印转发的精确时间关系。

本实验不证明向量加等张量计算正确，不证明高性能，也不证明其他 shape、接口、设备或版本可用。宿主机产品配置与固件不可获取，不影响本次已观察到的启动、同步与完整打印结果，但实验不提供跨宿主机或跨固件版本的兼容性结论。不能用 `Ascend910_9362`、`dav-2201` 或容器可见驱动信息互相补推。
