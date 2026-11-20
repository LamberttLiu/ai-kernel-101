/* !
 * \file hello_world.cpp
 * \brief 快速入门示例，演示最基本的 Ascend C 内核启动和 printf 输出
 */

#include <cstdio>
#include "utils/debug/asc_printf.h"
#include "kernel_operator.h"
#include "acl/acl.h"

__global__ __vector__ void hello_world()
{
    printf("[Block (%ld/%ld)]: Hello World!!!\n", AscendC::GetBlockIdx(), AscendC::GetBlockNum());
}

static bool CheckAcl(aclError result, const char* stage)
{
    if (result != ACL_SUCCESS) {
        std::fprintf(stderr, "[HOST][ERROR] %s: ret=%d\n", stage, static_cast<int>(result));
        return false;
    }
    std::printf("[HOST][OK] %s: ret=0\n", stage);
    return true;
}

int main()
{
    if (!CheckAcl(aclInit(nullptr), "aclInit")) {
        return 1;
    }

    bool deviceSelected = false;
    bool streamCreated = false;
    bool success = false;
    aclrtStream stream = nullptr;
    do {
        if (!CheckAcl(aclrtSetDevice(0), "aclrtSetDevice")) {
            break;
        }
        deviceSelected = true;
        if (!CheckAcl(aclrtCreateStream(&stream), "aclrtCreateStream")) {
            break;
        }
        streamCreated = true;

        hello_world<<<8, 0, stream>>>();
        std::printf("[HOST] Kernel launch call returned; waiting for Stream completion.\n");
        if (!CheckAcl(aclrtSynchronizeStream(stream), "aclrtSynchronizeStream")) {
            break;
        }
        success = true;
    } while (false);

    // Release every resource acquired before a failure, and preserve cleanup failures.
    if (streamCreated && !CheckAcl(aclrtDestroyStream(stream), "aclrtDestroyStream")) {
        success = false;
    }
    if (deviceSelected && !CheckAcl(aclrtResetDevice(0), "aclrtResetDevice")) {
        success = false;
    }
    if (!CheckAcl(aclFinalize(), "aclFinalize")) {
        success = false;
    }
    return success ? 0 : 1;
}
