// Host allocations, stream ownership and correctness checks live in run.py.
#include <cstdint>
#include "acl/acl.h"
#include "kernel_operator.h"
#define ASCENDC_CUBE_ONLY
#include "adv_api/matmul_intf.h"
#include "tiling/matrix/matmul_tiling.h"
#include "tiling/platform/platform_ascendc.h"

using namespace AscendC;
constexpr unsigned TILE = 2048;
__vector__ __global__ void add_tiles(__gm__ float *x, __gm__ float *y, __gm__ float *z,
                                     unsigned tiles, unsigned workers)
{
    InitSocState();
    GlobalTensor<float> left, right, output;
    left.SetGlobalBuffer(x);
    right.SetGlobalBuffer(y);
    output.SetGlobalBuffer(z);
    LocalMemAllocator<Hardware::UB> ub;
    auto a = ub.Alloc<float, TILE>();
    auto b = ub.Alloc<float, TILE>();
    auto c = ub.Alloc<float, TILE>();
    for (unsigned t = GetBlockIdx(); t < tiles; t += workers) {
        unsigned offset = t * TILE;
        DataCopy(a, left[offset], TILE);
        DataCopy(b, right[offset], TILE);
        PipeBarrier<PIPE_ALL>();
        Add(c, a, b, TILE);
        PipeBarrier<PIPE_ALL>();
        DataCopy(output[offset], c, TILE);
        PipeBarrier<PIPE_ALL>();
    }
}

using Input = MatmulType<TPosition::GM, CubeFormat::ND, half>;
using Output = MatmulType<TPosition::GM, CubeFormat::ND, float>;
using Tiling = AscendC::tiling::TCubeTiling;

// Each cube worker owns complete output tiles, including all K panels.
__cube__ __global__ void mm_tiles(__gm__ half *a, __gm__ half *b, __gm__ float *c,
                                  __kfc_workspace__ __gm__ uint8_t *workspace,
                                  Tiling tiling, unsigned n, unsigned tile, unsigned workers)
{
    TPipe pipe;
    Matmul<Input, Input, Output, Output> mm;
    REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling);
    GlobalTensor<half> left, right;
    GlobalTensor<float> output;
    left.SetGlobalBuffer(a);
    right.SetGlobalBuffer(b);
    output.SetGlobalBuffer(c);
    unsigned columns = n / tile;
    for (unsigned t = GetBlockIdx(); t < columns * columns; t += workers) {
        unsigned row = t / columns * tile;
        unsigned col = t % columns * tile;
        mm.SetOrgShape(n, n, n);
        mm.SetSingleShape(tile, tile, n);
        mm.SetTensorA(left[row * n]);
        mm.SetTensorB(right[col]);
        mm.IterateAll(output[row * n + col]);
        mm.End();
    }
}

static auto runtime_platform()
{
    const char *soc = aclrtGetSocName();
    return soc ? platform_ascendc::PlatformAscendCManager::GetInstance(soc) : nullptr;
}

extern "C" int device_info(unsigned *aiv, unsigned *aic, uint64_t *workspace)
{
    auto *p = runtime_platform();
    if (!p || p->GetCurNpuArch() != NpuArch::DAV_2201) return -1;
    *aiv = p->GetCoreNumAiv();
    *aic = p->GetCoreNumAic();
    *workspace = p->GetLibApiWorkSpaceSize();
    return 0;
}

extern "C" uint64_t l2_capacity()
{
    uint64_t bytes = 0;
    auto *p = runtime_platform();
    if (p) p->GetCoreMemSize(platform_ascendc::CoreMemType::L2, bytes);
    return bytes;
}

// The single-process driver prepares one configuration at a time.
static Tiling prepared;
extern "C" int prepare_mm(unsigned n, unsigned tile, unsigned *base)
{
    auto *p = runtime_platform();
    if (!p || !n || (tile != 32 && tile != 64) || n % tile) return -1;
    matmul_tiling::MatmulApiTiling api(*p);
    using Pos = matmul_tiling::TPosition;
    using Fmt = matmul_tiling::CubeFormat;
    using Type = matmul_tiling::DataType;
    api.SetAType(Pos::GM, Fmt::ND, Type::DT_FLOAT16);
    api.SetBType(Pos::GM, Fmt::ND, Type::DT_FLOAT16);
    api.SetCType(Pos::GM, Fmt::ND, Type::DT_FLOAT);
    api.SetBias(false);
    api.SetOrgShape(n, n, n);
    api.SetShape(tile, tile, n);
    api.SetFixSplit(tile, tile, 32);
    api.SetBufferSpace(-1, -1, -1);
    prepared = {};
    if (api.GetTiling(prepared) != 0) return -2;
    base[0] = prepared.baseM;
    base[1] = prepared.baseN;
    base[2] = prepared.baseK;
    return base[0] == tile && base[1] == tile && base[2] > 0 && n % base[2] == 0 ? 0 : -3;
}

extern "C" void launch_add(float *x, float *y, float *z, unsigned n, unsigned workers, aclrtStream s)
{
    add_tiles<<<workers, 0, s>>>(x, y, z, n / TILE, workers);
}

extern "C" void launch_mm(half *a, half *b, float *c, uint8_t *workspace,
                          unsigned n, unsigned tile, unsigned workers, aclrtStream s)
{
    mm_tiles<<<workers, 0, s>>>(a, b, c, workspace, prepared, n, tile, workers);
}
