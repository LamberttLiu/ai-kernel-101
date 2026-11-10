/* !
 * \file hello_world.cpp
 * \brief 快速入门示例，演示最基本的Ascend C内核启动和printf输出
 */

#include "utils/debug/asc_printf.h"
#include "kernel_operator.h"
#include "acl/acl.h"

__global__ __vector__ void hello_world()
{
    printf("[Block (%ld/%ld)]: Hello World!!!\n", AscendC::GetBlockIdx(), AscendC::GetBlockNum());
}

int main(int argc, char const* argv[])
{
    aclInit(nullptr);
    aclrtSetDevice(0); // 运行管理资源申请。
    aclrtStream stream = nullptr;
    aclrtCreateStream(&stream);
    hello_world<<<8, 0, stream>>>();
    aclrtSynchronizeStream(stream);
    aclrtDestroyStream(stream);
    aclrtResetDevice(0); // 销毁运行资源。
    aclFinalize();
    return 0;
}
