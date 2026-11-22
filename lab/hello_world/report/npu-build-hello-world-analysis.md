---
experiment_time: 2026-11-21
description: 云端 NPU 环境中 Hello World 的配置、编译、链接、运行及产物检查步骤。
---
# Hello World 程序的云端 NPU 构建

## 0. 开始前的位置和文件

本次实验在云端 NPU 环境中运行，仓库根目录为 `/mnt/workspace/ai-kernel-101`。使用 [hello_world.cpp](../src/hello_world.cpp)、[CMakeLists.txt](../src/CMakeLists.txt) 和 [npu-build.sh](../npu-build.sh)。查询到主机架构为 `aarch64`。CANN 环境脚本路径为 `/home/developer/Ascend/cann/set_env.sh`。

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

先打开 `CMakeFiles/demo.dir/build.make` 编译文件，找到生成 `hello_world.cpp.o` 的规则。冒号右边列出了 `flags.make`、源文件 `hello_world.cpp` 和 CMake 用于依赖跟踪的 `compiler_depend.ts`。

```make
CMakeFiles/demo.dir/hello_world.cpp.o: CMakeFiles/demo.dir/flags.make
CMakeFiles/demo.dir/hello_world.cpp.o: /mnt/workspace/ai-kernel-101/lab/hello_world/src/hello_world.cpp
CMakeFiles/demo.dir/hello_world.cpp.o: CMakeFiles/demo.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/mnt/workspace/ai-kernel-101/lab/hello_world/results/npu-build/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building ASC object CMakeFiles/demo.dir/hello_world.cpp.o"
	 /home/developer/Ascend/cann-9.1.0/bin/bisheng $(ASC_DEFINES) $(ASC_INCLUDES)  -std=c++17 $(ASC_FLAGS) -MD -MT CMakeFiles/demo.dir/hello_world.cpp.o -MF CMakeFiles/demo.dir/hello_world.cpp.o.d -o CMakeFiles/demo.dir/hello_world.cpp.o -c --asc-aicore-lang /mnt/workspace/ai-kernel-101/lab/hello_world/src/hello_world.cpp
```

> [!Tip]
> 在 Make 规则中，冒号左边是 **目标**（target），右边是 **依赖** （dependency）。

缩进的第一行用于显示构建进度，第二行调用毕昇编译器，以末尾的 `hello_world.cpp` 为输入，其中用 `-c` 编译并通过 `-o` 指定输出 `hello_world.cpp.o`。同一次调用还通过 `-MD` 生成依赖清单，`-MF` 指定写入 `hello_world.cpp.o.d`，`-MT` 指定清单里的目标名。进度行把目标称为 `ASC object`。源文件虽然以 `.cpp` 结尾，但 `CMakeLists.txt` 用下面这行将它交给 ASC 编译规则。对应的毕昇命令带有 `--asc-aicore-lang`，并用 `-std=c++17` 指定 C++ 标准。

```cmake
set_source_files_properties(hello_world.cpp PROPERTIES LANGUAGE ASC)
```

编译规则里还有三个待展开的 Make 变量。顺着 `build.make` 中的 `include CMakeFiles/demo.dir/flags.make` 找到它们的值。

```make
ASC_DEFINES =

ASC_INCLUDES =

ASC_FLAGS =  --npu-arch=dav-2201 --npu-arch=dav-2201
```

本次 `ASC_DEFINES` 和 `ASC_INCLUDES` 为空，`ASC_FLAGS` 则含有两个相同的 `--npu-arch=dav-2201`。Make 展开这个变量后，两项都出现在实际编译命令里，与 `build.log` 的回显一致。

生成的 `.o` 接下来被谁使用？继续在 `build.make` 里查找 `demo` 的规则，可以看到它依赖刚才的目标文件，并通过 `cmake_link_script` 执行 `link.txt`。

```make
demo: CMakeFiles/demo.dir/hello_world.cpp.o
demo: CMakeFiles/demo.dir/build.make
demo: CMakeFiles/demo.dir/link.txt
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/demo.dir/link.txt --verbose=$(VERBOSE)
```

`link.txt` 中记录的是第二次毕昇调用。

```bash
/home/developer/Ascend/cann-9.1.0/bin/bisheng --npu-arch=dav-2201 CMakeFiles/demo.dir/hello_world.cpp.o -o demo
```

这条命令直接以第一次调用生成的 `hello_world.cpp.o` 为输入，用 `-o demo` 指定链接产物。

## 2. 检查 `.o` 和 `demo` 是什么文件

上一节从构建规则看到，毕昇生成 `hello_world.cpp.o` 后，再把它链接成 `demo`。这两个产物分别是什么类型？先用 `file` 并排查看。

```bash
file lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o lab/hello_world/results/npu-build/build/demo
```

现场终端依次返回下面两行。为方便对照，摘录时省略了文件路径前缀：

```text
hello_world.cpp.o: ELF 64-bit LSB relocatable, ARM aarch64, version 1 (SYSV), not stripped
demo: ELF 64-bit LSB shared object, ARM aarch64, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux-aarch64.so.1, for GNU/Linux 3.7.0, not stripped
```

两份产物都是 64 位、小端序的 AArch64 ELF。第一行把 `.o` 标为 `relocatable`，第二行却把已经直接运行过的 `demo` 显示为 `shared object`。为了弄清这两个标签对应的 ELF 类型，接着用 `readelf -h` 查看文件头。

```bash
LC_ALL=C readelf -h lab/hello_world/results/npu-build/build/{CMakeFiles/demo.dir/hello_world.cpp.o,demo} | grep -E '^(File:|  (Class|Data|Type|Machine):)'
```

回显如下：

```text
File: lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o
  Class:                             ELF64
  Data:                              2's complement, little endian
  Type:                              REL (Relocatable file)
  Machine:                           AArch64
File: lab/hello_world/results/npu-build/build/demo
  Class:                             ELF64
  Data:                              2's complement, little endian
  Type:                              DYN (Position-Independent Executable file)
  Machine:                           AArch64
```

- `.o` 的 `Type` 是 `REL (Relocatable file)`，对应 ELF 规范中的 `ET_REL`，和 `file` 的回显 `relocatable` 一致。
- `demo` 的 `Type` 是 `DYN (Position-Independent Executable file)`。其中 `DYN` 对应 ELF 头中的 `ET_DYN`，这种类型也用于共享库，因而本次 `file` 给出的 `shared object` 标签也反映了这个类型。

> [!TIP]
> - `readelf -h <文件>`读取 ELF 头，显示 `Class`、`Data`、`Type`、`Machine` 等基本信息，可用于确认文件位数、字节序、类型和目标架构。
> - `REL (Relocatable file)`（`ET_REL`）通常是编译生成的 `.o` 目标文件，需要经过链接才能生成可执行文件（bin）或共享库 (.so) 。`DYN`（`ET_DYN`）表示动态对象类型，既用于共享库，也用于 PIE 可执行文件；此处 `demo` 的 `DYN` 由 PIE 标志进一步识别为位置无关可执行文件。

要看 `readelf` 为什么进一步标出位置无关可执行文件（PIE），需要再检查 `demo` 动态段中的 `FLAGS_1`。[ELF 类型定义](https://refspecs.linuxfoundation.org/elf/gabi4+/ch4.eheader.html)

```bash
LC_ALL=C readelf -W -d lab/hello_world/results/npu-build/build/demo | grep -F '(FLAGS_1)'
```

```text
 0x000000006ffffffb (FLAGS_1)            Flags: PIE
```

`Flags: PIE` 表示动态段的 `DT_FLAGS_1` 设置了 `DF_1_PIE`。这就解释了两条回显如何对应起来：`DYN` 是 ELF 头里的类型，`PIE` 是动态段里进一步标明的用途。到这里确认了两个产物的外层 ELF 类型。[glibc 标志定义](https://github.com/bminor/glibc/blob/master/elf/elf.h)

> [!TIP]
> `readelf -W -d <文件>`以宽格式显示动态段条目：`-d` 用于查看动态链接信息，`-W` 避免长行被折行。检查其中的 `FLAGS_1` 可以看到相关标志，例如 `PIE`。
> `FLAGS_1` 是 ELF 动态段中的 `DT_FLAGS_1` 条目，用位标志记录动态链接相关属性；其中 `DF_1_PIE`（`readelf` 显示为 `PIE`）表示该可执行文件被标记为位置无关可执行文件。

## 3. 看`.o`目标文件的符号和节区

同一份源码里既有 Device 侧入口 `__global__ __vector__ void hello_world()`，也有 Host 侧的 `main()` 和 `hello_world<<<8, 0, stream>>>()` 发射调用。两侧内容在 `.o` 中留下了哪些线索？先用 `nm -C` 看符号。

```bash
nm -C lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o
```

> [!TIP]
> `nm` 用于列出目标文件中的符号及其地址、类型等信息；大写选项 `-C` 会将 C++ 修饰后的符号名反修饰成更易读的形式。
> 输出通常按“符号值（通常是该符号在所属节区内的偏移量）、类型字符、符号名”排列；`U` 这类未定义符号没有符号值。
>
> - `U`：未定义符号，表示当前目标文件引用了该符号，通常由后续链接提供定义。
> - `T` / `t`：代码区（text）中的符号；大写 `T` 表示全局符号，小写 `t` 表示局部符号。
> - `d`：已初始化数据区中的局部符号；对应的大写 `D` 表示全局符号。

`nm -C` 的输出摘录如下：

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

`main` 和 `hello_world` 都标为 `T`，表示它们是外层 AArch64 对象中的全局代码符号。`BishengLaunchKernelWithHostArgs` 等标为 `t`，是局部代码符号。`aclInit` 等标为 `U`，是留给链接处理的未定义引用。回显里还出现了 `fatbinData`、`fatbinDataPtr` 和 `fatbinDataLength` 三个数据符号。它们对应的设备数据在文件哪里？接着用 `readelf -W -S` 查看节名、文件偏移和大小。

```bash
readelf -W -S lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o
```

回显共列出 22 个节，节表从文件偏移 `0x57b8` 开始。下面摘录相关行，保留原节编号：

```text
There are 22 section headers, starting at offset 0x57b8:
Section Headers:

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

> [!TIP]
> `readelf -W -S <文件>`显示 ELF 节表：`-S` 列出各节的元数据，`-W` 使用宽输出以避免长行折行。表头各列含义如下：
>
> - `Nr`：节编号；`Name`：节名；`Type`：节类型，如 `PROGBITS`、`SYMTAB`、`RELA`。
> - `Address`：节的虚拟地址；对于尚未链接的 `.o`，通常为 `0`。`Off`：节在文件中的起始偏移；`Size`：节占用的字节数。
> - `ES`：每个表项的大小；`Flg`：节属性标志，常见的 `A` 表示可分配到内存，`W` 表示可写，`X` 表示可执行。
> - `Lk`：链接字段，通常指向相关节的编号；`Inf`：依节类型而定的附加信息；`Al`：对齐要求，以字节为单位。

先用节表目录定位文件里的几块关键内容。

- 第 1 节 `.text` 的 `Flg` 有 `X`，说明这个节的内容可执行。
- 第 3 节 `.aicore_binary` 的 `Off` 是 `0x700`，`Size` 是 `0x1bf0`。从 `.o` 文件开头跳过 `0x700` 字节，再连续读取 `0x1bf0` 字节（7152 字节），取到的就是这个节的全部内容。
- 第 13 节 `__aicore_rel_binary` 也按同样的方法读取。从文件偏移 `0x2698` 开始，连续读取 `0x1591` 字节（5521 字节）。

这两个节都是 `PROGBITS`，从上面给出的范围里存着实际的字节。也就是说，毕昇编译器生成 `.o` 时，这两块内容就已经写进文件了。节名里的 `aicore` 提供了 Device 侧的线索。要进一步看这些字节如何与 Host 侧的 `fatbinData`、`fatbinDataPtr` 和 `fatbinDataLength` 对应，先用 `readelf -W -s -C` 查看符号表中的 `Ndx`（所在节编号）。

```bash
obj=lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o
readelf -W -s -C "$obj" | grep -E '(^ *Num:| (main|hello_world|fatbinData(Ptr|Length)?|cceModuleCtor)$)'
```

```text
   Num:    Value          Size Type    Bind   Vis      Ndx Name
     2: 0000000000000000     0 NOTYPE  LOCAL  DEFAULT    3 fatbinData
     5: 0000000000000008     8 OBJECT  LOCAL  DEFAULT    5 fatbinDataPtr
     6: 0000000000000010     8 OBJECT  LOCAL  DEFAULT    5 fatbinDataLength
    23: 0000000000000668    12 FUNC    LOCAL  DEFAULT    1 cceModuleCtor
    56: 000000000000037c    64 FUNC    GLOBAL DEFAULT    1 hello_world
    57: 00000000000003bc   660 FUNC    GLOBAL DEFAULT    1 main
```

> [!TIP]
> **`readelf -W -s -C <文件>` 查看 ELF 符号表。**`-s` 列出符号，`-W` 使用宽格式，`-C` 把 C++ 修饰后的符号名还原成易读的形式。后面的 `grep` 只保留表头和本次关注的符号。
>
> - `Num` 是符号自己在符号表里的编号，`Name` 是它的名字。
> - `Value` 对这里列出的已定义符号表示从**所在节开头数**多少字节，按十六进制显示。`Size` 是符号表记录的大小，按十进制字节数显示。大小为 `0` 也可能表示未记录大小。注意这里是节内偏移，不是文件开始的偏移。
> - `Type` 是符号类型。`FUNC` 表示函数，`OBJECT` 表示数据对象，`NOTYPE` 表示未指定类型。
> - `Bind` 表示链接时这个名字的作用范围。`LOCAL` 限于当前目标文件，`GLOBAL` 可以参与跨文件链接。`Vis` 是符号的可见性，`DEFAULT` 表示采用默认规则。
> - `Ndx` 是符号所在节的编号。数字值直接对应上面节表的 `Nr`。例如，`fatbinData` 的 `Num` 是 2，`Ndx` 是 3，所以要查节表第 3 项 `.aicore_binary`。多个符号可以落在同一个节里，因此可以有相同的 `Ndx`。若看到 `UND`，则表示符号尚未定义，对应不到某个实际的节。

`main` 和 `hello_world` 的 `Ndx` 都是 1，对应外层 AArch64 ELF 的 `.text`。结合源码中 `main()` 在 Host 执行，可以把这个节里的两个函数符号都认作 Host 侧代码。

按同样的读法，`fatbinData` 的 `Ndx=3`、`Value=0`，正好落在 `.aicore_binary` 开头。另外两个数据符号 `fatbinDataPtr`、`fatbinDataLength` 位于第 5 节 `.data`，节内偏移分别是 `0x8` 和 `0x10`，中间的 8Bytes 刚好存放的是 `fatbinDataPtr` 的内容。`fatbinDataPtr` 指到哪里，要看链接器将来会给它填什么。用 `readelf -W -r` 查看重定位条目，再用 `readelf -W -x .data` 查看长度字段的原始字节。

```bash
readelf -W -r "$obj" | sed -n '/Relocation section .*rela.data/,/^$/p; /Relocation section .*rela__aicore_rel_rec/,/^$/p; /Relocation section .*rela.init_array/,/^$/p'
readelf -W -x .data "$obj"
```

> [!TIP]
> **`readelf -W -r <文件>` 查看重定位记录。**
> - `Offset` 表示要修改的位置，在这份 `.o` 中从被修改的节开头算起。
> - `Info` 编码了符号编号和重定位类型，`Type` 显示具体的计算和写入规则。
> - `Symbol's Value` 是符号表里记录的值，最后一列显示引用的符号和附加量。例如，`.rela.data` 中的 `Offset=0x8` 对应 `fatbinDataPtr` 所在的 `.data+0x8`，末尾的 `.aicore_binary + 0` 表示要写入 `.aicore_binary` 开头的地址。
> ****
> **`readelf -W -x .data <文件>` 用十六进制显示 `.data` 节的原始字节。** 
> - 在本次回显中，左边的 `0x00000010` 表示这一行从 `.data+0x10` 开始。
> - 中间的 `f01b0000 00000000` 是按文件顺序显示的 8 个字节，按小端序读成整数就是 `0x1bf0`（7152），也就是 `fatbinDataLength`。
> - 最右边是这些字节的字符预览，点号表示不可打印的字符。

重定位回显摘录如下，每组保留节名和对应条目。

```text
Relocation section '.rela.data' at offset 0x4b68 contains 1 entry:
0000000000000008  0000000f00000101 R_AARCH64_ABS64       0000000000000000 .aicore_binary + 0

Relocation section '.rela__aicore_rel_rec' at offset 0x4cc8 contains 1 entry:
0000000000000008  0000002000000101 R_AARCH64_ABS64       0000000000000000 __aicore_rel_binary + 0

Relocation section '.rela.init_array' at offset 0x4ce0 contains 1 entry:
0000000000000000  0000000e00000101 R_AARCH64_ABS64       0000000000000000 .text + 668
```

`.data` 的十六进制回显中，长度字段所在的这一行如下。

```text
  0x00000010 f01b0000 00000000                   ........
```

`.rela.data` 的第一列 `0x8` 是要填写的 `.data` 节内位置，恰好对应 `fatbinDataPtr`，而行末的 `.aicore_binary + 0` 是它要指向的位置。再看紧随其后的长度字段，`f0 1b 00 00 00 00 00 00` 按小端序读为 `0x1bf0`，和 `.aicore_binary` 的节大小一致。这样就把设备数据的起点和长度都对上了。

另外两条也可以按“在哪里填写、填向哪里”来读。`__aicore_rel_rec` 在节内 `0x8` 处引用 `__aicore_rel_binary` 开头。`.init_array` 的第一个条目引用 `.text+0x668`，与符号表里 `cceModuleCtor` 的位置一致。

到这里可以确认，链接前的 `.o` 已经把 Host 代码和设备数据放在不同的节里。下一节用 `demo` 的节表继续追踪这两块设备数据，比较链接前后的位置、大小和内容。

## 4. 看最终文件 `demo` 的节、动态依赖及设备数据开头

第 3 节在 `.o` 里找到了 `.aicore_binary` 和 `__aicore_rel_binary`。链接成 `demo` 后，这两个节还在吗？先用同一条 `readelf -W -S` 命令检查最终文件。

```bash
readelf -W -S lab/hello_world/results/npu-build/build/demo
```

节表摘录如下。

```text
There are 34 section headers, starting at offset 0x5c5c8:
  [Nr] Name              Type            Address          Off    Size   ES Flg Lk Inf Al
  [ 1] .interp           PROGBITS        00000000000002a8 0002a8 00001b 00   A  0   0  1
  [11] __aicore_rel_binary PROGBITS      0000000000008ef8 008ef8 001591 00   A  0   0  8
  [15] .text             PROGBITS        0000000000027250 017250 01aab4 00  AX  0   0 16
  [20] .init_array       INIT_ARRAY      0000000000052328 032328 000018 00  WA  0   0  8
  [22] .dynamic          DYNAMIC         0000000000052b40 032b40 000250 10  WA  7   0  8
  [26] .aicore_binary    PROGBITS        0000000000062f00 032f00 001bf0 00  WA  0   0 256
  [27] __aicore_rel_rec  PROGBITS        0000000000064af0 034af0 000018 00 WAo  0   0  8
```

两节都保留了原来的大小，但在文件中的位置变了。对照 `Off` 列，`.aicore_binary` 从 `0x700` 移到 `0x32f00`，大小仍是 `0x1bf0`。`__aicore_rel_binary` 从 `0x2698` 移到 `0x8ef8`，大小仍是 `0x1591`。`demo` 的节表里也能看到 `__aicore_rel_rec`。

大小相同之后，还要看内容。先用 `readelf -x` 对照两份产物的 `.aicore_binary` 开头。

```bash
readelf -W -x .aicore_binary lab/hello_world/results/npu-build/build/CMakeFiles/demo.dir/hello_world.cpp.o | head -13
readelf -W -x .aicore_binary lab/hello_world/results/npu-build/build/demo | head -10
```

第一段按 `.o` 中该节的文件偏移读取前 64 字节重放，第二段摘自此前保存的 `demo` 终端回显。

```text
Hex dump of section '.aicore_binary':
  0x00000000 7f454c46 02010100 00000000 00000000 .ELF............
  0x00000010 02002910 01000000 00000000 00000000 ..).............
  0x00000020 40000000 00000000 70180000 00000000 @.......p.......
  0x00000030 00009400 40003800 03004000 0e000c00 ....@.8...@.....
```

```text
Hex dump of section '.aicore_binary':
  0x00062f00 7f454c46 02010100 00000000 00000000 .ELF............
  0x00062f10 02002910 01000000 00000000 00000000 ..).............
  0x00062f20 40000000 00000000 70180000 00000000 @.......p.......
  0x00062f30 00009400 40003800 03004000 0e000c00 ....@.8...@.....
```

两段开头的 `7f 45 4c 46` 是 ELF 魔数，后面列出的字节也一致。左侧 `0x0` 和 `0x62f00` 来自各自节表的 `Address` 列。直接从文件提取整节时，要用前面查到的 `Off` 和 `Size`。此前按这两个字段读取完整字节并计算 SHA-256，结果如下。每行的摘要在 `.o` 和 `demo` 中一致。

```text
.aicore_binary       e0dd748b8847886b3cd13457b38753e32e2f5a6cb432520fa40dd8a34fa9a559
__aicore_rel_binary  0a958af6ce008216813ea5e6be330e94a06dadc301184dd9e78625a9e1a3e944
```

结合偏移和摘要可以看出，这次链接把两块设备数据放到了 `demo` 的新位置，同时保留了它们的字节内容。`.aicore_binary` 以 ELF 头开头，和外层 AArch64 Host 代码所在的 `.text` 分列两节。

设备数据的位置和内容对照完了，再回到 Host 侧。第 3 节中有些调用在 `.o` 里标为 `U`。链接成 `demo` 后，这些符号是否已有定义？用 `nm -C` 再查一次。

```bash
nm -C lab/hello_world/results/npu-build/build/demo
```

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

`AscendGetFuncFromBinary` 和 `AscendLaunchKernelWithHostArgs` 在 `.o` 中是 `U`，在 `demo` 中变成 `t`，说明最终文件已经包含它们的局部代码定义。`aclInit`、`aclrtBinaryLoadFromData` 等在 `demo` 中仍是 `U`。这些未定义引用引出了下一个问题：最终文件声明了哪些动态库依赖？

```bash
readelf -W -d lab/hello_world/results/npu-build/build/demo
```

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

`NEEDED` 列出了 `demo` 的直接动态库依赖。这里既有 CANN 的 `libascendcl.so`、`libruntime.so`，也有 Host 侧的 `libc.so.6`、`libstdc++.so.6`。这些库为运行时解析外部引用提供依赖。`FLAGS_1` 中的 `PIE` 也与第 2 节核对的结果相同。

到这里，已经从产物看到链接后的两种变化：设备数据在最终 ELF 里换了位置，Host 侧的一些符号已有定义，另一些仍由动态链接处理。下一节回到构建日志，把这些变化对应到毕昇的两次调用。

## 5. 构建日志与阶段判断

前面从产物看到，`.o` 已经包含 Host 代码和设备数据，链接后的 `demo` 也保留了这两块设备数据。现在回到日志，按生成顺序把这些观察和构建命令对应起来。`configure.log` 的末尾记录了配置完成、生成规则以及规则的写入位置。

```text
-- Configuring done
-- Generating done
-- Build files have been written to: /mnt/workspace/ai-kernel-101/lab/hello_world/results/npu-build/build
```

这就是第 1 节查看的 `build.make`、`flags.make` 和 `link.txt` 所在的构建目录。规则生成后，实际执行了哪些命令？给 `build.log` 加上行号，查看编译到链接的这段日志。

```bash
nl -ba lab/hello_world/results/npu-build/build.log | sed -n '11,17p'
```

回显摘录如下，保留原行号，略去第 16 行的 Make 退出目录提示。

```text
    11  [ 50%] Building ASC object CMakeFiles/demo.dir/hello_world.cpp.o
    12  /home/developer/Ascend/cann-9.1.0/bin/bisheng    -std=c++17 --npu-arch=dav-2201 --npu-arch=dav-2201 -MD -MT CMakeFiles/demo.dir/hello_world.cpp.o -MF CMakeFiles/demo.dir/hello_world.cpp.o.d -o CMakeFiles/demo.dir/hello_world.cpp.o -c --asc-aicore-lang /mnt/workspace/ai-kernel-101/lab/hello_world/src/hello_world.cpp
    13  [100%] Linking ASC executable demo
    14  /opt/buildtools/cmake-3.20.5-linux-aarch64/bin/cmake -E cmake_link_script CMakeFiles/demo.dir/link.txt --verbose=1
    15   /home/developer/Ascend/cann-9.1.0/bin/bisheng  --npu-arch=dav-2201 CMakeFiles/demo.dir/hello_world.cpp.o -o demo
    17  [100%] Built target demo
```

先看第 11、12 行。第一条毕昇命令读取 `hello_world.cpp`，用 `-c` 编译到 `-o` 指定的 `hello_world.cpp.o`，同时按 `-MF` 指定的路径写出 `.o.d`。这就是第 2 节里 `file` 识别为可重定位 ELF 的那个文件。第 3 节又在这个文件中找到了 Host 的 `.text` 和设备相关的节，因此到第一次调用结束时，Host 代码和设备数据已经同在一个目标文件里。

接着看第 13–17 行。CMake 执行 `link.txt`，第二条毕昇命令把前一步的 `.o` 作为输入，用 `-o demo` 指定输出，随后 Make 报告构建完成。第 4 节对照的节表和摘要对应的就是这一步前后的两个文件。这次链接调整了两块设备数据的文件偏移，保留了它们的字节内容。

构建日志记录到了两次毕昇调用这一层。按 C/C++ 的阶段划分，第一次调用涵盖从预处理到生成目标文件的过程。至于预处理、编译和汇编各自如何执行，需要查看毕昇的内部子命令或中间产物。

因此，从日志和产物可以确认，这次构建先从源码生成包含 Host 代码和设备数据的 `.o`，再链接出 `demo`。第一部分的运行记录进一步确认，`demo` 在云端 NPU 环境运行后输出了 8 个 AIV Block 的 Hello World。
