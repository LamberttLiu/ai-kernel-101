/* !
 * \file add.cpp
 * \brief Add operator basic sample
 */

#include <cstdint>
#include <cstdlib>
#include <vector>
#include <algorithm>
#include <iterator>

#include <iostream>

#include "acl/acl.h"

#include "kernel_operator.h"

template <uint32_t blockLength>
__vector__ __global__ void add_custom(__gm__ float* x, __gm__ float* y, __gm__ float* z, uint32_t totalLength)
{
    AscendC::InitSocState();
    const uint32_t offset = block_idx * blockLength;
    const uint32_t currentLength = (totalLength - offset) <= blockLength
        ? (totalLength - offset) : blockLength;

    AscendC::GlobalTensor<float> xGm, yGm, zGm;
    xGm.SetGlobalBuffer(x + offset, currentLength);
    yGm.SetGlobalBuffer(y + offset, currentLength);
    zGm.SetGlobalBuffer(z + offset, currentLength);

    AscendC::LocalMemAllocator<AscendC::Hardware::UB> ubAllocator;
    AscendC::LocalTensor<float> xLocal = ubAllocator.Alloc<float, blockLength>();
    AscendC::LocalTensor<float> yLocal = ubAllocator.Alloc<float, blockLength>();
    AscendC::LocalTensor<float> zLocal = ubAllocator.Alloc<float, blockLength>();

    AscendC::DataCopyExtParams copyParams{
        1, static_cast<uint32_t>(currentLength * sizeof(float)), 0, 0, 0};
    AscendC::DataCopyPadExtParams<float> padParams{false, 0, 0, 0.0f};
    AscendC::DataCopyPad(xLocal, xGm, copyParams, padParams);
    AscendC::DataCopyPad(yLocal, yGm, copyParams, padParams);
    AscendC::PipeBarrier<PIPE_ALL>();

    AscendC::Add(zLocal, xLocal, yLocal, currentLength);
    AscendC::PipeBarrier<PIPE_ALL>();

#if 0
    // Debug I/O. Set #if 1 to enable print.
    AscendC::printf("%s\n", "[ DumpTensor in xLocal]");
    AscendC::DumpTensor(xLocal, 1, 32);

    AscendC::printf("%s\n", "[ DumpTensor in yLocal]");
    AscendC::DumpTensor(yLocal, 2, 32);

    AscendC::printf("%s\n", "[ DumpTensor in zLocal]");
    AscendC::DumpTensor(zLocal, 3, 32);
#endif

    AscendC::DataCopyPad(zGm, zLocal, copyParams);
    AscendC::PipeBarrier<PIPE_ALL>();
}

std::vector<float> kernel_add(std::vector<float>& x, std::vector<float>& y)
{
    if (x.empty()) {
        return {};
    }
    constexpr uint32_t blockLength = 2048;
    uint32_t totalLength = x.size();
    uint32_t numBlocks = (totalLength + blockLength - 1) / blockLength;
    size_t totalByteSize = totalLength * sizeof(float);
    float* xDevice = nullptr;
    float* yDevice = nullptr;
    float* zDevice = nullptr;
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

    add_custom<blockLength><<<numBlocks, 0, stream>>>(xDevice, yDevice, zDevice, totalLength);
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
    uint32_t totalLength = argc > 1
        ? static_cast<uint32_t>(std::strtoul(argv[1], nullptr, 10))
        : 7 * 2048 + 1001;
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
