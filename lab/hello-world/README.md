---
experiment_date: "2026-11-15"
summary: "Hello World 的 CPU、SIM、NPU 功能验证通过，无设备失败对照符合预期；仅验证启动、同步与打印，不涉及张量精度和性能。"
reference_checked_on: "2026-11-15"
---

# Hello World 验证

对应[第01篇文章](../../docs/articles/hello-world.md)，源码为 [hello_world.cpp](../../src/hello_world/hello_world.cpp)，构建配置为 [CMakeLists.txt](../../src/hello_world/CMakeLists.txt)。实验覆盖 CPU、SIM 和远端 NPU 功能验证，以及 WSL 无设备时的失败退出。

| 实验 | 解决的问题 | 结果 | 证明范围 |
| --- | --- | --- | --- |
| WSL CPU | 没有 NPU 能否执行核函数逻辑 | 8 个 Block 各打印一次，七项 ACL 状态为 0，退出码 0 | CPU 调测路径的入口和打印可执行 |
| WSL SIM | 设备代码能否通过目标模型执行 | 8 个 Block 各打印一次，模型正常停止，七项 ACL 状态为 0，退出码 0 | `dav_2201` 仿真路径可执行 |
| 云端 NPU | 同一份源码能否在实际 NPU 执行 | 8 个 Block 各打印一次，七项 ACL 状态为 0，退出码 0 | 本次实际设备上的启动、同步与打印成功 |
| WSL NPU 失败对照 | ACL 失败能否被程序暴露 | `aclInit` 返回 500000，退出码 1，无 Kernel 打印 | 程序不再以无条件返回 0 掩盖这次初始化失败 |

以上均为功能验证，没有张量数值计算或真机性能测量。CPU 的 ACL 调测打桩返回成功不代表访问了物理 NPU。

NPU 实验运行于云平台容器，环境按容器可见范围记录。宿主机配置和固件信息未向使用者开放，作为环境边界保留，不再列为待补项；本次真机功能通过的结论保持不变。

# 文件与复现

本目录只保留四个文件：本说明、[WSL 报告](wsl-report.md)、[NPU 报告](npu-report.md)和[验证脚本](verify.sh)。报告保留完整的 8 个 Block 输出、ACL 结果、环境、命令与结论；不回传二进制、构建树、模型大日志、安装包、SHA256 或精确 commit。

在已安装 CANN 的 Linux 环境，从仓库根目录运行：

```bash
bash lab/hello-world/verify.sh cpu
bash lab/hello-world/verify.sh sim
```

远端 `/mnt/workspace/ai-kernel-101` 中运行：

```bash
cd /mnt/workspace/ai-kernel-101
bash lab/hello-world/verify.sh npu
```

脚本依次查找当前用户的 `Ascend/cann/set_env.sh`、`Ascend/ascend-toolkit/set_env.sh` 和系统安装路径。其他位置通过 `CANN_ENV` 指定；编译目标默认 `dav-2201`，可通过 `HELLO_ARCH` 显式指定。脚本将构建、二进制和完整会话留在执行机器的 `/tmp/hello-world-模式.随机后缀`，退出时输出位置；这些是临时现场，不保证长期保留，本地报告已保留支撑结论的必要内容。

三种模式的完整会话另留在仅本地的 `.local/hello-world/cpu-session.txt`、`sim-session.txt` 和 `npu-session.txt`，用于编辑时核对，不作为公开文档链接。验证使用同一份已修正源码，最终脚本对模型结束条件的检查也已通过。

判定条件为：构建成功；Block 0—7 各出现一次；七项 ACL 调用成功且无 `[HOST][ERROR]`；进程退出码为 0。SIM 还必须报告 `Model stopped successfully`。脚本校验失败返回非零值，120 秒超时也不能算成功。

# 源码与资料范围

本轮在源码中加入 ACL 返回码检查和失败后的资源清理。Kernel 内容、Block 数量和 CMake 编译目标没有改变；远端先检查原文件，再同步同一份修改后的源码进行编译。`<<<>>>` 本身没有可直接检查的 ACL 返回值，记录它返回后仍须检查 Stream 同步状态及全部打印。

当前源码与官方 [SIMD Hello World](https://asc.gitcode.com/guide/getting_started/quick_start/simd_programming/hello_world.html) 使用相同的核函数修饰符和启动方式；该页面链接的[完整样例](https://gitcode.com/cann/asc-devkit/blob/master/examples/01_simd_cpp_api/00_introduction/00_quickstart/hello_world/README.md)为上游参考。本文保留 `.cpp` 文件，通过 `LANGUAGE ASC` 指定编译；Host 新增的错误处理是本项目修改。此前 CANN Samples 的来源线索继续保留在[源码目录说明](../../src/README.md)，不把当前在线示例当成原文件的逐字来源证明；许可问题不在本轮实验中自动认定完成。

| 核对项 | 本次依据与适用范围 |
| --- | --- |
| 安装与编译器 | 两端安装信息均为 CANN Toolkit/ops 9.1.0；实际编译器为 clang 15.0.5，完整版本输出见两个报告 |
| 本地安装包 | 已存在 Toolkit 9.1.0 与 910B ops 9.1.0 安装包，两者 `--check` 均报告完整性通过；未重新安装 |
| CPU 调测 | [CPU 域调试说明](https://asc.gitcode.com/guide/programming_guide/debug_and_tuning/functional_debug/cpu_twin_debug.html)说明部分 ACL 接口为打桩实现；本轮实测确认本样例可运行，不推广到所有 ACL API |
| SIMD 修饰符 | [SIMD BuiltIn 说明](https://asc.gitcode.com/guide/programming_guide/language_extension/simd_builtin_keywords.html)解释 `__global__`、`__vector__` 和启动配置；本例实际采用 `dav-2201`，不扩展到 SIMT 或 SIMD VF |
| printf | [printf 说明](https://asc.gitcode.com/api/Utils-API/tuning_interface/printf.html)与已安装 9.1.0 的头文件均覆盖本例的 SIMD 调测用法；本轮三种模式实际验证了打印 |
| AIV 前缀 | 已安装的 `x86_64-linux/asc/impl/utils/debug/asc_aicore_printf_impl.h` 第210行生成 `[AIV Block %u/%u]`；用户核函数只生成后面的 `[Block (...)]`。工具前缀与用户打印在 SIM 中可分批输出 |
| Stream 同步 | [CANN 9.1.X Runtime 同步文档](https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/910/others/acldevg/runtime_doc_dev_0014.html)为版本化资料入口；本轮检查实际 `aclrtSynchronizeStream` 返回值。在线抓取仅返回站点导航，未把它当作新增接口保证 |

`asc.gitcode.com` 页面属于开发中的 master 文档，用于解释机制；本文实际接口可用性以已安装 9.1.0 代码与本轮结果为准，不能据在线产品列表反推当前云端产品型号。
