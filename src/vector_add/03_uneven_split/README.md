# Vector Add：长度不整除时的分核

本目录是 [ai-kernel-101](https://github.com/LamberttLiu/ai-kernel-101) 的向量加法练习，使用 **CANN 9.1.0**。源文件是 [`add.cpp`](./add.cpp)，构建文件是 [`CMakeLists.txt`](./CMakeLists.txt)。当前实现的目标架构为 `dav-2201`。

## 这一版做什么

在基础版上处理尾块不足 2,048 个元素的情况。本例固定生成 `7 × 2048 + 1000 = 15,336` 个 `float` 元素，启动 8 个 Block；最后一个 Block 只处理 1,000 个元素。数学运算为 `z[i] = x[i] + y[i]`。

- Host 根据 `ceil(totalLength / 2048)` 计算 Block 数，并把 `totalLength` 传给 Kernel。
- Kernel 用 `offset = block_idx * 2048` 定位数据段，再以 `currentLength = min(totalLength - offset, 2048)` 限制最后一块的搬运与计算长度。
- 本例尾块的 1,000 个 `float` 占 4,000 字节，仍是 32 字节的整数倍，因此继续使用 `AscendC::DataCopy`。
- 如果尾块字节数不能满足普通搬运的对齐要求，请看 [04_arbitrary_length](../04_arbitrary_length/README.md)。

程序会打印 `Output` 和 `Golden` 的前 20 个元素；完整结果一致时打印 `test pass!` 并以退出码 0 结束。CPU 调试和 SIM 仿真在本地 WSL 运行；`npu` 模式需要有昇腾设备的环境，本地 WSL 不具备真机设备。

## 本地 WSL：CPU 调试与 SIM 仿真

以下路径对应本地仓库 `/home/lambertt/github-codes/ai-kernel-101`。先确保 CANN 9.1.0 Toolkit 和相应 ops 包已安装，再运行：

```bash
repo="$HOME/github-codes/ai-kernel-101"
source "$HOME/Ascend/cann/set_env.sh"
sample="$repo/src/vector_add/03_uneven_split"

for mode in cpu sim; do
  build="/tmp/ai-kernel-101-vector-add-03_uneven_split-$mode"
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
sample="$repo/src/vector_add/03_uneven_split"
build="/mnt/workspace/ai-kernel-101-vector-add-03_uneven_split-npu"

cmake -S "$sample" -B "$build" \
  -DCMAKE_ASC_RUN_MODE=npu \
  -DCMAKE_ASC_ARCHITECTURES=dav-2201 \
  -DCMAKE_PREFIX_PATH="$ASCEND_HOME_PATH"
cmake --build "$build" --parallel 4
"$build/demo"
```

真机结果也应显示 `test pass!`。本 README 给出复现命令，不将本地 WSL 的 CPU/SIM 结果视作 NPU 实测。

继续阅读：[04_arbitrary_length：处理非对齐尾块](../04_arbitrary_length/README.md)。
