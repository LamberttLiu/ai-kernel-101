# Vector Add：TPipe 与 TQueue

这一版以 [CANN Samples 的 `add_tpipe_tque.asc`](https://gitcode.com/cann/cann-samples/blob/master/Samples/0_Introduction/01_simd_cpp_api/01_add/add_tpipe_tque/add_tpipe_tque.asc) 为样例，来源提交为 `1e8cbde3cebea3e9e4a90c28c00dc6de99614c9a`。Kernel 保留上游的 TPipe/TQue 实现及版权声明；Host 侧改为与本仓库其他 Add 练习相同的自生成输入和结果比较，因此不需要上游的 `data_utils.h` 或数据脚本。构建配置取自同一上游样例。

本目录使用 **CANN 9.1.0**，目标架构为 `dav-2201`。源码在 [`add_tpipe_tque.cpp`](./add_tpipe_tque.cpp)，构建文件在 [`CMakeLists.txt`](./CMakeLists.txt)。运算仍是逐元素加法 `z[i] = x[i] + y[i]`：16,384 个 `float` 元素分给 8 个 Block，每个 Block 处理 2,048 个元素。

## 为什么引入队列

[00_basic](../00_basic/README.md) 直接用 `LocalMemAllocator` 分配 UB 空间，并在搬入、计算、搬出之间插入 `PipeBarrier`。本例把三个阶段所需的 LocalTensor 放到队列中，由 `TPipe` 初始化缓冲区、`TQue` 管理张量的分配、交接和释放。

| 阶段 | 本例中的操作 | 张量去向 |
| --- | --- | --- |
| 分核 | `GetBlockNum()` 与 `GetBlockIdx()` 确定每个 Block 的 GM 区间 | 每核负责互不重叠的 2,048 个元素 |
| 初始化 | `pipe.InitBuffer(...)` 为两个 `VECIN` 队列和一个 `VECOUT` 队列分配 UB 缓冲 | 每个队列深度为 1 |
| 搬入 | `AllocTensor` → `DataCopy` → `EnQue` | 两份输入从 GM 进入 UB，并交给输入队列 |
| 计算 | `DeQue` → `Add` → `EnQue`，随后释放输入张量 | 从输入队列取数据，结果进入输出队列 |
| 搬出 | `DeQue` → `DataCopy` → `FreeTensor` | 结果从 UB 写回 GM，释放输出张量 |

这里的队列深度是 **1**，每个 Block 只处理一段数据，便于看清数据的生命周期。代码没有实现双缓冲或跨批次的计算与搬运重叠；使用 TPipe/TQue 本身不等于已经完成性能优化。当前样例与 `00_basic` 的主要区别是 UB 缓冲和阶段间依赖的组织方式。

## 本地 WSL：CPU 调试与 SIM 仿真

以下命令对应 `/home/lambertt/github-codes/ai-kernel-101`，需要先安装 CANN 9.1.0 Toolkit 和相应 ops 包。本地 WSL 用于 CPU 调试与 SIM 仿真；这两个模式不表示真实 NPU 已执行。

```bash
repo="$HOME/github-codes/ai-kernel-101"
source "$HOME/Ascend/cann/set_env.sh"
sample="$repo/src/vector_add/02_tpipe_tque"

for mode in cpu sim; do
  build="/tmp/ai-kernel-101-vector-add-02_tpipe_tque-$mode"
  cmake -S "$sample" -B "$build" \
    -DCMAKE_ASC_RUN_MODE="$mode" \
    -DCMAKE_ASC_ARCHITECTURES=dav-2201
  cmake --build "$build" --parallel 4
  "$build/demo"
done
```

两个模式使用不同的构建目录。程序打印 `Output` 和 `Golden` 的前 20 个元素，结果一致时输出 `test pass!` 并以退出码 0 结束。

## 有 NPU 的环境：真机运行

将本仓库克隆到云端 `/mnt/workspace/ai-kernel-101`，在具备昇腾设备的环境中执行。以下以 CANNLab A3 的 Toolkit 安装路径为例：

```bash
repo=/mnt/workspace/ai-kernel-101
source /home/developer/Ascend/ascend-toolkit/set_env.sh
sample="$repo/src/vector_add/02_tpipe_tque"
build="/mnt/workspace/ai-kernel-101-vector-add-02_tpipe_tque-npu"

cmake -S "$sample" -B "$build" \
  -DCMAKE_ASC_RUN_MODE=npu \
  -DCMAKE_ASC_ARCHITECTURES=dav-2201 \
  -DCMAKE_PREFIX_PATH="$ASCEND_HOME_PATH"
cmake --build "$build" --parallel 4
"$build/demo"
```

真机运行也应得到 `test pass!`；上面的 WSL 结果不能代替上板验证。
