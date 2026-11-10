# Vector Add：处理非对齐尾块

本目录是 [ai-kernel-101](https://github.com/LamberttLiu/ai-kernel-101) 的向量加法练习，使用 **CANN 9.1.0**。源文件是 [`add.cpp`](./add.cpp)，构建文件是 [`CMakeLists.txt`](./CMakeLists.txt)。当前实现的目标架构为 `dav-2201`。

## 这一版做什么

在不均匀分核版上处理尾块字节数不按 32 字节对齐的情况。默认输入为 `7 × 2048 + 1001 = 15,337` 个 `float` 元素，最后一个 Block 处理 1,001 个元素，即 4,004 字节。数学运算为 `z[i] = x[i] + y[i]`。

- Host 从命令行读取元素个数；未提供参数时使用默认值 15,337。Block 数仍按 `ceil(totalLength / 2048)` 计算。
- Kernel 根据 `currentLength` 构造 `DataCopyExtParams`，用 `AscendC::DataCopyPad` 搬入和搬出尾块数据，再对有效元素执行 `AscendC::Add`。
- `0` 长度由 Host 直接返回空结果；其他长度仍受设备资源和 Kernel 约束，标题中的“任意长度”指不要求尾块凑齐 2,048 个元素或 32 字节对齐。
- 默认用例会将设备结果与 Host 上的 `x + y` 逐元素比较。

程序会打印 `Output` 和 `Golden` 的前 20 个元素；完整结果一致时打印 `test pass!` 并以退出码 0 结束。CPU 调试和 SIM 仿真在本地 WSL 运行；`npu` 模式需要有昇腾设备的环境，本地 WSL 不具备真机设备。

## 本地 WSL：CPU 调试与 SIM 仿真

以下路径对应本地仓库 `/home/lambertt/github-codes/ai-kernel-101`。先确保 CANN 9.1.0 Toolkit 和相应 ops 包已安装，再运行：

```bash
repo="$HOME/github-codes/ai-kernel-101"
source "$HOME/Ascend/cann/set_env.sh"
sample="$repo/src/vector_add/04_arbitrary_length"

for mode in cpu sim; do
  build="/tmp/ai-kernel-101-vector-add-04_arbitrary_length-$mode"
  cmake -S "$sample" -B "$build" \
    -DCMAKE_ASC_RUN_MODE="$mode" \
    -DCMAKE_ASC_ARCHITECTURES=dav-2201
  cmake --build "$build" --parallel 4
  "$build/demo"
done
```

两个模式使用独立构建目录，避免切换模式时沿用旧的 CMake 缓存。以 `test pass!` 和进程退出码 0 作为当前模式的结果检查。

## 有 NPU 的环境：真机运行

将仓库克隆到云端的 `/mnt/workspace/ai-kernel-101` 后，在已安装 CANN 9.1.0 且可访问 NPU 的环境中运行。下面以 CANNLab A3 的 Toolkit 路径为例；其他环境按实际安装位置调整 `set_env.sh`。

```bash
repo=/mnt/workspace/ai-kernel-101
source /home/developer/Ascend/ascend-toolkit/set_env.sh
sample="$repo/src/vector_add/04_arbitrary_length"
build="/mnt/workspace/ai-kernel-101-vector-add-04_arbitrary_length-npu"

cmake -S "$sample" -B "$build" \
  -DCMAKE_ASC_RUN_MODE=npu \
  -DCMAKE_ASC_ARCHITECTURES=dav-2201 \
  -DCMAKE_PREFIX_PATH="$ASCEND_HOME_PATH"
cmake --build "$build" --parallel 4
"$build/demo"
# 可把上一行改为 "$build/demo" 1001，以指定元素个数
```

真机结果也应显示 `test pass!`。本 README 给出复现命令，不将本地 WSL 的 CPU/SIM 结果视作 NPU 实测。

对照阅读：[00_basic：固定等分](../00_basic/README.md) · [03_uneven_split：不均匀分核](../03_uneven_split/README.md)。
