
# 主题三

**Fat Binary（Fatbin，胖二进制）** 是 Ascend C 已有的机制，类似 CUDA。在源码和机器指令之间，还有中间层吗？是什么？

官方承认了 “AscendNPU IR”，[AscendNPU IR](https://gitcode.com/Ascend/AscendNPU-IR/blob/master/docs/source/zh_cn/introduction/introduction.md)，可以再深入探讨。

通过这个项目深入，建立三种能够迁移到其他 AI 计算平台的能力：
- **第一，理解异构程序的构建和执行。**
- **第二，知道如何透过抽象层观察程序。**
- **第三，识别自己的优化控制边界。**

# 胖二进制、设备中间表示与优化接口

这里要找的是 **fat binary（fatbin，胖二进制）**。Fat tree 是互连网络拓扑。判断昇腾是否有与 PTX 类似的能力时，需要分别看设备代码如何打包、编译中间表示能否由开发者直接输入，以及运行时的加载方式。

| 能力 | CUDA | 昇腾公开资料能确认的范围 |
| --- | --- | --- |
| 设备代码打包 | CUDA fatbin 可容纳 PTX、cubin 等设备代码。 | 毕昇的 AI Core SIMD 通用流程将设备侧二进制封装成 Fatbin，并与 Host 部分合成。当前样例实际封装的成员和位置待取证。 |
| 编写较低层的设备程序 | PTX 是公开的虚拟指令集，支持单独编写，也支持在 CUDA C++ 中内联。 | AscendNPU IR 提供可直接编写的 MLIR/HIVM。公开的向量加示例中，`bishengir-compile` 将 `.mlir` 编译为设备目标文件，Host 再通过 CANN Runtime 注册并启动。 |
| 从源代码控制设备执行细节 | 可通过内联 PTX 指定特定操作，最终机器码由工具链生成。 | 可在 Ascend C 中用目标平台支持的低层 API 表达数据搬运、同步及部分指令粒度的计算。例如 CANN 9.1.X 的 `RegTensor` 文档列出寄存器矢量接口的适用产品，使用前应按具体产品核对。 |

依据：[CUDA nvFatbin](https://docs.nvidia.com/cuda/nvfatbin/)、[CUDA Inline PTX](https://docs.nvidia.com/cuda/inline-ptx-assembly/)、[Ascend C AI Core 编译](https://asc.gitcode.com/guide/programming_guide/compilation_and_execution/operator_compilation/ai_core_operator_compilation.html)、[AscendNPU IR 编译运行示例](https://ascendnpu-ir.gitcode.com/en/introduction/quick_start/examples.html)、[CANN 9.1.X RegTensor](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/reg_vector_compute/register_data_types/RegTensor.md)。

AscendNPU IR 的公开示例支持“手写 IR → 编译 → Runtime 加载设备二进制”这条路径。当前尚无本样例经过同一公开 HIVM 输入路径的构建证据。也需要独立资料才能确认 CANN 是否提供具备 PTX 式内联、跨架构兼容及 Runtime JIT 的统一设备接口。

DeepSeek-V3 技术报告 §3.2.2 提到在跨节点通信 Kernel 中使用定制 PTX 指令和自动调整通信分块，目标涉及 L2 Cache 使用和对其他 SM 的干扰。这个案例提出了一个可迁移的问题：当源码层无法表达所需的硬件行为时，工具链是否提供更低层的控制。若要在昇腾上验证这类能力，可从有明确输入、输出和数据搬运的向量加开始，固定目标与功能，先观察编译产物或仿真追踪，再评估真机性能。[DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437)
