// Fixed-shape educational FA forward; block-level GM handoff, not on-chip fusion.
// Uses this project's prior m/l/u implementation and the arch22 scheduling pattern.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

constexpr int N = 64, D = 32, BR = 32, BC = 32;
constexpr int TRACE_COUNT = (N / BR) * (N / BC) * BR * (D + 2);
constexpr int REPEATS = 20;
static_assert(N % BR == 0 && N % BC == 0 && N / BR >= 2 && N / BC >= 2);

#ifndef FA_REFERENCE_ONLY
#include "acl/acl.h"
#include "kernel_operator.h"
#include "adv_api/matmul_intf.h"
#include "tiling/matrix/matmul_tiling.h"
#include "tiling/platform/platform_ascendc.h"
using namespace AscendC;
using A = MatmulType<TPosition::GM, CubeFormat::ND, half>;
using B = MatmulType<TPosition::GM, CubeFormat::ND, half>;
using BTransposed = MatmulType<TPosition::GM, CubeFormat::ND, half, true>;
using C = MatmulType<TPosition::GM, CubeFormat::ND, float>;
using AE = A;
using Bias = MatmulType<TPosition::GM, CubeFormat::ND, float>;

// One active Vector worker drives the registered Cube service synchronously.
// Explicit GM score/E/EV tiles mirror arch22's staged dataflow. m/l/u stay in UB.
__global__ __mix__(1, 2) void flash_attention_fixed(__gm__ half *q, __gm__ half *k,
                                              __gm__ half *v, __gm__ float *output, __gm__ float *trace, __gm__ float *scores, __gm__ half *weights, __gm__ float *products,
                                              __kfc_workspace__ __gm__ uint8_t *workspace,
                                              AscendC::tiling::TCubeTiling tq, AscendC::tiling::TCubeTiling tv)
{
    constexpr int n = N, br = BR, bc = BC;
    TPipe pipe;
    Matmul<A, BTransposed, C, Bias> qk;
    Matmul<AE, B, C, Bias> ev;
    REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), qk, &tq, ev, &tv);
    if (GetBlockIdx() != 0)
        return;
    TBuf<TPosition::VECIN> sb, vb;
    TBuf<TPosition::VECOUT> eb;
    TBuf<TPosition::VECCALC> ub, mb, lb, ab, wb, tb;
    pipe.InitBuffer(sb, 4096);
    pipe.InitBuffer(vb, 4096);
    pipe.InitBuffer(eb, 2048);
    pipe.InitBuffer(ub, 4096);
    pipe.InitBuffer(mb, 128);
    pipe.InitBuffer(lb, 128);
    pipe.InitBuffer(ab, 128);
    pipe.InitBuffer(wb, 4096);
    pipe.InitBuffer(tb, 256);
    auto s = sb.Get<float>();
    auto z = vb.Get<float>();
    auto eh = eb.Get<half>();
    auto u = ub.Get<float>();
    auto m = mb.Get<float>();
    auto l = lb.Get<float>();
    auto alpha = ab.Get<float>();
    auto work = wb.Get<float>();
    auto temp = tb.Get<float>();
    s.SetSize(br * bc);
    z.SetSize(br * 32);
    eh.SetSize(br * bc);
    u.SetSize(br * 32);
    GlobalTensor<half> gq, gk, gv, ge;
    GlobalTensor<float> gs, gz;
    GlobalTensor<float> go, gt;
    gq.SetGlobalBuffer(q);
    gk.SetGlobalBuffer(k);
    gv.SetGlobalBuffer(v);
    go.SetGlobalBuffer(output);
    gs.SetGlobalBuffer(scores);
    ge.SetGlobalBuffer(weights);
    gz.SetGlobalBuffer(products);
    gt.SetGlobalBuffer(trace);
    int traceOffset = 0;
    for (int qi = 0; qi < n; qi += br)
    {
        Duplicate(u, 0.0f, br * 32);
        Duplicate(l, 0.0f, br);
        Duplicate(m, 0.0f, br);
        PipeBarrier<PIPE_ALL>();
        for (int kj = 0; kj < n; kj += bc)
        {
            qk.SetTensorA(gq[qi * 32]);
            qk.SetTensorB(gk[kj * 32], true);
            qk.IterateAll<false>(gs);
            qk.WaitIterateAll();
            qk.End();
            DataCopy(s, gs, br * bc);
            PipeBarrier<PIPE_ALL>();
            Muls(s, s, 0.1767766952966369f, br * bc);
            PipeBarrier<PIPE_ALL>();
            for (int r = 0; r < br; r++)
            {
                ReduceMax(temp, s[r * bc], work, bc, false);
                PipeBarrier<PIPE_ALL>();
                float mx = temp.GetValue(0), old = m.GetValue(r);
                if (kj != 0 && old > mx)
                    mx = old;
                m.SetValue(r, mx);
                alpha.SetValue(r, kj == 0 ? 0.0f : old - mx);
                Adds(s[r * bc], s[r * bc], -mx, bc);
                PipeBarrier<PIPE_ALL>();
            }
            PipeBarrier<PIPE_ALL>();
            if (kj == 0)
                Duplicate(alpha, 0.0f, br);
            else
                Exp(alpha, alpha, br);
            Exp(s, s, br * bc);
            PipeBarrier<PIPE_ALL>();
            for (int r = 0; r < br; r++)
            {
                ReduceSum(temp, s[r * bc], work, bc);
                PipeBarrier<PIPE_ALL>();
                l.SetValue(r, alpha.GetValue(r) * l.GetValue(r) + temp.GetValue(0));
                Muls(u[r * 32], u[r * 32], alpha.GetValue(r), 32);
                PipeBarrier<PIPE_ALL>();
            }
            Cast(eh, s, RoundMode::CAST_NONE, br * bc);
            PipeBarrier<PIPE_ALL>();
            DataCopy(ge, eh, br * bc);
            PipeBarrier<PIPE_ALL>();
            ev.SetTensorA(ge);
            ev.SetTensorB(gv[kj * 32]);
            ev.IterateAll<false>(gz);
            ev.WaitIterateAll();
            ev.End();
            DataCopy(z, gz, br * 32);
            PipeBarrier<PIPE_ALL>();
            Add(u, u, z, br * 32);
            PipeBarrier<PIPE_ALL>();
            // Debug prefix states; not a score/probability matrix.
            {
                DataCopy(gt[traceOffset], m, br);
                traceOffset += br;
                DataCopy(gt[traceOffset], l, br);
                traceOffset += br;
                DataCopy(gt[traceOffset], u, br * 32);
                traceOffset += br * 32;
                PipeBarrier<PIPE_ALL>();
            }
        }
        for (int r = 0; r < br; r++)
            Muls(u[r * 32], u[r * 32], 1.0f / l.GetValue(r), 32);
        PipeBarrier<PIPE_ALL>();
        DataCopy(go[qi * 32], u, br * 32);
        PipeBarrier<PIPE_ALL>();
    }
}


#endif

namespace fs = std::filesystem;
template<class T> void write_binary(const fs::path &path, const std::vector<T> &data)
{
    std::ofstream f(path, std::ios::binary);
    f.write(reinterpret_cast<const char *>(data.data()), data.size() * sizeof(T));
    if (!f) throw std::runtime_error("Cannot write " + path.string());
}

// All inputs are exact multiples of 1/16 in [-1,1]. Encode their IEEE FP16
// representation explicitly so CPU-only and NPU builds consume identical bytes.
static uint16_t encode_input(int x)
{
    if (x == 0) return 0;
    const uint16_t sign = x < 0 ? 0x8000 : 0;
    const unsigned a = static_cast<unsigned>(std::abs(x));
    unsigned p = 0;
    while ((1u << (p + 1)) <= a) ++p;
    return sign | static_cast<uint16_t>((p + 11) << 10) |
           static_cast<uint16_t>((a - (1u << p)) << (10 - p));
}
struct Inputs {
    std::vector<uint16_t> q, k, v;
    std::vector<double> q64, k64, v64;
    Inputs() : q(N*D), k(N*D), v(N*D), q64(N*D), k64(N*D), v64(N*D)
    {
        uint32_t state = 20261109;
        for (int t = 0; t < 3; ++t) {
            auto &bits = t == 0 ? q : (t == 1 ? k : v);
            auto &values = t == 0 ? q64 : (t == 1 ? k64 : v64);
            for (int i = 0; i < N*D; ++i) {
                state = state * 1664525u + 1013904223u;
                int x = static_cast<int>((state >> 16) % 33) - 16;
                bits[i] = encode_input(x);
                values[i] = x / 16.0;
            }
        }
    }
};
struct Reference { std::vector<double> output, trace; };

// Independent definition: recompute stable attention over every K/V prefix.
// It does not reuse the device online recurrence or its FP16 E rounding.
static Reference reference(const Inputs &in)
{
    Reference ref{std::vector<double>(N*D), {}};
    const double scale = 1.0 / std::sqrt(static_cast<double>(D));
    for (int qi = 0; qi < N; qi += BR) {
        for (int end = BC; end <= N; end += BC) {
            std::vector<double> m(BR), l(BR), u(BR*D);
            for (int r = 0; r < BR; ++r) {
                std::vector<double> scores(end);
                for (int j = 0; j < end; ++j) {
                    double dot = 0;
                    for (int d = 0; d < D; ++d)
                        dot += in.q64[(qi+r)*D+d] * in.k64[j*D+d];
                    scores[j] = dot * scale;
                }
                m[r] = *std::max_element(scores.begin(), scores.end());
                for (int j = 0; j < end; ++j) {
                    double e = std::exp(scores[j] - m[r]);
                    l[r] += e;
                    for (int d = 0; d < D; ++d) u[r*D+d] += e * in.v64[j*D+d];
                }
                if (end == N)
                    for (int d = 0; d < D; ++d) ref.output[(qi+r)*D+d] = u[r*D+d]/l[r];
            }
            ref.trace.insert(ref.trace.end(), m.begin(), m.end());
            ref.trace.insert(ref.trace.end(), l.begin(), l.end());
            ref.trace.insert(ref.trace.end(), u.begin(), u.end());
        }
    }
    return ref;
}

// Separate CPU recurrence for checking the prefix oracle; not NPU evidence.
static Reference cpu_online(const Inputs &in)
{
    Reference got{std::vector<double>(N*D), {}};
    for (int qi = 0; qi < N; qi += BR) {
        std::vector<double> m(BR), l(BR), u(BR*D);
        for (int kj = 0; kj < N; kj += BC) {
            for (int r = 0; r < BR; ++r) {
                std::vector<double> s(BC);
                for (int j = 0; j < BC; ++j) {
                    for (int d = 0; d < D; ++d)
                        s[j] += in.q64[(qi+r)*D+d] * in.k64[(kj+j)*D+d];
                    s[j] /= std::sqrt(static_cast<double>(D));
                }
                double next = *std::max_element(s.begin(), s.end());
                if (kj) next = std::max(next, m[r]);
                double a = kj ? std::exp(m[r]-next) : 0;
                l[r] *= a;
                for (int d = 0; d < D; ++d) u[r*D+d] *= a;
                for (int j = 0; j < BC; ++j) {
                    double e = std::exp(s[j]-next);
                    l[r] += e;
                    for (int d = 0; d < D; ++d) u[r*D+d] += e * in.v64[(kj+j)*D+d];
                }
                m[r] = next;
            }
            got.trace.insert(got.trace.end(), m.begin(), m.end());
            got.trace.insert(got.trace.end(), l.begin(), l.end());
            got.trace.insert(got.trace.end(), u.begin(), u.end());
        }
        for (int r = 0; r < BR; ++r)
            for (int d = 0; d < D; ++d) got.output[(qi+r)*D+d] = u[r*D+d]/l[r];
    }
    return got;
}

template<class T> static bool compare(const std::vector<T> &got, const std::vector<double> &ref,
                                    bool trace, bool cpu, int repeat, std::ostream &csv)
{
    if (got.size() != ref.size()) throw std::runtime_error("Wrong result size");
    const char *names[] = {"O", "m", "l", "u"};
    size_t failures[4]{}, counts[4]{};
    double absmax[4]{}, relmax[4]{};
    for (size_t i = 0; i < ref.size(); ++i) {
        size_t pos = i % (BR*(D+2));
        int tag = trace ? (pos < BR ? 1 : (pos < 2*BR ? 2 : 3)) : 0;
        double tol = cpu ? 1e-11 : (tag == 1 ? 2e-4 : 3e-3);
        double x = static_cast<double>(got[i]);
        double delta = std::abs(x - ref[i]);
        bool finite = std::isfinite(x) && std::isfinite(ref[i]);
        failures[tag] += !finite || delta > tol + tol * std::abs(ref[i]);
        ++counts[tag];
        absmax[tag] = std::max(absmax[tag], finite ? delta : std::numeric_limits<double>::infinity());
        relmax[tag] = std::max(relmax[tag], finite ? delta/std::max(std::abs(ref[i]),1e-6) : std::numeric_limits<double>::infinity());
    }
    bool passed = true;
    for (int tag = 0; tag < 4; ++tag) if (counts[tag]) {
        double tol = cpu ? 1e-11 : (tag == 1 ? 2e-4 : 3e-3);
        csv << (cpu ? "CPU" : "NPU") << ',' << repeat << ',' << names[tag] << ','
            << counts[tag] << ',' << failures[tag] << ',' << absmax[tag] << ',' << relmax[tag]
            << ',' << tol << ',' << tol << '\n';
        passed = passed && failures[tag] == 0;
    }
    return passed;
}

#ifndef FA_REFERENCE_ONLY
static void acl_check(aclError code, const char *op)
{
    if (code != ACL_SUCCESS) throw std::runtime_error(std::string(op)+" error="+std::to_string(code));
}
#define ACL(call) acl_check((call), #call)
struct Runtime {
    bool initialized = false, selected = false;
    aclrtStream stream = nullptr;
    void init() {
        ACL(aclInit(nullptr)); initialized = true;
        ACL(aclrtSetDevice(0)); selected = true;
        ACL(aclrtCreateStream(&stream));
    }
    ~Runtime() {
        if (stream) { aclrtSynchronizeStream(stream); aclrtDestroyStream(stream); }
        if (selected) aclrtResetDevice(0);
        if (initialized) aclFinalize();
    }
};
struct DeviceBuffer {
    void *ptr = nullptr;
    size_t bytes;
    explicit DeviceBuffer(size_t n) : bytes(n) { ACL(aclrtMalloc(&ptr,n,ACL_MEM_MALLOC_HUGE_FIRST)); }
    ~DeviceBuffer() { if(ptr) aclrtFree(ptr); }
    DeviceBuffer(const DeviceBuffer &) = delete;
    DeviceBuffer &operator=(const DeviceBuffer &) = delete;
    template<class T> T *as() { return reinterpret_cast<T *>(ptr); }
    template<class T> void upload(const std::vector<T> &v) {
        if (v.size()*sizeof(T) != bytes) throw std::runtime_error("Upload size mismatch");
        ACL(aclrtMemcpy(ptr,bytes,v.data(),bytes,ACL_MEMCPY_HOST_TO_DEVICE));
    }
    std::vector<float> download() {
        std::vector<float> v(bytes/sizeof(float));
        ACL(aclrtMemcpy(v.data(),bytes,ptr,bytes,ACL_MEMCPY_DEVICE_TO_HOST));
        return v;
    }
};
static AscendC::tiling::TCubeTiling make_tiling(platform_ascendc::PlatformAscendC &p, bool transpose)
{
    matmul_tiling::MatmulApiTiling api(p);
    using namespace matmul_tiling;
    api.SetAType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16);
    api.SetBType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16, transpose);
    api.SetCType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT);
    api.SetBias(false);
    api.SetOrgShape(BR, transpose ? BC : D, transpose ? D : BC);
    api.SetShape(BR, transpose ? BC : D, transpose ? D : BC);
    api.SetFixSplit(BR, transpose ? BC : D, transpose ? D : BC);
    api.SetBufferSpace(-1,-1,64*1024);
    AscendC::tiling::TCubeTiling t{};
    if(api.GetTiling(t) != 0 || t.baseM != BR || t.baseN != (transpose ? BC : D))
        throw std::runtime_error("Unsupported Matmul tiling: require one output tile");
    std::cout << "tiling=" << (transpose ? "QK" : "EV") << " base=" << t.baseM << ',' << t.baseN << ',' << t.baseK << '\n';
    return t;
}
static void run_npu(const Inputs &in, const Reference &ref, const fs::path &dir, std::ostream &metrics)
{
    Runtime runtime;
    runtime.init();
    const char *soc = aclrtGetSocName();
    if(!soc) throw std::runtime_error("aclrtGetSocName returned null");
    auto *platform = platform_ascendc::PlatformAscendCManager::GetInstance(soc);
    if(!platform) throw std::runtime_error("No platform information for runtime SoC");
    if(platform->GetCurNpuArch() != NpuArch::DAV_2201)
        throw std::runtime_error("This example requires DAV_2201");
    const size_t workspaceBytes = platform->GetLibApiWorkSpaceSize();
    if(!workspaceBytes) throw std::runtime_error("Unexpected zero system workspace");
    std::ofstream env(dir/"runtime.txt");
    env << "soc=" << soc << "\ntarget=dav-2201\nworkspace_bytes=" << workspaceBytes
        << "\nCANN/compiler/driver/firmware: record separately; not inferred from SoC\n";
    if(!env) throw std::runtime_error("Cannot write runtime metadata");
    std::cout << "soc=" << soc << " system_workspace_bytes=" << workspaceBytes << std::endl;
    auto tq = make_tiling(*platform,true), tv = make_tiling(*platform,false);
    DeviceBuffer q(N*D*2), k(N*D*2), v(N*D*2), out(N*D*4), trace(TRACE_COUNT*4);
    DeviceBuffer scores(BR*BC*4), weights(BR*BC*2), products(BR*D*4), workspace(workspaceBytes);
    q.upload(in.q); k.upload(in.k); v.upload(in.v);
    std::vector<float> firstOutput, firstTrace;
    for(int rep=0; rep<REPEATS; ++rep) {
        ACL(aclrtMemset(out.ptr,out.bytes,0xff,out.bytes));
        ACL(aclrtMemset(trace.ptr,trace.bytes,0xff,trace.bytes));
        flash_attention_fixed<<<1,0,runtime.stream>>>(q.as<half>(),k.as<half>(),v.as<half>(),
            out.as<float>(),trace.as<float>(),scores.as<float>(),weights.as<half>(),products.as<float>(),
            workspace.as<uint8_t>(),tq,tv);
        ACL(aclrtSynchronizeStream(runtime.stream));
        auto o=out.download(), states=trace.download();
        write_binary(dir/("output-"+std::to_string(rep)+".bin"),o);
        write_binary(dir/("states-"+std::to_string(rep)+".bin"),states);
        bool okO=compare(o,ref.output,false,false,rep,metrics);
        bool okStates=compare(states,ref.trace,true,false,rep,metrics);
        metrics.flush();
        if(!okO || !okStates) throw std::runtime_error("NPU accuracy failed; outputs preserved");
        if(rep==0) { firstOutput=o; firstTrace=states; }
        else if(std::memcmp(o.data(),firstOutput.data(),out.bytes) ||
                std::memcmp(states.data(),firstTrace.data(),trace.bytes))
            throw std::runtime_error("NPU bitwise repeat check failed; outputs preserved");
    }
    std::cout << "NPU correctness and " << REPEATS << " bitwise repeats: PASS (no performance claim)\n";
}
#endif

int main(int argc, char **argv)
{
    fs::path dir;
    bool reserved = false;
    try {
        if(argc!=2) throw std::runtime_error("usage: fa_fixed NEW_OUTPUT_DIRECTORY");
        dir=fs::absolute(argv[1]);
        // Do not overwrite an earlier success or failure, including a concurrent run.
        fs::create_directories(dir.parent_path());
        if(!fs::create_directory(dir)) throw std::runtime_error("Output directory already exists");
        reserved=true;
        Inputs in;
        write_binary(dir/"q.bin",in.q); write_binary(dir/"k.bin",in.k); write_binary(dir/"v.bin",in.v);
        Reference ref=reference(in), online=cpu_online(in);
        write_binary(dir/"reference-output-fp64.bin",ref.output);
        write_binary(dir/"reference-states-fp64.bin",ref.trace);
        std::ofstream metrics(dir/"metrics.csv");
        if(!metrics) throw std::runtime_error("Cannot create metrics.csv");
        metrics << std::setprecision(17) << "mode,repeat,quantity,elements,failed,max_abs,max_rel_floor_1e-6,atol,rtol\n";
        bool cpuO=compare(online.output,ref.output,false,true,0,metrics);
        bool cpuStates=compare(online.trace,ref.trace,true,true,0,metrics);
        if(!cpuO || !cpuStates) throw std::runtime_error("CPU oracle/recurrence mismatch");
        std::cout << "B=1 H=1 N=64 D=32 BR=32 BC=32 non-causal; CPU FP64 checks: PASS\n";
#ifdef FA_REFERENCE_ONLY
        std::cout << "REFERENCE_ONLY: no NPU execution, no NPU correctness/performance claim\n";
#else
        run_npu(in,ref,dir,metrics);
#endif
        metrics.flush();
        if(!metrics) throw std::runtime_error("Cannot finish metrics.csv");
        std::ofstream status(dir/"status.txt");
#ifdef FA_REFERENCE_ONLY
        status << "CPU_REFERENCE_PASS; NPU_NOT_RUN\n";
#else
        status << "CPU_REFERENCE_PASS; NPU_FUNCTION_PASS; PERFORMANCE_NOT_MEASURED\n";
#endif
        if(!status) throw std::runtime_error("Cannot write status.txt");
        return 0;
    } catch(const std::exception &e) {
        std::cerr << e.what() << '\n';
        if(reserved) { std::ofstream error(dir/"error.txt"); error << e.what() << '\n'; }
        return 1;
    }
}
