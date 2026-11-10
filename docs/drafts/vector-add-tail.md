---
series: AI Kernel 101：从 Hello World 到 Flash Attention 的 Ascend C 实践
title: 数据放不下怎么办？从一个 Kernel 理解 Tiling
aliases:
  - 第 04 篇：Tiling、尾块与对齐
  - 从固定长度到任意长度：Vector Add 的尾块与对齐
writing_status: 草稿补充中；核内循环实现与 NPU 验证待完成
publication_status: 未发布
---

> 状态：容量与划分部分为推导；尾块代码为现有练习；核内循环版本待实现，真机功能与性能验证待完成。
> 历史环境叙述沿用第03篇的 CANNLab A3（910C、`aarch64`）、CANN 9.1.0、`dav-2201`。这些字段的对应关系仍需核对，不代表本篇已在该环境执行新实验。

> 现有 CPU 验证摘要与本篇真机计划分开记录；“待实现”“待验证”不表示已有运行结果。

# 一、为什么固定长度样例还不够

[第03篇](vector-add.md)保留了静态 Tensor 和 TPipe/TQue 两种写法：8 个 Block 各处理 2048 个 `float`，总长恰好为 16384。两版都为每个 Block 的全部输入与输出一次准备局部缓冲，显式数据空间是 $3\times2048\times4=24576$ 字节，即 24 KiB。

如果输入继续增大，是否也要按比例增加每个 Block 的 UB 申请量？如果只增加 Block 数，每个任务仍处理 2048 个元素，是否就等于解决了分块问题？另外，总长不是整块的倍数时，剩下的数据又该交给谁？

这些问题需要一起考虑。分块（Tiling）既要把所有有效元素完整覆盖，也要让每次计算的活动数据放得下，并满足搬运接口的边界要求。分得更细还会增加循环、地址计算和阶段交接的次数；块大小因此是资源容量与执行开销之间的选择。

先建立覆盖与容量模型，再回看已有的两个尾块练习。它们基于 [CANN Samples 基础样例](https://gitcode.com/cann/cann-samples/blob/3a85e824537feaef646bd89eb4d0e799cc2886b5/Samples/0_Introduction/01_simd_cpp_api/01_add/add/add.asc) 衍生，完整代码分别在 [`03_uneven_split`](../../src/vector_add/03_uneven_split/README.md) 与 [`04_arbitrary_length`](../../src/vector_add/04_arbitrary_length/README.md)。两者都还没有核内多轮循环，不能用现有尾块实现代替后文计划中的完整 Tiling 版本。

# 二、分给谁，与一次放多少，是两层划分

## 先把输出区间分给逻辑 Block

设总长度为 $L$，下标范围为 $[0,L)$。Host 为非空输入选择 $B$ 个逻辑 Block，每个 Block 负责连续且互不重叠的输出区间。$B$ 是启动的任务数量，不直接等于物理核数；具体并发与调度仍由目标设备及运行时决定。

为了让 FP32 数据的各段起点尽量满足 32 字节对齐，先以 8 个元素为一组划分。设：

$$
U=\lceil L/8\rceil,\qquad 1\le B\le U.
$$

$U$ 是覆盖输入所需的对齐组数，最后一组可以不满。给第 $b$ 个 Block（$0\le b<B$）安排：

$$
s_b=8\left\lfloor\frac{bU}{B}\right\rfloor,\qquad
e_b=\min\left(L,8\left\lfloor\frac{(b+1)U}{B}\right\rfloor\right),\qquad
n_b=e_b-s_b.
$$

这里 $s_b$ 是起点，$e_b$ 是右开终点，$n_b$ 是有效元素数。相邻区间满足 $e_b=s_{b+1}$，首段从 0 开始，末段在 $L$ 结束，因此没有遗漏也没有交叠。取 $B\le U$，避免分配没有有效元素的任务；$L=0$ 时由 Host 返回空结果，不启动 Kernel。

这是一种待实现的划分方案，不是现有尾块源码已经采用的公式。它还要求 GM 基址本身满足所用接口的地址约束。实现时需用足够宽的整数完成乘法、字节数和偏移计算，并分别检查容器长度、Kernel 参数范围与允许的启动规模，不能让整数溢出破坏覆盖关系。

## 再把一个 Block 的区间切成可重复处理的 Tile

令 $T>0$ 表示每个 Tile 最多处理的元素数。第 $b$ 个 Block 需要：

$$J_b=\lceil n_b/T\rceil$$

轮循环。第 $j$ 轮（$0\le j<J_b$）的全局起点与有效长度为：

$$
o_{b,j}=s_b+jT,\qquad
t_{b,j}=\min(T,n_b-jT).
$$

该轮处理 $[o_{b,j},o_{b,j}+t_{b,j})$。前一轮的终点恰好是下一轮的起点，最后一轮在 $e_b$ 结束，所以核内循环也保持完整覆盖。选择 $T$ 为 8 的倍数时，中间各轮的起点仍按 FP32 的 32 字节粒度对齐；最后一轮的有效字节数则需要另行检查。

以 **$L=1000000$、$B=8$、$T=2048$ 为理论例子**：每个 Block 负责 125000 个元素，先处理 61 个完整 Tile（共 124928 个元素），再处理 72 个元素的尾 Tile。任务负责的数据规模远大于一次缓冲容量，但可以复用同一组局部缓冲完成 62 轮处理。

```text
全局输出 [0, L)
  ├─ Block 0：自己的连续区间 → Tile 0 → Tile 1 → … → 尾 Tile
  ├─ Block 1：自己的连续区间 → Tile 0 → Tile 1 → … → 尾 Tile
  └─ 其余 Block：同样在各自区间内循环

单缓冲的每轮顺序：搬入 → 计算 → 写回 → 确认可复用 → 下一轮
```

图描述的是设计顺序，不是实际硬件时间线。只不断增加逻辑 Block 数、每个 Block 仍只处理一块数据，是另一种任务组织方式；它可能适合某些规模，但没有展示在固定局部容量下进行核内多轮计算的过程。接下来我们关注后者。

# 三、块大小必须服从同时存活的数据

## 先列容量，再选参数

对当前不覆盖输入的 FP32 Add，一轮需要两份输入和一份输出。设 $a(x)=32\lceil x/32\rceil$，表示将字节数向上补齐到 32 字节；三个队列分别保留 $q_x,q_y,q_z$ 份缓冲，其他仍需计入的临时空间为 $R$，则数据与临时空间预算为：

$$C(T)=(q_x+q_y+q_z)\,a(4T)+R\le M_{\mathrm{avail}}.$$

$M_{\mathrm{avail}}$ 是已按目标环境扣除框架／编译器预留后的可用预算，不能拿未经核对的物理 UB 总量直接代入；$R$ 则包含尚未计入该预算的内部缓冲、对齐空隙和本 Kernel 临时数据，避免遗漏或重复扣除。实际约束还包括队列可用事件等资源，字节数通过只是必要条件。

在 $T$ 是 8 的倍数、三份缓冲都只有一份时，数据部分是 $12T$ 字节。若三份都配置两份缓冲，数据部分成为 $24T$，但是否形成有效重叠另需验证。TPipe 队列版用 `InitBuffer` 的缓冲块数配置份数，它与 `TQue` 的队列深度不同〔4〕。

| Tile 元素数 $T$ | 每份 FP32 数据缓冲 | 三份单缓冲合计 | 三份各配两份的合计 |
| ---: | ---: | ---: | ---: |
| 2048 | 8 KiB | 24 KiB | 48 KiB |
| 4096 | 16 KiB | 48 KiB | 96 KiB |
| 8192 | 32 KiB | 96 KiB | 192 KiB |

表格只计算数据缓冲，不含 $R$，也不是实测占用。最后一列仅展示容量如何变化，不表示本篇已经实现双缓冲。

例如，**假设**可用预算为 128 KiB，另需预留 8 KiB 临时空间，单缓冲的理论上限就是 $T\le(128-8)\times1024/12=10240$ 个元素。这里的 128 KiB 和 8 KiB 只是说明计算方法的假设，不能当成目标设备的实查数值或最终参数。

静态 Tensor 版可以把三块 Tile 缓冲放在循环之外申请，队列版可以在循环外初始化队列、在每轮取得和释放 Tensor。两种方式都应复用有限空间，不能每轮继续线性追加申请。队列版还要遵守第03篇的交接协议：输入被计算消费、输出被搬出后，缓冲才能按资源管理规则重新使用。

## 有效长度与实际容纳空间不同

尾 Tile 的数学有效长度是 $t$，搬运到 UB 后占用的空间还可能需要补齐。以 1001 个 FP32 元素为例，有效数据占 4004 字节，对齐后的容量是 4032 字节，即 1008 个元素的位置。

申请足够空间，不表示可以读到 GM 输入范围之外；也不表示补齐位置都是零。向量加可以只计算前 $t$ 个有效元素，再只写回对应输出。对于后面的归约，补齐值可能改变最大值或求和结果，必须另外选择合适填充值或屏蔽策略，不能把 Add 的边界处理原样推广到 Softmax。

容量模型确定的是“放得下”，覆盖模型确定的是“不漏不重”。还剩最后一个检查：实际使用的搬运接口能否表达这个有效长度。下面保留的两个练习，分别检查对齐尾块与非对齐尾块。

## 现有尾块练习的复现准备

下面命令在同一云端 Shell 执行；先准备环境和基础版源码。此处代码编辑步骤保留原文，改动都在临时副本中进行。

```bash
repo=/mnt/workspace/ai-kernel-101
if [ ! -d "$repo/.git" ]; then
  git clone https://github.com/LamberttLiu/ai-kernel-101 "$repo"
fi
source /home/developer/Ascend/ascend-toolkit/set_env.sh
sample="$repo/src/vector_add/00_basic"
```

# 四、尾块一：让最后一个 Block 处理较短片段

第03篇分析的是**未修改的原始样例**：8 个 Block 各处理 2048 个元素，总长 16384。现在单独制作一个练习副本，使前 `N-1` 个 Block 的工作量相同，第 `N` 个 Block 只处理剩余元素。不要直接改仓库里的原始 `add.cpp`，以便保留前面章节的基准结果。

## 4.1 先确定切分规则

设每个完整 Block 处理 `B=2048` 个 `float`，总长 `L=7×2048+1000=15336`，则 `N=⌈L/B⌉=8`。各 Block 的起点为 `offset = block_idx × B`，本 Block 的实际长度为 `currentLength = min(B, L-offset)`：

| `block_idx` | 起点 `offset` | 实际长度 `currentLength` | GM 元素区间 |
| ---: | ---: | ---: | --- |
| 0～6 | `block_idx × 2048` | 2048 | 各自不重叠的完整片段 |
| 7 | 14336 | 1000 | `[14336, 15336)` |

尾块先选 **1000 个 `float`**：`1000×4=4000` 字节，恰好是 32 字节的整数倍，满足本例连续 `DataCopy` 的搬运对齐要求〔1〕。这里暂不处理尾长为 1001 等不满足该条件的情况；要覆盖任意元素数，需要另行设计非对齐尾块搬运。

## 4.2 修改临时副本中的 Host

在云端复制现有样例工程；`sample` 已在本篇开头指向基础版源码：

```bash
tailWork="$(mktemp -d /tmp/ascend-add-tail-XXXXXX)"
cp -a "$sample" "$tailWork/sample"
```

只编辑 `"$tailWork/sample/add.cpp"`。先将 `main` 中的总长改为：

```cpp
constexpr uint32_t totalLength = 7 * 2048 + 1000;
```

然后在 `kernel_add` 中保留 `blockLength=2048`，根据实际总长计算 Block 数，并把总长作为第四个 Kernel 实参传入：

```cpp
constexpr uint32_t blockLength = 2048;
uint32_t totalLength = x.size();
uint32_t numBlocks = (totalLength + blockLength - 1) / blockLength;
// 原有 aclrtMalloc、输入拷贝等代码保持原样。
add_custom<blockLength><<<numBlocks, 0, stream>>>(
    xDevice, yDevice, zDevice, totalLength);
```

此处 `numBlocks` 是逻辑 Block 数。对本次 `L=15336`，向上取整得到 8；输入长度应为正数，且 `x`、`y` 长度一致。本练习的 `main` 已构造满足条件的两个向量。

## 4.3 修改 Kernel 的实际处理长度

将 Kernel 函数签名增加 `uint32_t totalLength`，在 `InitSocState()` 后计算当前 Block 的 `offset` 和 `currentLength`。用 `currentLength` 绑定 GM 片段，并作为 `DataCopy`、`Add` 的本核实际运算元素数：

```cpp
template <uint32_t blockLength>
__vector__ __global__ void add_custom(
    __gm__ float* x, __gm__ float* y, __gm__ float* z, uint32_t totalLength)
{
    AscendC::InitSocState();
    const uint32_t offset = block_idx * blockLength;
    // 本核的实际运算元素数目
    uint32_t currentLength = (totalLength - offset) <= blockLength ? (totalLength - offset) : blockLength;

    AscendC::GlobalTensor<float> xGm, yGm, zGm;
    xGm.SetGlobalBuffer(x + offset, currentLength);
    yGm.SetGlobalBuffer(y + offset, currentLength);
    zGm.SetGlobalBuffer(z + offset, currentLength);

    AscendC::LocalMemAllocator<AscendC::Hardware::UB> ubAllocator;
    AscendC::LocalTensor<float> xLocal = ubAllocator.Alloc<float, blockLength>();
    AscendC::LocalTensor<float> yLocal = ubAllocator.Alloc<float, blockLength>();
    AscendC::LocalTensor<float> zLocal = ubAllocator.Alloc<float, blockLength>();

    AscendC::DataCopy(xLocal, xGm, currentLength);
    AscendC::DataCopy(yLocal, yGm, currentLength);
    AscendC::PipeBarrier<PIPE_ALL>();
    AscendC::Add(zLocal, xLocal, yLocal, currentLength);
    AscendC::PipeBarrier<PIPE_ALL>();
    AscendC::DataCopy(zGm, zLocal, currentLength);
    AscendC::PipeBarrier<PIPE_ALL>();
}
```

这一行三元表达式等价于取 `min(totalLength - offset, blockLength)`；等于 `blockLength` 时选哪一支，结果都相同。它成立的前提是 `blockLength > 0`、`totalLength > 0`，且 Host 按 `numBlocks = ⌈totalLength / blockLength⌉` 启动，保证每个已启动 Block 的 `offset < totalLength`。若在其他场景中额外启动了 `offset >= totalLength` 的 Block，`uint32_t` 减法会下溢，不能直接使用此写法。

最后一个 Block **仍按 `blockLength` 为三个 `LocalTensor` 各准备 2048 元素的 UB 容量，但只搬运和计算 `currentLength=1000` 个元素**。

容量与实际工作量不同；把 `SetGlobalBuffer`、`DataCopy`、`Add` 都改为实际长度，才不会让尾核读取或写入输入范围之外的数据。前 7 个 Block 的 `currentLength` 仍为 2048。

## 4.4 在 NPU 上编译并核对短尾块

完成上述编辑后，在云端以 `npu` 模式构建临时副本：

```bash
cmake -S "$tailWork/sample" -B "$tailWork/build-npu" \
  -DCMAKE_ASC_RUN_MODE=npu \
  -DCMAKE_ASC_ARCHITECTURES=dav-2201 \
  -DCMAKE_PREFIX_PATH="$ASCEND_HOME_PATH"
cmake --build "$tailWork/build-npu" --parallel 4
"$tailWork/build-npu/demo"
echo "exit=$?"
```

检查 `test pass!` 和退出码 0。`VerifyResult` 用 `std::equal` 比较完整的 15,336 个结果，虽然终端只展示前 20 项，尾块也包含在比较范围内。此练习解决的是**长度对齐但工作量不均匀**的尾核；它尚未解决非对齐尾块。仓库中的完整实现见 [`03_uneven_split`](../../src/vector_add/03_uneven_split/README.md)。

# 五、尾块二：处理非 32 字节对齐的长度

进阶一的尾长 1000 个 `float`，即 4000 字节，满足连续 `DataCopy` 的 32 字节对齐要求。若改为 `L=7×2048+1001=15337`，最后一个 Block 的 1001 个 `float` 只占 **4004 字节**，无法被 32 整除。继续使用第四节的 `DataCopy(..., currentLength)`，就不能保证尾部完整搬运；本节改用非对齐搬运接口 `DataCopyPad`〔2、3〕，目标 A3 环境的具体适用约束仍需核实。

## 5.1 在进阶一的副本上继续修改

先完成第四节，再复制一份已经实现不均匀切分的样例。以下命令假定 `tailWork` 仍是第四节创建的变量：

```bash
anyWork="$(mktemp -d /tmp/ascend-add-anylen-XXXXXX)"
cp -a "$tailWork/sample" "$anyWork/sample"
```

只编辑 `"$anyWork/sample/add.cpp"`。保留第四节的 `offset`、`currentLength`、GM 片段绑定和 Host 传入 `totalLength` 的逻辑；把 Kernel 中原来的三次 `DataCopy` 替换为下列调用，`Add` 及三个 `PipeBarrier` 保持原有顺序：

```cpp
// blockCount=1；blockLen 按字节指定；两个 stride 和保留字段均为 0。
AscendC::DataCopyExtParams copyParams{
    1, static_cast<uint32_t>(currentLength * sizeof(float)), 0, 0, 0};
AscendC::DataCopyPadExtParams<float> padParams{false, 0, 0, 0.0f};

AscendC::DataCopyPad(xLocal, xGm, copyParams, padParams); // GM → UB
AscendC::DataCopyPad(yLocal, yGm, copyParams, padParams); // GM → UB
AscendC::PipeBarrier<PIPE_ALL>();
AscendC::Add(zLocal, xLocal, yLocal, currentLength);
AscendC::PipeBarrier<PIPE_ALL>();
AscendC::DataCopyPad(zGm, zLocal, copyParams);             // UB → GM
AscendC::PipeBarrier<PIPE_ALL>();
```

`DataCopyExtParams` 的 `blockLen` 单位是**字节**，与连续 `DataCopy` 的 `count` 单位（元素）不同。本例 `currentLength=1001` 时，`blockLen=4004`。`sizeof(float)` 的结果类型是 `size_t`；`blockLen` 字段为 `uint32_t`，这里显式转换是为了避免列表初始化的窄化编译错误。`padParams` 关闭自定义填充值，左右额外填充数设为 0；GM→UB 的搬运会在 UB 侧将不足 32 字节的部分补成完整数据块，**加法只使用前 `currentLength` 个有效元素**。UB→GM 的 `DataCopyPad` 只写回指定的 4004 字节，不把用于对齐的 dummy 数据写出。

尾块需要在 UB 中容纳对齐后的 `⌈4004/32⌉×32=4032` 字节，即 1008 个 `float` 位置；第四节保留的 `Alloc<float, blockLength>()` 提供 2048 个位置，因此足够。本练习为了先验证功能，让完整块和尾块都走 `DataCopyPad`；暂不比较它与完整块使用 `DataCopy` 的性能。

## 5.2 让同一个程序接收不同长度

在 `add.cpp` 的头文件区增加 `#include <cstdlib>`。将 `main` 里的固定总长改为可从命令行读取的非负十进制数；不传参数时默认测试 15337：

```cpp
uint32_t totalLength = argc > 1
    ? static_cast<uint32_t>(std::strtoul(argv[1], nullptr, 10))
    : 7 * 2048 + 1001;
```

`main` 其余构造 `x`、`y`、`golden` 的代码保持原样。在 `kernel_add` 的函数体开头加入：

```cpp
if (x.empty()) {
    return {};
}
```

空向量直接由 Host 返回，不启动 Kernel，也不调用零字节的 ACL 分配。非空向量沿用第四节的 `numBlocks = (totalLength + blockLength - 1) / blockLength`。这个命令行入口只用于本练习，测试参数需为 `uint32_t` 范围内的非负十进制数；生产代码应另外检查解析错误及两个输入的长度是否相同。

## 5.3 在 NPU 上检查不同尾长

仍在同一云端 Shell 中，以 `npu` 模式构建非对齐版本，并逐个传入待检查的元素数：

```bash
cmake -S "$anyWork/sample" -B "$anyWork/build-npu" \
  -DCMAKE_ASC_RUN_MODE=npu \
  -DCMAKE_ASC_ARCHITECTURES=dav-2201 \
  -DCMAKE_PREFIX_PATH="$ASCEND_HOME_PATH"
cmake --build "$anyWork/build-npu" --parallel 4

for n in 1 7 8 9 1001 2048 2049 15337; do
  printf 'length=%s\n' "$n"
  "$anyWork/build-npu/demo" "$n"
done
```

各长度对应的分核与尾部搬运边界如下。每次运行都应独立检查 `test pass!` 与退出码，不能把下表当作已采集的实测结果。

| 总长 `L` | Block 数 | 最后一个 Block 的有效元素 | 尾部字节数 |
| ---: | ---: | ---: | ---: |
| 1、7、8、9 | 1 | 分别为 1、7、8、9 | 4、28、32、36 |
| 1001 | 1 | 1001 | 4004 |
| 2048 | 1 | 2048 | 8192 |
| 2049 | 2 | 1 | 4 |
| 15337 | 8 | 1001 | 4004 |

`VerifyResult` 比较整个输出向量，终端只打印前 20 项；因此要以完整比对的结果判断尾块是否正确。参数 `0` 在 Host 侧直接返回空向量，不会启动 NPU Kernel，故未列入本节的设备运行用例。这里的“任意长度”指**在样例可分配内存、`uint32_t` 计数和可启动 Block 范围内，不再要求尾长满足 32 字节对齐**，并不表示已验证无限大的向量。仓库中的完整实现见 [`04_arbitrary_length`](../../src/vector_add/04_arbitrary_length/README.md)。

# 六、核内多轮实现：预留位置

## 6.1 静态 Tensor 单缓冲循环

**待实现。** 在独立源码中实现第二节的 Block／Tile 划分，循环外申请三块容量为 $T$ 的 UB 缓冲，循环内按实际起点和 $t_{b,j}$ 完成搬入、计算、写回与安全复用。完整块和尾块的接口选择、同步及地址约束需逐项核对。保留现有基础版和两份尾块练习，不把它们改名当作已完成的多轮版本。

## 6.2 TPipe/TQue 单缓冲循环

**待实现。** 沿用第03篇的三个队列，在循环外按 Tile 字节数初始化，每轮进行输入分配／入队／出队、计算、输出入队／出队与释放。先保证单缓冲正确，不在这里直接加入双缓冲或宣称阶段重叠。正文届时只补必要循环片段，完整实现与构建入口放 src。

# 七、NPU 实验：预留问题与结果位置

本节是实验计划，尚未取得新真机数据。先固定输入、预期与判据，再在匹配环境中运行；目前所有结果栏均保留待办状态。

## 7.1 环境、接口与构建核对

**待验证。** 记录实际 SoC、驱动／固件、CANN、编译器、编译目标、选项、代码版本和支持接口。历史 A3／910C／dav-2201 字段不能代替本轮实查。两种核内循环版本尚未实现，因此相应 NPU 构建也未执行。

## 7.2 分核、分块和尾部正确性

**待实现／待验证。** 核对全量输出，不以终端前 20 个数代替检查；配合可用的越界检查工具或受保护输出区域，另查读写边界。对于确定的有限 FP32 Add 输入，先固定逐元素比较标准，并确认参考与设备的计算语义可比，不在看到误差后放宽门槛。

| 用例 | 要检查什么 | 当前结果 |
| --- | --- | --- |
| $L=0$ | Host 返回空结果，不启动零工作量 Kernel | 新多轮版本待实现；NPU 不适用 |
| $L=1,7,8,9$ | 短输入、对齐边界及有效长度 | 多轮版本待实现，真机待验证 |
| $L=T-1,T,T+1$ | 一个 Tile 的前后边界与第二轮起点 | 待实现／待验证 |
| $L=BT-1,BT,BT+1$，按选定划分计算各 $n_b$ | 核间分配与 Tile 数共同变化 | 待实现／待验证 |
| $L=15336,15337$ | 对齐／非对齐尾块，覆盖现有练习 | 现有源码可查，本篇目标 NPU 记录待补 |
| $L=1000000$，示例 $B=8,T=2048$ | 局部缓冲复用 62 轮，覆盖完整输出 | 理论设计；实现及 NPU 验证待完成 |
| 多个合法 $B,T$ 组合 | 不同划分保持同一数学结果 | 待实现／待验证 |

现有[历史 CPU 摘要](../../lab/verification-2026-11-05.md)记录了 `03_uneven_split` 默认输入通过，以及 `04_arbitrary_length` 默认输入和部分边界长度通过；原始日志未随仓库归档，精确源码版本对应待补。这些记录不包括本篇新设计的核内循环，也不代表 NPU 验证完成。

## 7.3 容量预算与实际资源核对

**待验证。** 在源码实现后列出每块显式缓冲、对齐、份数、临时区和资源管理开销，与目标平台可用预算核对；工具可提供的资源信息另行记录。不能把申请量表格直接改成“实测 UB 占用率”，也不以刻意超容量申请作为必须执行的实验。

## 7.4 固定规模下的 Tile 参数扫描

**待实现／待测。** 先提出假设：Tile 太小可能增加循环和阶段交接开销，Tile 过大可能压缩可用缓冲空间或改变资源安排。固定总长、Block 数、dtype、算法和缓冲份数，仅扫描通过容量与接口约束的少量 $T$；用同一计时区间、预热与重复方式测量，记录中位数和波动。此假设不预设性能曲线或最佳参数。

预留结果表：

| $T$ | 每 Block 循环次数 | 显式数据缓冲预算 | 正确性 | Kernel 耗时与波动 |
| --- | --- | --- | --- | --- |
| 待按目标容量选定 | 待计算 | 待按实现核对 | 待验证 | 待测 |

## 7.5 静态 Tensor 与队列版对照

**待实现／待测。** 两版使用相同 $L,B,T$、输入、计时口径和单缓冲策略，先各自验证正确性，再比较耗时。记录实际改变的是资源管理与交接方式；没有对照数据前，不写“队列版更快”或“已经隐藏搬运”。正式方法、原始数据及运行记录在实际执行时归入 lab，当前不生成虚构结果文件。

# 八、验证边界与下一篇

两项练习的代码与命令保留为可复现步骤，表格中的长度与字节数是按源码计算的理论值；`test pass!` 和退出码 0 是每次运行的核验标准，不是本篇已取得的日志。`DataCopyPad` 的具体产品、地址和填充约束请以对应 CANN 9.1 文档核对；尤其不能把基础版的 `PipeBarrier<PIPE_ALL>()` 简单推广为所有跨流水依赖的通用保证。练习代码的同步语义及在目标 NPU 的运行结果均待进一步核实。

本篇目前建立了两层划分与容量模型，保留了已有尾块实现，并明确列出多轮代码与真机实验的缺项。尚未完成的部分继续标记待实现／待验证，不因正文补齐而提升状态。

当一个 Block 已经可以反复处理多批数据，搬入、计算、搬出的阶段就会重复出现。单缓冲要求按依赖安全复用；如果再准备另一份缓冲，能不能让下一批搬入与本批计算重叠？第05篇将围绕这个问题设计对照，判断 Double Buffer 在什么条件下有效，以及为什么有时增加缓冲却没有变快。

# 参考链接

1. [CANN 9.1：GM 与 UB 连续搬运 `DataCopy`](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMAndUB_continuous.md)
2. [Ascend C 官方：GM→UB 非对齐搬运 `DataCopyPad`](https://asc.gitcode.com/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_GMToUB.html)
3. [Ascend C 官方：UB→GM 非对齐搬运 `DataCopyPad`](https://asc.gitcode.com/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_UBToGM.html)
4. [Ascend C 官方：`TPipe::InitBuffer` 的缓冲块数与字节数](https://asc.gitcode.com/api/SIMD-API/basic_api/resource_management/TPipe/InitBuffer.html)

在线接口资料来自 master 持续开发文档，用于核对概念与寻找接口约束，不替代 CANN 9.1 安装版本和目标产品的支持证明。当前补充没有修改算法源码、构建配置、历史实验或截图，也没有执行新的 CPU／SIM／NPU 测试。
