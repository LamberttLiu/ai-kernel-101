---
experiment_time: 2026-11-21
description: 云端 NPU 环境中 Hello World 的配置、编译、链接、运行及产物检查步骤。
---
# Hello World 程序的云端 NPU 构建

## 0. 开始前的位置和文件

本次实验在云端 NPU 环境中运行，仓库根目录为 `/mnt/workspace/ai-kernel-101`。使用 [hello_world.cpp](../src/hello_world.cpp)、[CMakeLists.txt](../src/CMakeLists.txt) 和 [npu-build.sh](../npu-build.sh)。查询到主机架构为 `aarch64`，仓库 HEAD 短哈希为 `3603c49`。CANN 环境脚本路径为 `/home/developer/Ascend/cann/set_env.sh`。

脚本将日志和构建产物保存到 `lab/hello_world/results/npu-build`。

## 1. 启动脚本，创建记录目录

在云端仓库根目录运行：

```bash
bash lab/hello_world/npu-build.sh
```

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

`Build files have been written to` 确认 CMake 已在 `build/` 生成构建文件。

## 3. 编译与链接

配置结束后脚本继续运行：

```bash
cmake --build "$PWD/lab/hello_world/results/npu-build/build" \
  --verbose --parallel 1 \
  2>&1 | tee "$PWD/lab/hello_world/results/npu-build/build.log"
```

- `--verbose` 保留实际编译和链接命令；
- `--parallel 1` 让输出按单任务顺序排列。

`build.log` 记录了两次毕昇调用，分别用于编译和链接。以下摘录省略了 Make 进入和离开目录等行：

```txt
[50%] Building ASC object CMakeFiles/demo.dir/hello_world.cpp.o
/home/developer/Ascend/cann-9.1.0/bin/bisheng -std=c++17 --npu-arch=dav-2201 --npu-arch=dav-2201 -MD -MT CMakeFiles/demo.dir/hello_world.cpp.o -MF CMakeFiles/demo.dir/hello_world.cpp.o.d -o CMakeFiles/demo.dir/hello_world.cpp.o -c --asc-aicore-lang /mnt/workspace/ai-kernel-101/lab/hello_world/src/hello_world.cpp
[100%] Linking ASC executable demo
/opt/buildtools/cmake-3.20.5-linux-aarch64/bin/cmake -E cmake_link_script CMakeFiles/demo.dir/link.txt --verbose=1
/home/developer/Ascend/cann-9.1.0/bin/bisheng --npu-arch=dav-2201 CMakeFiles/demo.dir/hello_world.cpp.o -o demo
[100%] Built target demo
```

编译调用以 `.cpp` 为输入生成 `.o`，链接调用以 `.o` 为输入生成 `demo`。结尾的 `[100%] Built target demo` 表示目标构建完成。
`build/CMakeFiles/demo.dir/flags.make` 保存编译选项，同目录下的 `link.txt` 保存链接命令，`hello_world.cpp.o.d` 保存编译依赖。

## 4. 运行 `demo` 并核对回显

先在云端终端直接执行：

```bash
./lab/hello_world/results/npu-build/build/demo
```

终端显示 Host 侧 ACL 调用成功，并输出 Block 0 到 Block 7 的八行 Hello World。脚本运行 `demo` 时也将程序输出写入云端的 `run.log`。

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

在云端检查 `lab/hello_world/results/npu-build`，确认有三份日志和 `build/`。目录树列出主要构建产物，省略 `CMakeFiles/` 中的其他自动生成文件。`report/` 在实验结束后添加。

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

`build.make` 中的 `$(ASC_FLAGS)` 展开后，编译命令带有两个 `--npu-arch=dav-2201`。重复参数来自 `flags.make` 中的变量值。

`build.make` 给出了生成 `hello_world.cpp.o` 的 Make 依赖规则，包含下面的内容：

```make
CMakeFiles/demo.dir/hello_world.cpp.o: CMakeFiles/demo.dir/flags.make
CMakeFiles/demo.dir/hello_world.cpp.o: /mnt/workspace/ai-kernel-101/lab/hello_world/src/hello_world.cpp
CMakeFiles/demo.dir/hello_world.cpp.o: CMakeFiles/demo.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/mnt/workspace/ai-kernel-101/lab/hello_world/results/npu-build/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building ASC object CMakeFiles/demo.dir/hello_world.cpp.o"
	 /home/developer/Ascend/cann-9.1.0/bin/bisheng $(ASC_DEFINES) $(ASC_INCLUDES)  -std=c++17 $(ASC_FLAGS) -MD -MT CMakeFiles/demo.dir/hello_world.cpp.o -MF CMakeFiles/demo.dir/hello_world.cpp.o.d -o CMakeFiles/demo.dir/hello_world.cpp.o -c --asc-aicore-lang /mnt/workspace/ai-kernel-101/lab/hello_world/src/hello_world.cpp
```

> [!Tip]
> 在 Make 规则中，冒号左边是**目标**，右边是**依赖**。

目标 `hello_world.cpp.o` 有三项依赖，分别来自编译选项文件 `flags.make`、源文件 `hello_world.cpp` 和 CMake 用于依赖跟踪的 `compiler_depend.ts`。

缩进的第一行显示构建进度，第二行调用毕昇编译器。编译命令各参数的作用如下。

- `/home/developer/Ascend/cann-9.1.0/bin/bisheng`：执行毕昇编译器驱动。
- `$(ASC_DEFINES)`、`$(ASC_INCLUDES)`、`$(ASC_FLAGS)`：Make 变量，执行时展开成定义、头文件搜索路径和编译选项。
- `-std=c++17`、`--asc-aicore-lang`：指定 C++ 标准，并让其后的 `.cpp` 源文件按 Ascend C 异构语言方式处理。
- `-c` 指定构建到目标文件为止，`-o CMakeFiles/demo.dir/hello_world.cpp.o` 指定输出路径。
- `-MD -MT CMakeFiles/demo.dir/hello_world.cpp.o -MF CMakeFiles/demo.dir/hello_world.cpp.o.d`：编译时将对应依赖也输出成 `.d` 文件：`-MF` 指定 `.d` 输出路径，`-MT` 指定依赖规则里的目标名。
- `/mnt/workspace/ai-kernel-101/lab/hello_world/src/hello_world.cpp`：指定输入源文件。

`CMakeLists.txt` 将 `hello_world.cpp` 交给 ASC 编译规则。

```cmake
set_source_files_properties(hello_world.cpp PROPERTIES LANGUAGE ASC)
```

同一源文件里既有设备侧入口
`__global__ __vector__ void hello_world()`，又有 Host 侧 `main()` 和 `hello_world<<<8, 0, stream>>>()` 发射调用。因此需要继续从 `.o` 的符号与节区辨认两侧分别留下了什么。

`link.txt` 记录了生成 `demo` 的完整链接命令。

```bash
/home/developer/Ascend/cann-9.1.0/bin/bisheng --npu-arch=dav-2201 CMakeFiles/demo.dir/hello_world.cpp.o -o demo
```

## 2. 检查 `.o` 和 `demo` 是什么文件

在仓库根目录，用 `file` 并排检查编译生成的 `.o` 和链接生成的 `demo`。

```bash
file lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o lab/hello_world/results/npu-build/build/demo
```

现场终端依次返回下面两行。为方便对照，摘录时省略了文件路径前缀。

```text
hello_world.cpp.o: ELF 64-bit LSB relocatable, ARM aarch64, version 1 (SYSV), not stripped
demo: ELF 64-bit LSB shared object, ARM aarch64, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux-aarch64.so.1, for GNU/Linux 3.7.0, not stripped
```

直接读取两份文件的 ELF 头，并检查 `demo` 的程序头和动态段。下面是从文件中读出的字段值。

```text
hello_world.cpp.o: EI_CLASS=2, EI_DATA=1, e_type=0x0001, e_machine=0x00b7
demo:              EI_CLASS=2, EI_DATA=1, e_type=0x0003, e_machine=0x00b7
demo:              PT_INTERP=/lib/ld-linux-aarch64.so.1, DT_FLAGS_1=0x08000000
```

两份产物均为 64 位、小端序的 AArch64 ELF（Executable and Linkable Format），保留了符号表。

- `hello_world.cpp.o` 是编译生成的可重定位目标文件（`ET_REL`）。
- `demo` 是链接生成的 Linux 位置无关可执行文件（PIE），其 ELF 类型为 `ET_DYN`，因此 `file` 显示为 `shared object`。
- 本地检查动态段确认了 `DF_1_PIE` 标志。运行 `demo` 时，Linux 使用 `/lib/ld-linux-aarch64.so.1` 加载它依赖的共享库。

## 3. 看`.o`目标文件的符号和节区

用 `nm -C` 查看目标文件中的 Host 入口、设备数据和运行时相关符号，再用 `readelf -W -S` 核对节名、大小和文件偏移。

```bash
nm -C lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o

readelf -W -S lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o
```

`nm -C` 的输出摘录如下。

```text
                 U AscendGetFuncFromBinary
                 U AscendLaunchKernelWithHostArgs
0000000000000000 t BishengDevBinaryEagerRegister
0000000000000088 t BishengLaunchKernelWithHostArgs
000000000000037c T hello_world
0000000000000008 d fatbinDataPtr
0000000000000010 d fatbinDataLength
                 U aclInit
                 U aclrtBinaryLoadFromData
                 U aclrtGetFuncBySymbol
                 U aclrtLaunchKernelWithHostArgs
0000000000000668 t cceModuleCtor
0000000000000000 d fatbinData
00000000000003bc T main
```

`readelf -W -S` 共列出 22 个节，节表从文件偏移 `0x57b8` 开始。关键行如下（保留原节编号）：

```text
  [Nr] Name              Type            Address          Off    Size   ES Flg Lk Inf Al
  [ 1] .text             PROGBITS        0000000000000000 000040 000674 00  AX  0   0  4
  [ 2] .rela.text        RELA            0000000000000000 003c50 000f18 18   I 19   1  8
  [ 3] .aicore_binary    PROGBITS        0000000000000000 000700 001bf0 00  WA  0   0 256
  [ 5] .data             PROGBITS        0000000000000000 002300 000018 00  WA  0   0  8
  [ 6] .rela.data        RELA            0000000000000000 004b68 000018 18   I 19   5  8
  [13] __aicore_rel_binary PROGBITS      0000000000000000 002698 001591 00   A  0   0  8
  [14] __aicore_rel_rec  PROGBITS        0000000000000000 003c30 000018 00 WAo  0   0  8
  [15] .rela__aicore_rel_rec RELA        0000000000000000 004cc8 000018 18   I 19  14  8
  [16] .init_array       INIT_ARRAY      0000000000000000 003c48 000008 00  WA  0   0  8
  [17] .rela.init_array  RELA            0000000000000000 004ce0 000018 18   I 19  16  8
  [19] .symtab           SYMTAB          0000000000000000 004cf8 000690 18     21  42  8
```

`nm` 中的 `T` 和 `t` 分别标记全局和局部代码符号，`U` 表示本文件中未定义的引用。另从本地 `.o` 读取符号表，确认 `main` 和 `hello_world` 都在外层 AArch64 ELF 的 `.text`，节内偏移分别是 `0x3bc` 和 `0x37c`。因此，此处看到的同名 `hello_world` 是 Host 侧代码符号。节表的 `Off` 则是节在文件中的偏移，例如 `.text` 从文件的 `0x40` 开始。

`.aicore_binary` 从文件偏移 `0x700` 开始，大小为 `0x1bf0` 字节。读取本地符号表和重定位记录，确认 `fatbinData` 位于该节开头，`.rela.data` 把 `fatbinDataPtr` 指向这个节，`fatbinDataLength` 保存的值正是 `0x1bf0`。这把设备二进制节与 Host 侧记录的地址和长度对应了起来。

`.rela__aicore_rel_rec` 指向 `__aicore_rel_binary` 的起始处，`.rela.init_array` 则把初始化项指向 `.text+0x668`，与 `cceModuleCtor` 的位置吻合。因此，链接前的 `.o` 已经包含 Host 代码、设备数据及关联它们的重定位记录。

## 4. 看最终文件的节、动态依赖及设备数据开头

继续用 `readelf` 和 `nm` 检查 `demo`：

```bash
readelf -W -S lab/hello_world/results/npu-build/build/demo

readelf -W -d lab/hello_world/results/npu-build/build/demo

nm -C lab/hello_world/results/npu-build/build/demo

readelf -W -x .aicore_binary lab/hello_world/results/npu-build/build/demo | head -10
```

以下按执行顺序取部分关键行。`readelf -W -S` 查看节表：

```text
There are 34 section headers, starting at offset 0x5c5c8:
  [Nr] Name              Type            Address          Off    Size   ES Flg Lk Inf Al
  [ 1] .interp           PROGBITS        00000000000002a8 0002a8 00001b 00   A  0   0  1
  [11] __aicore_rel_binary PROGBITS        0000000000008ef8 008ef8 001591 00   A  0   0  8
  [15] .text             PROGBITS        0000000000027250 017250 01aab4 00  AX  0   0 16
  [20] .init_array       INIT_ARRAY      0000000000052328 032328 000018 00  WA  0   0  8
  [22] .dynamic          DYNAMIC         0000000000052b40 032b40 000250 10  WA  7   0  8
  [26] .aicore_binary    PROGBITS        0000000000062f00 032f00 001bf0 00  WA  0   0 256
  [27] __aicore_rel_rec  PROGBITS        0000000000064af0 034af0 000018 00 WAo  0   0  8
```

`readelf -W -d` 查看动态段：

```text
Dynamic section at offset 0x32b40 contains 37 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libascendcl.so]
 0x0000000000000001 (NEEDED)             Shared library: [libruntime.so]
 0x0000000000000001 (NEEDED)             Shared library: [libstdc++.so.6]
 0x000000006ffffffb (FLAGS_1)            Flags: PIE
 0x0000000000000019 (INIT_ARRAY)         0x52328
 0x000000000000001b (INIT_ARRAYSZ)       24 (bytes)
```

`nm -C` 查看 Host 符号：

```text
0000000000028c24 t AscendGetFuncFromBinary
0000000000028e08 t AscendLaunchKernelWithHostArgs
00000000000276e0 T hello_world
0000000000027250 T _start
                 U aclInit
                 U aclrtBinaryLoadFromData
                 U aclrtGetFuncBySymbol
                 U aclrtLaunchKernelWithHostArgs
0000000000027720 T main
```

`readelf -W -x .aicore_binary ... | head -10` 查看设备数据开头：

```text
Hex dump of section '.aicore_binary':
  0x00062f00 7f454c46 02010100 00000000 00000000 .ELF............
  0x00062f10 02002910 01000000 00000000 00000000 ..).............
  0x00062f20 40000000 00000000 70180000 00000000 @.......p.......
  0x00062f30 00009400 40003800 03004000 0e000c00 ....@.8...@.....
```

- **链接调整了设备相关节的位置，保留了两块设备数据的原始字节。** `.aicore_binary` 的文件偏移从 `.o` 的 `0x700` 变为 `demo` 的 `0x32f00`，大小仍为 `0x1bf0`。`__aicore_rel_binary` 的偏移从 `0x2698` 变为 `0x8ef8`，大小仍为 `0x1591`。按各自节表的 `Off` 和 `Size` 从两个本地产物读取字节并计算 SHA-256 后，两个节各自的摘要均一致。节表也保留了 `__aicore_rel_rec`。
- **最终程序仍依赖 Host 侧动态库。** 动态段的 `FLAGS_1` 显示 `PIE`，`NEEDED` 同时列出 CANN 的 `libascendcl.so`、`libruntime.so` 和 Host 的 `libc.so.6`、`libstdc++.so.6`。`nm` 中，`AscendGetFuncFromBinary` 和 `AscendLaunchKernelWithHostArgs` 从 `.o` 中的 `U` 变成了 `demo` 中的 `t`，说明链接为它们纳入了定义。`aclInit`、`aclrtBinaryLoadFromData` 等仍标为 `U`，由运行时动态链接处理。
- **设备数据节开头是内层 ELF 头。** 回显的前四个字节是 ELF 魔数 `7f 45 4c 46`。该行开头的 `0x62f00` 对应节表的 `Address`，按文件取这段数据时应使用 `Off` 列的 `0x32f00`。与上一节看到的 Host `.text` 对照，`demo` 把 AArch64 Host 代码和这份内嵌 ELF 数据放在了不同的节里。

在仓库根目录执行以下三条命令，分别查看 `.o` 的 `.aicore_binary`、尝试读取另一个设备相关节，再查看 `demo` 的 `.aicore_binary`。

```bash
readelf -W -x .aicore_binary lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o | head -13
readelf -W -x .__aicore_rel_binary lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o | head -13
readelf -W -x .aicore_binary lab/hello_world/results/npu-build/build/demo | head -10
```

第一条命令对应的 `.o` 节开头如下（从本地回传的 `.o` 按节表偏移 `0x700` 读取前 64 字节，按十六进制格式重放）：

```text
Hex dump of section '.aicore_binary':
  0x00000000 7f454c46 02010100 00000000 00000000 .ELF............
  0x00000010 02002910 01000000 00000000 00000000 ..).............
  0x00000020 40000000 00000000 70180000 00000000 @.......p.......
  0x00000030 00009400 40003800 03004000 0e000c00 ....@.8...@.....
```

第二条命令报出警告：

```text
readelf: Warning: Section '.__aicore_rel_binary' was not dumped because it does not exist!
```

第三条命令的回显摘自 `demo.txt`。当前工作区保留以下摘录。

```text
Hex dump of section '.aicore_binary':
  0x00062f00 7f454c46 02010100 00000000 00000000 .ELF............
  0x00062f10 02002910 01000000 00000000 00000000 ..).............
  0x00062f20 40000000 00000000 70180000 00000000 @.......p.......
  0x00062f30 00009400 40003800 03004000 0e000c00 ....@.8...@.....
```

- 两份产物的 `.aicore_binary` 前 64 字节相同，都以 ELF 魔数 `7f 45 4c 46` 开头。`.o` 的节地址从 `0x0` 开始，`demo` 中变为 `0x62f00`。这两个值对应节表的 `Address` 列。
- 第二条命令多写了前导点，节表第 13 项的名称是 `__aicore_rel_binary`。重查时把 `-x .__aicore_rel_binary` 改为 `-x __aicore_rel_binary`。

## 5. 构建日志与阶段判断

在云端仓库根目录用 `wc -l` 核对三份日志，用 `file` 和 `readelf` 检查编译和链接的产物。回传日志后，在本地用最后一条命令对应的行号定位毕昇的两次调用。

```bash
wc -l lab/hello_world/results/npu-build/{configure,build,run}.log
file lab/hello_world/results/npu-build/build/{CMakeFiles/demo.dir/hello_world.cpp.o,demo}
readelf -W -S lab/hello_world/results/npu-build/build/demo
nl -ba lab/hello_world/results/npu-build/build.log | sed -n '11,17p'
```

按回传日志重新计数，三份文件各有以下行数：

```text
 7 lab/hello_world/results/npu-build/configure.log
19 lab/hello_world/results/npu-build/build.log
16 lab/hello_world/results/npu-build/run.log
```

`file` 的回显如下，省略路径前缀：

```text
hello_world.cpp.o: ELF 64-bit LSB relocatable, ARM aarch64, version 1 (SYSV), not stripped
demo: ELF 64-bit LSB shared object, ARM aarch64, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux-aarch64.so.1, for GNU/Linux 3.7.0, not stripped
```

从上面已记录的 `demo` 节表中摘出两条设备相关记录：

```text
  [11] __aicore_rel_binary PROGBITS        0000000000008ef8 008ef8 001591 00   A  0   0  8
  [26] .aicore_binary    PROGBITS        0000000000062f00 032f00 001bf0 00  WA  0   0 256
```

以下摘录保留 `build.log` 的原行号，省略第 16 行的 Make 退出目录提示。

```text
    11  [ 50%] Building ASC object CMakeFiles/demo.dir/hello_world.cpp.o
    12  /home/developer/Ascend/cann-9.1.0/bin/bisheng    -std=c++17 --npu-arch=dav-2201 --npu-arch=dav-2201 -MD -MT CMakeFiles/demo.dir/hello_world.cpp.o -MF CMakeFiles/demo.dir/hello_world.cpp.o.d -o CMakeFiles/demo.dir/hello_world.cpp.o -c --asc-aicore-lang /mnt/workspace/ai-kernel-101/lab/hello_world/src/hello_world.cpp
    13  [100%] Linking ASC executable demo
    14  /opt/buildtools/cmake-3.20.5-linux-aarch64/bin/cmake -E cmake_link_script CMakeFiles/demo.dir/link.txt --verbose=1
    15   /home/developer/Ascend/cann-9.1.0/bin/bisheng  --npu-arch=dav-2201 CMakeFiles/demo.dir/hello_world.cpp.o -o demo
    17  [100%] Built target demo
```

`configure.log` 中的 `Configuring done` 和 `Generating done` 标记配置完成和构建规则生成。`build.log` 第 12 行的毕昇调用生成 AArch64 可重定位目标文件 `hello_world.cpp.o`，并按 `-MF` 指定的路径写出依赖文件 `.o.d`。

第 14 行记录 CMake 执行 `link.txt`，第 15 行记录毕昇将 `.o` 链接为 `demo`，第 17 行报告目标构建完成。

这次构建由两次毕昇调用完成。第一次涵盖预处理、编译和汇编，生成同时包含 AArch64 Host 代码和设备数据的 `.o`。第二次链接生成 `demo`，两块设备数据的文件偏移发生变化，字节内容保持一致。云端 `run.log` 记录了 Host 侧 ACL 调用的成功回显和 8 个 AIV Block 的 Hello World 输出。
