# 主题一

**从 C/C++ 编译模型进入 NPU 异构编译**。

细分成四个问题：
1. **源码如何分流？** 编译器怎样识别 Host 代码、Kernel 入口和 `<<<>>>` 启动语法？
2. **各自编译成什么？** Host 面向 x86-64/AArch64，Device 面向指定的 `dav-2201` 架构，两者是什么关系？
3. **二进制怎样组织？** 目标文件、Fatbin、可执行程序之间的区别是什么？
4. **谁真正加载 Kernel？** 编译完成不等于执行。Runtime 如何将 Host 提交的任务交给 Device？

实际操作：
在 hello world 程序上，**分析真实编译产物**，可以使用工具包括：
- `readelf` 能分析 ELF 结构，但不能保证直接解析内部设备代码；
- 结合 CANN 提供的 `msobjdump` 等工具确认。

区分编译器前端、代码生成、链接器与运行时。不要把这些不同阶段统称为“编译”。最终建立**一张由真实构建日志和二进制检查结果支撑的 Ascend C 编译链路图。**


# 从 C/C++ 编译到 Ascend C 异构执行

用普通 C 程序作参照：预处理展开头文件和宏，编译与汇编生成面向 Host 的目标文件，链接得到可执行文件。运行时由操作系统和动态加载器装载 Host 程序及其共享库。Ascend C 的区别从编译目标开始，同一源文件可以同时描述 Host 控制流程与设备 Kernel。

| 环节 | 当前样例中的线索 | 还需核对 |
| --- | --- | --- |
| 源码识别 | CMake 用 `LANGUAGE ASC` 处理 `hello_world.cpp`。`main()` 是 Host 入口，`__global__ __vector__` 标记 Vector Kernel，`<<<8, 0, stream>>>` 在 Host 侧发起启动。 | 记录 CMake 实际调用的编译驱动及编译参数。 |
| 分目标编译 | Host 代码面向当前主机架构。NPU 路径的设备目标由 `--npu-arch=dav-2201` 指定。 | 保存实际 Host 和设备目标参数。驱动只打印一条命令时，再查询其支持的子命令显示选项。 |
| 封装与链接 | 官方的 AI Core SIMD 通用流程先封装设备二进制，再与 Host 部分合成可执行文件。 | 样例只有 Vector Kernel，检查实际存在的设备成员、入口和容器位置。 |
| 加载与执行 | Linux 启动 `demo` 的 Host 代码。Host 初始化 ACL、创建 Stream、提交 Kernel，再用 `aclrtSynchronizeStream` 等待完成。 | 通过符号、调用点或调试观察确认本版生成的启动桥接与 Runtime 调用。加载发生在哪一步，取决于实际证据。 |

依据：[CANN 9.1.X 毕昇编译器](https://www.hiascend.com/doc_center/source/zh/CANNCommunityEdition/910/compiler/BishengCompiler/atlas_bisheng_10_0001.html)、[Ascend C AI Core 编译基本用法](https://asc.gitcode.com/guide/programming_guide/compilation_and_execution/operator_compilation/ai_core_operator_compilation.html)、[CANN 9.1.X Runtime 显式同步](https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/910/others/acldevg/runtime_doc_dev_0014.html)。开发版文档描述通用流程，样例实现见 [CMakeLists.txt](../../lab/hello_world/src/CMakeLists.txt) 和 [hello_world.cpp](../../lab/hello_world/src/hello_world.cpp)。

## 取证顺序

1. 在同一个 x86-64 WSL 环境中构建 CPU、SIM、NPU 三个版本。已有 `Lab01-NEG` 记录表明当时无卡也能完成 NPU 模式构建。真机执行证据可沿用历史报告，新的真机对照只在有需要时做。
2. 每种模式使用独立构建目录。保留配置日志和 `cmake --build <build-dir> --verbose` 的编译、链接命令及产物清单。若构建日志只出现驱动命令，先核实该版本支持的详细输出选项，再沿原命令追踪子阶段。
3. 对 `demo` 与相关目标文件运行 `file` 和 `readelf -h -S -d -sW`。ELF 头记录外层程序面向的 CPU 架构，节表、动态依赖、符号表提供寻找封装与启动桥接的线索。动态依赖表仅覆盖链接时记录的依赖。
4. 如已安装 `msobjdump`，先用 `--help` 核对输入格式与选项，再试相关算子产物。工具拒绝外层 `demo` 时，检查构建时能保留的设备侧中间产物，并保留工具的错误输出。记录成功识别的成员和 Kernel 名称，再画构建链路图。[CANN 算子直调产物说明](https://asc.gitcode.com/guide/programming_guide/appendix/kernel_direct_call_from_sample.html)

交叉核对：`bisheng --version` 中的 Host target 用于描述驱动的主机目标，设备目标取自实际构建命令和可解析的设备产物。历史功能成功日志只能说明启动流程走通，当前还缺设备封装布局和桥接符号的直接证据。
