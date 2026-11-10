#include <acl/acl.h>

#include <cerrno>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

namespace {

void Check(aclError result, const char* operation) {
    if (result != ACL_SUCCESS) {
        throw std::runtime_error(std::string(operation) + " failed, aclError=" +
                                 std::to_string(result));
    }
}

std::size_t ParsePositive(const char* text, const char* name) {
    errno = 0;
    char* end = nullptr;
    const unsigned long long value = std::strtoull(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0' || value == 0 || text[0] == '-' ||
        value > std::numeric_limits<std::size_t>::max()) {
        throw std::invalid_argument(std::string(name) + " must be a positive integer");
    }
    return static_cast<std::size_t>(value);
}

class Resources {
public:
    explicit Resources(std::size_t bytes) : bytes_(bytes) {
        Check(aclInit(nullptr), "aclInit");
        initialized_ = true;
        Check(aclrtSetDevice(0), "aclrtSetDevice");
        device_set_ = true;
        Check(aclrtCreateStream(&stream_), "aclrtCreateStream");
        Check(aclrtMallocHost(&host_input_, bytes_), "aclrtMallocHost(input)");
        Check(aclrtMallocHost(&host_output_, bytes_), "aclrtMallocHost(output)");
        Check(aclrtMalloc(&device_, bytes_, ACL_MEM_MALLOC_HUGE_FIRST), "aclrtMalloc");
    }

    ~Resources() {
        if (stream_ != nullptr) aclrtSynchronizeStream(stream_);
        if (device_ != nullptr) aclrtFree(device_);
        if (host_output_ != nullptr) aclrtFreeHost(host_output_);
        if (host_input_ != nullptr) aclrtFreeHost(host_input_);
        if (stream_ != nullptr) aclrtDestroyStream(stream_);
        if (device_set_) aclrtResetDevice(0);
        if (initialized_) aclFinalize();
    }

    Resources(const Resources&) = delete;
    Resources& operator=(const Resources&) = delete;

    void* input() const { return host_input_; }
    void* output() const { return host_output_; }
    void* device() const { return device_; }
    aclrtStream stream() const { return stream_; }
    std::size_t bytes() const { return bytes_; }

private:
    std::size_t bytes_;
    bool initialized_ = false;
    bool device_set_ = false;
    aclrtStream stream_ = nullptr;
    void* host_input_ = nullptr;
    void* host_output_ = nullptr;
    void* device_ = nullptr;
};

class TimingEvents {
public:
    TimingEvents() {
        Check(aclrtCreateEventExWithFlag(&start_, ACL_EVENT_TIME_LINE), "create start event");
        Check(aclrtCreateEventExWithFlag(&end_, ACL_EVENT_TIME_LINE), "create end event");
    }
    ~TimingEvents() {
        if (end_ != nullptr) aclrtDestroyEvent(end_);
        if (start_ != nullptr) aclrtDestroyEvent(start_);
    }
    aclrtEvent start() const { return start_; }
    aclrtEvent end() const { return end_; }

private:
    aclrtEvent start_ = nullptr;
    aclrtEvent end_ = nullptr;
};

struct Measurement {
    double microseconds_per_copy;
    double gigabytes_per_second;
};

Measurement Measure(Resources& resources, void* dst, const void* src,
                    aclrtMemcpyKind kind, std::size_t iterations, std::size_t warmup) {
    const auto copy = [&] {
        Check(aclrtMemcpyAsync(dst, resources.bytes(), src, resources.bytes(), kind,
                             resources.stream()), "aclrtMemcpyAsync");
    };

    for (std::size_t i = 0; i < warmup; ++i) copy();
    Check(aclrtSynchronizeStream(resources.stream()), "warmup synchronize");

    TimingEvents events;
    Check(aclrtRecordEvent(events.start(), resources.stream()), "record start");
    for (std::size_t i = 0; i < iterations; ++i) copy();
    Check(aclrtRecordEvent(events.end(), resources.stream()), "record end");
    Check(aclrtSynchronizeStream(resources.stream()), "measurement synchronize");

    float elapsed_ms = 0.0f;
    Check(aclrtEventElapsedTime(&elapsed_ms, events.start(), events.end()), "event elapsed time");
    if (!(elapsed_ms > 0.0f) || !std::isfinite(elapsed_ms)) {
        throw std::runtime_error("invalid event elapsed time");
    }
    const double elapsed_seconds = static_cast<double>(elapsed_ms) / 1000.0;
    return {elapsed_seconds * 1e6 / static_cast<double>(iterations),
            static_cast<double>(resources.bytes()) * static_cast<double>(iterations) /
                elapsed_seconds / 1e9};
}

}  // namespace

int main(int argc, char* argv[]) {
    try {
        if (argc > 3) {
            std::cerr << "Usage: transfer_bench [bytes=16777216] [iterations=100]\n";
            return 2;
        }
        const std::size_t bytes = argc > 1 ? ParsePositive(argv[1], "bytes") : 16u * 1024u * 1024u;
        const std::size_t iterations = argc > 2 ? ParsePositive(argv[2], "iterations") : 100;
        if (bytes > std::numeric_limits<std::size_t>::max() / iterations) {
            throw std::invalid_argument("bytes * iterations overflows size_t");
        }

        Resources resources(bytes);
        auto* input = static_cast<std::uint8_t*>(resources.input());
        auto* output = static_cast<std::uint8_t*>(resources.output());
        for (std::size_t i = 0; i < bytes; ++i) input[i] = static_cast<std::uint8_t>(i * 131u + 7u);
        std::memset(output, 0, bytes);

        constexpr std::size_t warmup = 10;
        const auto h2d = Measure(resources, resources.device(), resources.input(),
                                 ACL_MEMCPY_HOST_TO_DEVICE, iterations, warmup);
        const auto d2h = Measure(resources, resources.output(), resources.device(),
                                 ACL_MEMCPY_DEVICE_TO_HOST, iterations, warmup);

        if (std::memcmp(input, output, bytes) != 0) {
            throw std::runtime_error("D2H output differs from H2D input");
        }
        std::cout << "bytes=" << bytes << " iterations=" << iterations
                  << " warmup=" << warmup << " verify=pass\n";
        std::cout << std::fixed << std::setprecision(3);
        std::cout << "H2D: " << h2d.microseconds_per_copy << " us/copy, "
                  << h2d.gigabytes_per_second << " GB/s\n";
        std::cout << "D2H: " << d2h.microseconds_per_copy << " us/copy, "
                  << d2h.gigabytes_per_second << " GB/s\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << '\n';
        return 1;
    }
}
