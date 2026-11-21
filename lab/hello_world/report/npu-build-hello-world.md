---
experiment_time: 2026-11-21
description: 云端 NPU 环境中 Hello World 的配置、编译、链接、运行及产物检查步骤。
---

# Hello World：云端 NPU 构建与运行步骤记录

这份记录按当时在云端终端中的操作顺序写。实验日期为 2026-11-21，没有记录每条命令的精确时间。下面的“执行后目录”指云端状态；报告是事后复制到本地工作区的。

## 0. 开始前的位置和文件

云端环境仓库根目录 `/mnt/workspace/ai-kernel-101`。这次使用 [hello_world.cpp](../src/hello_world.cpp)、[CMakeLists.txt](../src/CMakeLists.txt) 和 [npu-build.sh](../npu-build.sh)。查询到主机架构为 `aarch64`，仓库 HEAD 短哈希为 `3603c49`。CANN 环境脚本路径为 `/home/developer/Ascend/cann/set_env.sh`。

只观察真实 NPU 环境。脚本的记录目录为 `lab/hello_world/results/npu-build`；下面记录的是本次在云端核对到的配置、构建、运行日志与产物。

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

后来重新核对云端的完整 `build.log`：该文件共有 19 行，能直接看到编译与链接两次毕昇调用。以下摘录关键行，省略了 Make 进入和离开目录等行；完整原始日志位于云端 `lab/hello_world/results/npu-build/build.log`：

```txt
[50%] Building ASC object CMakeFiles/demo.dir/hello_world.cpp.o
/home/developer/Ascend/cann-9.1.0/bin/bisheng -std=c++17 --npu-arch=dav-2201 --npu-arch=dav-2201 -MD -MT CMakeFiles/demo.dir/hello_world.cpp.o -MF CMakeFiles/demo.dir/hello_world.cpp.o.d -o CMakeFiles/demo.dir/hello_world.cpp.o -c --asc-aicore-lang /mnt/workspace/ai-kernel-101/lab/hello_world/src/hello_world.cpp
[100%] Linking ASC executable demo
/opt/buildtools/cmake-3.20.5-linux-aarch64/bin/cmake -E cmake_link_script CMakeFiles/demo.dir/link.txt --verbose=1
/home/developer/Ascend/cann-9.1.0/bin/bisheng --npu-arch=dav-2201 CMakeFiles/demo.dir/hello_world.cpp.o -o demo
[100%] Built target demo
```

编译调用以 `.cpp` 为输入生成 `.o`，链接调用以 `.o` 为输入生成 `demo`。结尾的 `[100%] Built target demo` 表示目标构建完成。
这一步后可以从 `build/CMakeFiles/demo.dir/flags.make` 核对编译选项，从 `link.txt` 核对链接命令。`hello_world.cpp.o.d` 是依赖文件。本次首次构建时还没有解析目标文件或 `demo` 的内部设备代码布局；后续的检查单独记在“对构建产物的进一步深入分析”。

## 4. 运行 `demo` 并保存退出状态

先在云端终端直接执行：

```bash
./lab/hello_world/results/npu-build/build/demo
```

终端显示 Host 侧 ACL 调用成功，并输出 Block 0 到 Block 7 的八行 Hello World。云端的 `run.log` 也记录了这一详细回显。

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

上述配置、构建和运行日志位于 `results/npu-build/` 下。`demo` 是刚才执行的文件，`hello_world.cpp.o` 是编译得到的目标文件。

# 对构建产物的进一步深入分析

## 1. 先看构建规则中的两次毕昇调用

涉及构建目录里的：

- `CMakeFiles/demo.dir/flags.make`；
- `CMakeFiles/demo.dir/build.make`；
- `CMakeFiles/demo.dir/link.txt`。

在 `flags.make` 中，观察到以下两行：

```make
# compile ASC with /home/developer/Ascend/cann-9.1.0/bin/bisheng
ASC_FLAGS = --npu-arch=dav-2201 --npu-arch=dav-2201
```

`ASC_FLAGS` 这一行内，`--npu-arch=dav-2201` 被连续写了两遍。下面 `build.make` 中只有一个 `$(ASC_FLAGS)` 引用；展开该变量后，编译命令才包含两个相同的参数。

`build.make` 给出了生成 `hello_world.cpp.o` 的 Make 依赖规则，包含下面的内容：

```make
CMakeFiles/demo.dir/hello_world.cpp.o: CMakeFiles/demo.dir/flags.make
CMakeFiles/demo.dir/hello_world.cpp.o: /mnt/workspace/ai-kernel-101/lab/hello_world/src/hello_world.cpp
CMakeFiles/demo.dir/hello_world.cpp.o: CMakeFiles/demo.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/mnt/workspace/ai-kernel-101/lab/hello_world/results/npu-build/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building ASC object CMakeFiles/demo.dir/hello_world.cpp.o"
	 /home/developer/Ascend/cann-9.1.0/bin/bisheng $(ASC_DEFINES) $(ASC_INCLUDES)  -std=c++17 $(ASC_FLAGS) -MD -MT CMakeFiles/demo.dir/hello_world.cpp.o -MF CMakeFiles/demo.dir/hello_world.cpp.o.d -o CMakeFiles/demo.dir/hello_world.cpp.o -c --asc-aicore-lang /mnt/workspace/ai-kernel-101/lab/hello_world/src/hello_world.cpp
```

先看冒号两边：左边重复出现的 `CMakeFiles/demo.dir/hello_world.cpp.o` 是**同一个待生成文件**，右边三次分别列出 `flags.make`、源文件 `hello_world.cpp` 和 `compiler_depend.ts`，这是为同一个目标列出依赖。`compiler_depend.ts` 是 CMake 依赖跟踪机制使用的文件，此处可以忽略。

缩进的第一行 `$(CMAKE_COMMAND) -E cmake_echo_color ... "Building ASC object ..."` 用来显示进度，下面重点看第二行才是真正调用毕昇编译器。

把这一行按作用拆开看：

- `/home/developer/Ascend/cann-9.1.0/bin/bisheng`：执行毕昇编译器驱动。
- `$(ASC_DEFINES)`、`$(ASC_INCLUDES)`、`$(ASC_FLAGS)`：Make 变量，执行时展开成定义、头文件搜索路径和编译选项。
- `-std=c++17`、`--asc-aicore-lang`：指定 C++ 标准，并让其后的 `.cpp` 源文件按 Ascend C 异构语言方式处理。
- `-o CMakeFiles/demo.dir/hello_world.cpp.o`、`-c`：这次调用的主要产物是 `.o` 目标文件；最终可执行文件 `demo` 不在这里形成。
- `-MD -MT CMakeFiles/demo.dir/hello_world.cpp.o -MF CMakeFiles/demo.dir/hello_world.cpp.o.d`：编译时将对应依赖也输出成 `.d` 文件：`-MF` 指定 `.d` 输出路径，`-MT` 指定依赖规则里的目标名。
- 最后的 `/mnt/workspace/ai-kernel-101/lab/hello_world/src/hello_world.cpp`：输入源文件。

 `CMakeLists.txt` 中：

```cmake
set_source_files_properties(hello_world.cpp PROPERTIES LANGUAGE ASC)
```

表示代码会被交给 ASC 编译规则。同一源文件里既有设备侧入口 
`__global__ __vector__ void hello_world()`，又有 Host 侧 `main()` 和 `hello_world<<<8, 0, stream>>>()` 发射调用。因此需要继续从 `.o` 的符号与节区辨认两侧分别留下了什么。

`link.txt` 的完整一行是：

```bash
/home/developer/Ascend/cann-9.1.0/bin/bisheng --npu-arch=dav-2201 CMakeFiles/demo.dir/hello_world.cpp.o -o demo
```

这是另一轮毕昇调用，输入为 `.o`，输出为 `demo`。CMake 配置生成这两条构建规则，两次调用分别做了两个步骤。

## 2. 检查 `.o` 和 `demo` 是什么文件

在构建目录的相对路径上运行 `file`：

```bash
file lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o lab/hello_world/results/npu-build/build/demo
```

终端给出的类型信息为（路径前缀省略）：

```text
hello_world.cpp.o: ELF 64-bit LSB relocatable, ARM aarch64, version 1 (SYSV), not stripped
demo: ELF 64-bit LSB shared object, ARM aarch64, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux-aarch64.so.1, for GNU/Linux 3.7.0, not stripped
```

`file` 把 `demo` 的外层 ELF 报成 `shared object`，同时显示它有动态加载器；前一轮已实际执行这个文件。由此可确认外层是 AArch64 主机 ELF，不能仅凭 `file demo` 就断定设备侧二进制不存在。

## 3. 看目标文件的符号和节区

终端使用 `nm -C` 查目标文件符号，再用 `readelf -W -S` 看节表；下面给出能重做这次检查的命令：

```bash
nm -C lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o

readelf -W -S lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o
```

`nm` 输出中可见 `main`、`hello_world`、`fatbinData`、`fatbinDataPtr`、`fatbinDataLength`，以及 `BishengDevBinaryEagerRegister`、`BishengLaunchKernelWithHostArgs` 等符号；ACL 的 `aclInit`、`aclrtSetDevice`、`aclrtCreateStream`、`aclrtSynchronizeStream` 等在 `.o` 中仍是未定义引用。只凭这些名字能确认目标文件包含主机入口、设备数据相关符号和运行时调用引用，尚不能断言设备数据在运行时的确切注册时机。

节表中观察到 `.text`、`.aicore_binary`、`.__aicore_rel_binary`、`.__aicore_rel_rec` 等节。其中 `.aicore_binary` 大小为 `0x1bf0`，`.__aicore_rel_binary` 大小为 `0x1591`。这说明 `.o` 除了主机代码相关节，还有独立的设备相关节；节名是线索，接着用十六进制内容进一步核对。

## 4. 看最终文件的节、动态依赖及设备数据开头

继续在云端用 `readelf` 和 `nm` 检查 `demo`：

```bash
readelf -W -S lab/hello_world/results/npu-build/build/demo
readelf -W -d lab/hello_world/results/npu-build/build/demo
nm -C lab/hello_world/results/npu-build/build/demo
readelf -W -x .aicore_binary lab/hello_world/results/npu-build/build/demo | head -10
```

`demo` 中仍能看到 `.aicore_binary`（大小 `0x1bf0`）、`.__aicore_rel_binary`（大小 `0x1591`）和 `fatbinData`、`hello_world` 等符号。动态节的 `NEEDED` 项包括 `libascendcl.so`、`libruntime.so`，也包括 `libc.so.6`、`libstdc++.so.6` 等主机库。`readelf -x .aicore_binary` 输出的开头为：

```text
Hex dump of section '.aicore_binary':
  0x00062f00 7f454c46 02010100 00000000 00000000 .ELF............
```

开头的 `7f 45 4c 46` 是 ELF 魔数。我们实际看到的是**外层 AArch64 ELF 中的一个节以另一个 ELF 文件头开头**；目前没有抽取、解析这个内层 ELF 的程序头、符号和指令，因此不把其内部结构写成已验证结论。

检查过程中还尝试对 `hello_world.cpp.o` 查看另一个节；同一行还分别查看了 `.o` 与 `demo` 的 `.aicore_binary` 开头：

```bash
readelf -W -x .aicore_binary lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o | head -13
readelf -W -x .__aicore_rel_binary lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o | head -13
readelf -W -x .aicore_binary lab/hello_world/results/npu-build/build/demo | head -10
```

第二条命令的回显是 `readelf: Warning: Section '.__aicore_rel_binary' was not dumped because it does not exist!`。这与先前节表显示的节名不一致，可能是输入节名或文件选取出了差错；保留这个回显，不用它否定节表观察。后续要重新从节表复制精确名称核查。

## 5. 构建日志与阶段判断

在云端仓库根目录执行以下只读命令，核对这份日志及两个产物：

```bash
wc -l lab/hello_world/results/npu-build/{configure,build,run}.log
file lab/hello_world/results/npu-build/build/{CMakeFiles/demo.dir/hello_world.cpp.o,demo}
readelf -W -S lab/hello_world/results/npu-build/build/demo
```

本次回显：`configure.log` 7 行、`build.log` 19 行、`run.log` 16 行。检查日志关键行时，第 11、12 行是生成 `.o` 的进度与毕昇命令，第 13、15 行是链接 `demo` 的进度与毕昇命令，第 17 行为 `[100%] Built target demo`。`file` 将 `.o` 识别为 AArch64 可重定位 ELF，将 `demo` 识别为带动态加载器的 AArch64 ELF；`readelf` 在 `demo` 中列出 `.aicore_binary`（`0x1bf0`）及 `.__aicore_rel_binary`（`0x1591`）。构建规则给出的两条调用与本轮实际构建日志相互吻合；产物类型和设备相关节也与前述检查相符。

与普通 C/C++ 的“预处理 → 编译 → 汇编 → 链接”相比，当前证据直接覆盖的是 CMake 配置、毕昇生成 `.o` 的调用、毕昇链接 `demo` 的调用，以及两种 ELF 产物。源码的头文件与宏需要处理，Host 和 Device 都需要生成机器可执行内容；但本次没有保留预处理输出、汇编文件或毕昇驱动的内部子命令，不能据此给它们逐项标上具体工具与发生顺序。下一次可以在**另一个记录目录**里确认当前版本毕昇支持的诊断和中间文件保存选项，再分别检查内层 ELF、Host 代码与设备指令。

