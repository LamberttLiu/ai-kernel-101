# 2026-11-05：原代码仓库的 WSL CPU 验证记录

> 本记录从原本地代码仓库 README 的“WSL CPU 验证（2026-11-05）”章节整理迁入。它是既有记录，不是本次合并重新取得的实验结果。原始构建日志未随本次工作区合并导入。

# 环境与编译方式

原记录环境：WSL Ubuntu 24.04、CANN 9.1.0、dav-2201，CMAKE_ASC_RUN_MODE=cpu。

内核源文件统一使用 .cpp 扩展名，在 CMake 中显式设置 LANGUAGE ASC，继续使用 CANN ASC 编译流程。Host/Device 传输测速是普通 C++/ACL 程序，不具有 CPU 调试模式。

# 原记录结果

| 样例 | 原记录结论 |
| --- | --- |
| hello_world | 编译成功，8 个 Block 打印 Hello World，退出码 0 |
| 00_basic | 编译成功，默认输入 test pass!，退出码 0 |
| 02_tpipe_tque | 编译成功，默认输入 test pass!，退出码 0 |
| 03_uneven_split | 编译成功，默认输入 test pass!，退出码 0 |
| 04_arbitrary_length | 默认输入及长度 0、1、7、8、1001、2048、2049 通过 |
| 01_host_device_transfer | 编译成功；本地运行在 aclInit 返回 aclError=500000，退出码 1，未通过运行验证 |

原记录的构建产物及 configure.log、build.log、run.log 位于 WSL 的 `/home/lambertt/github-codes/ai-kernel-101-build-cpu`，不属于本仓库已经归档的证据文件。CPU 结果不替代 SIM 或 NPU 验证。

# 复现基础向量加

按实际安装位置调整 CANN 环境路径，并在具备工具链的 Linux/WSL 环境运行：

```bash
source "$HOME/Ascend/cann/set_env.sh"
repo="$HOME/github-codes/ai-kernel-101"
build="$HOME/github-codes/ai-kernel-101-build-cpu/vector_add/00_basic"
cmake -S "$repo/src/vector_add/00_basic" -B "$build" \
  -DCMAKE_ASC_RUN_MODE=cpu -DCMAKE_ASC_ARCHITECTURES=dav-2201
cmake --build "$build" --parallel 4
mkdir -p "$build/run"
(cd "$build/run" && "$build/demo")
```

各样例的具体说明仍在 [src 目录](../src/README.md)，未来新增实验按 [实验记录约定](../lab/README.md)保存真实参数和结果。
