# Host↔Device 传输基准

独立测量页锁定 Host 内存与 NPU Device 内存之间的 H2D、D2H 传输。程序用 `aclrtMallocHost`、`aclrtMalloc` 分配缓冲区，在同一 Stream 中批量提交 `aclrtMemcpyAsync`，用 `ACL_EVENT_TIME_LINE` Event 测量一批拷贝的 Stream 耗时，最后逐字节核对结果。

本工程只使用 AscendCL Host API，不包含 Ascend C Kernel；需要在有真实 NPU 的 CANN 9.1.0 环境运行。本地无 NPU 的 WSL 可以编译，但不能取得设备传输结果。

## 构建与运行

```bash
source /home/developer/Ascend/ascend-toolkit/set_env.sh
cmake -S /mnt/workspace/ai-kernel-101/src/vector_add/01_host_device_transfer \
  -B /mnt/workspace/ai-kernel-101-build/vector-add/01-host-device-transfer
cmake --build /mnt/workspace/ai-kernel-101-build/vector-add/01-host-device-transfer --parallel 4

bench=/mnt/workspace/ai-kernel-101-build/vector-add/01-host-device-transfer/transfer_bench
"$bench"                    # 默认 16 MiB，100 次
"$bench" 1048576 100         # 1 MiB，100 次
"$bench" 67108864 50        # 64 MiB，50 次
```

参数依次是**每次拷贝的字节数**和**计时区间内的拷贝次数**；每个方向另有 10 次预热。输出的 `us/copy` 是整批 Event 耗时除以次数；`GB/s` 按 `bytes × iterations / elapsed_seconds / 10^9` 计算，使用十进制 GB。H2D 和 D2H 单独计时，不包含内存分配、初始化和最后的逐字节校验。

这是一条 Stream 上重复拷贝同一块缓冲区的测量。Event 区间可能包含任务调度和提交间隙，因此结果应称为**该批传输的 Stream 有效带宽**，不能直接解释为纯 DMA 硬件峰值。比较不同数据量时，应在同一设备上多次运行并报告范围或中位数。程序使用页锁定 Host 缓冲区，避免普通可分页 Host 内存使异步接口退化为同步行为。

## API 依据

- [CANN 9.1 `aclrtMemcpyAsync`](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/runtimeapi/aclcppdevg_03_0069.html)
- [CANN 9.1 `aclrtCreateEventExWithFlag`](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/runtimeapi/aclcppdevg_03_0081.html)
- [CANN 9.1 `aclrtEventElapsedTime`](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/runtimeapi/aclcppdevg_03_0090.html)
