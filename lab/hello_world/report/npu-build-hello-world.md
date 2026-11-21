---
experiment_time: 2026-11-21
description: 云端 NPU 环境中 Hello World 的配置、编译、链接、运行及产物检查步骤。
---

# Hello World：云端 NPU 构建与运行步骤记录

这份记录按当时在云端终端中的操作顺序写。实验日期为 2026-11-21，没有记录每条命令的精确时间。下面的“执行后目录”指云端状态；报告是事后复制到本地工作区的。

## 0. 开始前的位置和文件

云端环境仓库根目录 `/mnt/workspace/ai-kernel-101`。这次使用 [hello_world.cpp](../src/hello_world.cpp)、[CMakeLists.txt](../src/CMakeLists.txt) 和 [npu-build.sh](../npu-build.sh)。查询到主机架构为 `aarch64`，仓库 HEAD 短哈希为 `3603c49`。CANN 环境脚本路径为 `/home/developer/Ascend/cann/set_env.sh`。

只观察真实 NPU 环境。脚本的记录目录固定为 `lab/hello_world/results/npu-build`，再次运行会更新同名日志和构建产物，因此下文是当时那一次执行所见。

## 1. 启动脚本，创建记录目录

在云端仓库根目录运行：

```bash
bash lab/hello_world/npu-build.sh
```

下为脚本实际执行的具体操作详解。
## 2. CMake 配置

脚本内执行的命令（把脚本中的 `record` 展开为实际路径）：

```bash
cmake -S "$PWD/lab/hello_world/src" \
  -B "$PWD/lab/hello_world/results/npu-build/build" \
  -DCMAKE_ASC_RUN_MODE=npu \
  -DCMAKE_ASC_ARCHITECTURES=dav-2201 \
  2>&1 | tee "$PWD/lab/hello_world/results/npu-build/configure.log"
```

- `-S` 是源码目录；
- `-B` 是这次新建的构建目录；
- 两个 `-D` 参数分别明确选择 NPU 模式和 `dav-2201`。

标准输出和错误输出同时显示在终端并保存到 `configure.log`：

```
-- System processer: aarch64
-- CMAKE_ASC_COMPILER: /home/developer/Ascend/cann-9.1.0/bin/bisheng
-- ASCEND_CANN_PACKAGE_LINUX_PATH: /home/developer/Ascend/cann-9.1.0/aarch64-linux
-- CMAKE_ASC_LLD_LINKER: /home/developer/Ascend/cann-9.1.0/aarch64-linux/ccec_compiler/bin/ld.lld
-- Configuring done
-- Generating done
-- Build files have been written to: /mnt/workspace/ai-kernel-101/lab/hello_world/results/npu-build/build
```

此时 CMake 已生成构建文件，但还不能据此判断程序已经编译和运行。

## 3. 编译与链接

配置结束后脚本继续运行：

```bash
cmake --build "$PWD/lab/hello_world/results/npu-build/build" \
  --verbose --parallel 1 \
  2>&1 | tee "$PWD/lab/hello_world/results/npu-build/build.log"
```

- `--verbose` 保留实际编译和链接命令；
- `--parallel 1` 让输出按单任务顺序排列。

编译和构建阶段日志 `build.log` 部分显示：

```txt
/opt/buildtools/cmake-3.20.5-linux-aarch64/bin/cmake -S/mnt/workspace/ai-kernel-101/lab/hello_world/src -B/mnt/workspace/ai-kernel-101/lab/hello_world/results/

......

Consolidate compiler generated dependencies of target demo

...... 

[100%] Built target demo
make[1]: Leaving directory '/mnt/workspace/ai-kernel-101/lab/hello_world/results/npu-build/build'
```

结尾显示： `[100%] Built target demo` 表示构建完成。
这一步后可以从 `build/CMakeFiles/demo.dir/flags.make` 核对编译选项，从 `link.txt` 核对链接命令。`hello_world.cpp.o.d` 是依赖文件。本次还没有解析目标文件或 `demo` 的内部设备代码布局。

## 4. 运行 `demo` 并保存退出状态

先在云端终端直接执行：

```bash
./lab/hello_world/results/npu-build/build/demo
```

终端显示 Host 侧 ACL 调用成功，并输出 Block 0 到 Block 7 的八行 Hello World。本地的 `run.log` 也记录了这一详细回显。

```txt
[HOST][OK] aclInit: ret=0
[HOST][OK] aclrtSetDevice: ret=0
[HOST][OK] aclrtCreateStream: ret=0
[HOST] Kernel launch call returned; waiting for Stream completion.
[HOST][OK] aclrtSynchronizeStream: ret=0
[HOST][OK] aclrtDestroyStream: ret=0
[AIV Block 4/8] [Block (4/8)]: Hello World!!!
[AIV Block 5/8] [Block (5/8)]: Hello World!!!
[AIV Block 6/8] [Block (6/8)]: Hello World!!!
[AIV Block 7/8] [Block (7/8)]: Hello World!!!
[AIV Block 0/8] [Block (0/8)]: Hello World!!!
[AIV Block 1/8] [Block (1/8)]: Hello World!!!
[AIV Block 2/8] [Block (2/8)]: Hello World!!!
[AIV Block 3/8] [Block (3/8)]: Hello World!!!
[HOST][OK] aclrtResetDevice: ret=0
[HOST][OK] aclFinalize: ret=0
```

## 5. 执行后检查文件目录

在云端机器检查 `lab/hello_world/results/npu-build`，看到了三份日志和 `build/`。下面展开本次重点查看的构建产物；`CMakeFiles/` 下还有其他自动生成的依赖和规则文件。`report/` 是事后添加的记录目录，不是构建脚本产物。

```text
lab/hello_world/
├── npu-build.sh
├── src/
│   ├── CMakeLists.txt
│   └── hello_world.cpp
├── results/
│   └── npu-build/
│       ├── configure.log
│       ├── build.log
│       ├── run.log
│       └── build/
│           ├── CMakeCache.txt
│           ├── Makefile
│           ├── cmake_install.cmake
│           ├── autogen/
│           │   ├── custom_compile_options.ini
│           │   ├── custom_opc_options.ini
│           │   └── group_proto/
│           ├── CMakeFiles/
│           │   └── demo.dir/
│           │       ├── flags.make
│           │       ├── link.txt
│           │       ├── hello_world.cpp.o
│           │       └── hello_world.cpp.o.d
│           └── demo
└── report/
```

上述的配置、构建和运行日志也位于路劲下。`demo` 是刚才执行的文件，`hello_world.cpp.o` 是编译得到的目标文件。

