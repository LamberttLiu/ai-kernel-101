"""FP16 ND inputs, FP32 ND output through the installed ACLNN API."""
import ctypes as ct
import torch


class LibraryMatmul:
    def __init__(self, a, b, c, stream):
        self.tensors = (a, b, c)
        self.stream = stream
        self.base = ct.CDLL("libnnopbase.so")
        self.ops = ct.CDLL("libopapi.so")
        ptr = ct.c_void_p
        dims_ptr = ct.POINTER(ct.c_int64)
        self.base.aclCreateTensor.argtypes = [
            dims_ptr, ct.c_uint64, ct.c_int, dims_ptr, ct.c_int64,
            ct.c_int, dims_ptr, ct.c_uint64, ptr]
        self.base.aclCreateTensor.restype = ptr
        self.base.aclDestroyTensor.argtypes = [ptr]
        self.ops.aclnnMmGetWorkspaceSize.argtypes = [
            ptr, ptr, ptr, ct.c_int8, ct.POINTER(ct.c_uint64), ct.POINTER(ptr)]
        self.ops.aclnnMm.argtypes = [ptr, ct.c_uint64, ptr, ptr]
        self.handles = []
        self.workspace = None
        for t in self.tensors:
            shape = (ct.c_int64 * 2)(*t.shape)
            stride = (ct.c_int64 * 2)(*t.stride())
            dtype = 1 if t.dtype == torch.float16 else 0
            handle = self.base.aclCreateTensor(shape, 2, dtype, stride, 0, 2, shape, 2, t.data_ptr())
            if not handle:
                raise RuntimeError("aclCreateTensor failed")
            self.handles.append(handle)
        self.executor = self.prepare()

    def prepare(self):
        size, executor = ct.c_uint64(), ct.c_void_p()
        status = self.ops.aclnnMmGetWorkspaceSize(*self.handles, -1, ct.byref(size), ct.byref(executor))
        if status:
            raise RuntimeError(f"aclnnMmGetWorkspaceSize failed: {status}, cubeMathType=-1")
        if self.workspace is None or self.workspace.numel() < size.value:
            self.workspace = torch.empty(max(1, size.value), device=self.tensors[0].device, dtype=torch.uint8)
        self.workspace_bytes = size.value
        return executor

    def launch(self):
        executor = self.executor
        if executor is None:
            executor = self.prepare()
        self.executor = None
        status = self.ops.aclnnMm(self.workspace.data_ptr(), self.workspace_bytes, executor, self.stream)
        if status:
            raise RuntimeError(f"aclnnMm failed: {status}")

    def close(self):
        torch.npu.synchronize()
        for handle in self.handles:
            self.base.aclDestroyTensor(handle)
        self.handles.clear()

