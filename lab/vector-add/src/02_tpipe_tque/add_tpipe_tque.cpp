/* !
 * \file add_tpipe_tque.cpp
 * \brief 基于TPipe和TQue的Add向量加法样例，演示按核切分输入数据，
 *        并通过队列完成 GM 到 UB 搬入、UB 内向量加法和结果写回 GM 的完整流程。
 */
#include "acl/acl.h"
#include "kernel_operator.h"
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <iterator>
#include <vector>

__global__ __vector__ void add_custom(__gm__ uint8_t* x, __gm__ uint8_t* y, __gm__ uint8_t* z, uint32_t totalLength)
{
    AscendC::TPipe pipe;
    AscendC::TQue<AscendC::TPosition::VECIN, 1> inQueueX;
    AscendC::TQue<AscendC::TPosition::VECIN, 1> inQueueY;
    AscendC::TQue<AscendC::TPosition::VECOUT, 1> outQueueZ;
    AscendC::GlobalTensor<float> xGm;
    AscendC::GlobalTensor<float> yGm;
    AscendC::GlobalTensor<float> zGm;

    // totalLength 表示全局输入长度；GetBlockNum() 返回本次启动的核数，
    // 这里按核数均分每个 block 的处理区间。
    uint32_t blockLength = totalLength / AscendC::GetBlockNum();

    // 根据 block_idx 计算当前核在 GM 中的起始地址，确保各核访问互不重叠的数据分片。
    xGm.SetGlobalBuffer((__gm__ float*)x + blockLength * AscendC::GetBlockIdx(), blockLength);
    yGm.SetGlobalBuffer((__gm__ float*)y + blockLength * AscendC::GetBlockIdx(), blockLength);
    zGm.SetGlobalBuffer((__gm__ float*)z + blockLength * AscendC::GetBlockIdx(), blockLength);

    // 为输入和输出队列申请与 blockLength 对应的 UB 缓冲，保持 TPipe/TQue 的编程范式。
    pipe.InitBuffer(inQueueX, 1, blockLength * sizeof(float));
    pipe.InitBuffer(inQueueY, 1, blockLength * sizeof(float));
    pipe.InitBuffer(outQueueZ, 1, blockLength * sizeof(float));

    // 使用 DataCopy 将输入从 GM 搬运到 UB，并通过 EnQue 将 LocalTensor 入队，供后续计算阶段 DeQue 取用。
    AscendC::LocalTensor<float> xLocal = inQueueX.AllocTensor<float>();
    AscendC::LocalTensor<float> yLocal = inQueueY.AllocTensor<float>();
    AscendC::DataCopy(xLocal, xGm, blockLength);
    AscendC::DataCopy(yLocal, yGm, blockLength);
    inQueueX.EnQue(xLocal);
    inQueueY.EnQue(yLocal);

    // DeQue 取出输入张量，在 UB 内执行 Add，并将结果 EnQue 到输出队列，供后续写回 GM。
    xLocal = inQueueX.DeQue<float>();
    yLocal = inQueueY.DeQue<float>();
    AscendC::LocalTensor<float> zLocal = outQueueZ.AllocTensor<float>();
    AscendC::Add(zLocal, xLocal, yLocal, blockLength);
    outQueueZ.EnQue<float>(zLocal);
    inQueueX.FreeTensor(xLocal);
    inQueueY.FreeTensor(yLocal);

    // 从输出队列取出结果，并写回当前核负责的 GM 分片。
    zLocal = outQueueZ.DeQue<float>();
    AscendC::DataCopy(zGm, zLocal, blockLength);
    outQueueZ.FreeTensor(zLocal);
}

std::vector<float> kernel_add(std::vector<float>& x, std::vector<float>& y)
{
    constexpr uint32_t numBlocks = 8;
    uint32_t totalLength = x.size();
    size_t totalByteSize = totalLength * sizeof(float);
    uint8_t* xDevice = nullptr;
    uint8_t* yDevice = nullptr;
    uint8_t* zDevice = nullptr;
    uint8_t* zHost = nullptr;

    aclInit(nullptr);
    int32_t deviceId = 0;
    aclrtSetDevice(deviceId);
    aclrtStream stream = nullptr;
    aclrtCreateStream(&stream);

    aclrtMalloc((void**)&xDevice, totalByteSize, ACL_MEM_MALLOC_HUGE_FIRST);
    aclrtMalloc((void**)&yDevice, totalByteSize, ACL_MEM_MALLOC_HUGE_FIRST);
    aclrtMalloc((void**)&zDevice, totalByteSize, ACL_MEM_MALLOC_HUGE_FIRST);
    aclrtMallocHost((void**)&zHost, totalByteSize);

    aclrtMemcpy(xDevice, totalByteSize, x.data(), totalByteSize, ACL_MEMCPY_HOST_TO_DEVICE);
    aclrtMemcpy(yDevice, totalByteSize, y.data(), totalByteSize, ACL_MEMCPY_HOST_TO_DEVICE);

    add_custom<<<numBlocks, 0, stream>>>(xDevice, yDevice, zDevice, totalLength);
    aclrtSynchronizeStream(stream);

    aclrtMemcpy(zHost, totalByteSize, zDevice, totalByteSize, ACL_MEMCPY_DEVICE_TO_HOST);
    std::vector<float> z((float*)zHost, (float*)(zHost + totalByteSize));

    aclrtFree(xDevice);
    aclrtFree(yDevice);
    aclrtFree(zDevice);
    aclrtFreeHost(zHost);

    aclrtDestroyStream(stream);
    aclrtResetDevice(deviceId);
    aclFinalize();

    return z;
}

uint32_t VerifyResult(std::vector<float>& output, std::vector<float>& golden)
{
    auto printTensor = [](std::vector<float>& tensor, const char* name) {
        constexpr size_t maxPrintSize = 20;
        std::cout << name << ": ";
        std::copy(
            tensor.begin(), tensor.begin() + std::min(tensor.size(), maxPrintSize),
            std::ostream_iterator<float>(std::cout, " "));
        if (tensor.size() > maxPrintSize) {
            std::cout << "...";
        }
        std::cout << std::endl;
    };
    printTensor(output, "Output");
    printTensor(golden, "Golden");
    if (std::equal(golden.begin(), golden.end(), output.begin())) {
        std::cout << "test pass!" << std::endl;
        return 0;
    } else {
        std::cout << "test failed!" << std::endl;
        return 1;
    }
}

int32_t main(int32_t argc, char* argv[])
{
    constexpr uint32_t totalLength = 8 * 2048;
    std::vector<float> x(totalLength);
    std::vector<float> y(totalLength);

    for (uint32_t i = 0; i < totalLength; ++i) {
        x[i] = i * 0.1f;
        y[i] = i * 0.2f;
    }

    std::vector<float> output = kernel_add(x, y);

    std::vector<float> golden(totalLength);
    for (uint32_t i = 0; i < totalLength; ++i) {
        golden[i] = x[i] + y[i];
    }

    return VerifyResult(output, golden);
}
