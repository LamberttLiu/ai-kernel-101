"""Lab02 NPU experiments. Invoke one stage explicitly after author approval."""
import argparse
import ctypes as ct
import json
import os
import random
from pathlib import Path

import numpy as np
# Submit framework events and external ACL launches in the same host order.
os.environ["TASK_QUEUE_ENABLE"] = "0"
import torch
import torch_npu  # registers the NPU backend
from library_matmul import LibraryMatmul


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices="A1 A2 A3 M0 M1 M2 M3".split())
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--max-n", type=int, choices=[64, 128, 256, 512, 1024], default=512)
    parser.add_argument("--l2-bytes", type=int)
    parser.add_argument("--reps", type=int, default=50)
    args = parser.parse_args()
    if args.reps < 50:
        parser.error("at least 50 launches per timing group")
    if args.stage == "A3" and (not args.l2_bytes or args.l2_bytes <= 0):
        parser.error("A3 requires the verified device L2 capacity in bytes")
    if args.stage == "M2" and args.max_n < 512:
        parser.error("M2 compares both tiles at n=512")
    torch.npu.set_device(args.device)
    torch.npu.config.allow_internal_format = False
    device = torch.device(f"npu:{args.device}")
    stream = torch.npu.current_stream()
    lib = ct.CDLL(str(args.library.resolve()))
    pointer, uint = ct.c_void_p, ct.c_uint
    lib.device_info.argtypes = [ct.POINTER(uint), ct.POINTER(uint), ct.POINTER(ct.c_uint64)]
    lib.prepare_mm.argtypes = [uint, uint, ct.POINTER(uint)]
    lib.launch_add.argtypes = [pointer, pointer, pointer, uint, uint, pointer]
    lib.launch_mm.argtypes = [pointer] * 4 + [uint] * 3 + [pointer]
    lib.launch_add.restype = lib.launch_mm.restype = None
    lib.l2_capacity.restype = ct.c_uint64
    aiv, aic, ws = uint(), uint(), ct.c_uint64()
    if lib.device_info(ct.byref(aiv), ct.byref(aic), ct.byref(ws)):
        raise RuntimeError("requires a DAV_2201 platform descriptor")
    matrix = args.stage.startswith("M")
    available = aic.value if matrix else aiv.value
    workers = available if args.workers is None else args.workers
    if not 1 <= workers <= available:
        parser.error(f"workers must be between 1 and {available}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stream_ptr = stream.npu_stream
    workspace = torch.empty(max(1, ws.value), device=device, dtype=torch.uint8) if matrix else None

    with args.output.open("x", encoding="utf-8", buffering=1) as out:
        def record(**fields):
            print(json.dumps(fields, allow_nan=False), file=out)

        record(stage=args.stage, device=torch.npu.get_device_name(args.device), seed=2026,
               aiv=aiv.value, aic=aic.value, torch=torch.__version__, torch_npu=torch_npu.__version__,
               workers=workers, reps=args.reps, l2_bytes=args.l2_bytes,
               platform_l2_bytes=lib.l2_capacity(), task_queue_enable=0, hbm_bytes=None)

        def measure(launch, verify, count, **fields):
            for i in range(max(20, count)):
                launch(i % count)
            verify()
            samples = []
            repeats = max(count, args.reps)
            for group in range(5):
                start = torch.npu.Event(enable_timing=True)
                end = torch.npu.Event(enable_timing=True)
                start.record(stream)
                for i in range(repeats):
                    launch((group * repeats + i) % count)
                end.record(stream)
                end.synchronize()
                elapsed = start.elapsed_time(end) * 1000 / repeats
                if elapsed <= 0:
                    raise RuntimeError("unresolved event duration; increase --reps")
                samples.append(elapsed)
                verify()
                record(kind="group", group=group, mean_us=elapsed, launches=repeats, **fields)
            low, q1, median, q3, high = np.percentile(samples, [0, 25, 50, 75, 100])
            record(kind="timing", min_us=low, q1_us=q1, median_us=median, q3_us=q3,
                   max_us=high, timer="device_stream_group", **fields)

        def add_case(n, g, slots, baseline=False, check_only=False):
            if n <= 0 or n % 2048:
                raise ValueError("Add requires a positive multiple of 2048")
            rng = np.random.default_rng(2026)
            buffers, expected = [], []
            for slot in range(slots):
                x, y = rng.random((2, n), dtype=np.float32) - np.float32(0.5)
                # Include zeros, opposite signs and positional markers in every tile.
                x[::2048] = np.arange(n // 2048, dtype=np.float32) + slot
                y[::2048] = -1
                x[1::2048] = y[1::2048] = 0
                expected.append(np.maximum(x, y) if baseline else x + y)
                buffers.append((torch.from_numpy(x).to(device), torch.from_numpy(y).to(device),
                                torch.full((n,), float("nan"), device=device)))
            torch.npu.synchronize()
            def launch(i):
                x, y, z = buffers[i]
                if baseline:
                    torch.maximum(x, y, out=z)
                else:
                    lib.launch_add(x.data_ptr(), y.data_ptr(), z.data_ptr(), n, g, stream_ptr)
            def verify():
                for (_, _, z), ref in zip(buffers, expected):
                    np.testing.assert_array_equal(z.cpu().numpy().view("u4"), ref.view("u4"))
            if check_only:
                launch(0)
                verify()
                return
            tile_counts = [len(range(worker, n // 2048, g)) for worker in range(g)]
            assert sum(tile_counts) * 2048 == n
            measure(launch, verify, slots, n=n, workers=g, active=min(g, n // 2048),
                    slots=slots, footprint=slots * n * 12, logical_bytes=12 * n,
                    tiles_per_worker=None if baseline else tile_counts,
                    kernel="torch.maximum" if baseline else "add")

        if not matrix:
            add_case(2048 * (workers + 1), workers, 1, check_only=True)
            if args.stage == "A1":
                cases = [(2**p, workers, 1, False) for p in [11, 12, 14, 16, 18, 20, 22, 24]]
            elif args.stage == "A2":
                cases = [(2**22, g, 1, False) for g in sorted({1, 2, 4, 8, workers}) if g <= available]
            else:
                n = 2**22
                slots = max(2, args.l2_bytes // (12 * n) + 1)
                cases = [(n, workers, s, base) for s in [1, slots] for base in [False, True]]
            random.Random(2026).shuffle(cases)
            for case in cases:
                add_case(*case)
            return

        shared_inputs = {}

        def matrix_case(n, tile, pattern, benchmark=False, library=False):
            base = (uint * 3)()
            status = lib.prepare_mm(n, tile, base)
            if status:
                raise ValueError(f"tiling rejected ({status}), returned {list(base)}")
            rng = np.random.default_rng(2026)
            x, y = rng.uniform(-0.5, 0.5, (2, n, n)).astype(np.float16)
            if pattern == "identity":
                x = np.eye(n, dtype=np.float16)
            elif pattern == "zero":
                x.fill(0)
            elif pattern == "precision":
                x.fill(1)
                y.fill(0)
                y[0], y[-1] = 2048, 1  # 2049 is exactly FP32, inexact in FP16.
            elif pattern == "cancellation":
                # A dot product starts at 2048, adds units, then subtracts 2048.
                # FP16 sequential accumulation can lose units near that first term.
                x.fill(1)
                y.fill(1)
                y[0] = 2048
                y[-1] = -2048
            ref = x.astype(np.float64) @ y.astype(np.float64)
            if benchmark and n in shared_inputs:
                a, b, c = shared_inputs[n]
            else:
                a, b = torch.from_numpy(x).to(device), torch.from_numpy(y).to(device)
                c = torch.empty((n, n), device=device, dtype=torch.float32)
                if benchmark:
                    shared_inputs[n] = a, b, c
            c.fill_(float("nan"))
            torch.npu.synchronize()
            library_call = LibraryMatmul(a, b, c, stream_ptr) if library else None
            def launch(_):
                if library:
                    library_call.launch()
                else:
                    lib.launch_mm(a.data_ptr(), b.data_ptr(), c.data_ptr(), workspace.data_ptr(),
                                  n, tile, workers, stream_ptr)
            def verify():
                actual = c.cpu().numpy()
                error = np.abs(actual - ref)
                exact = pattern != "random"
                ok = np.isclose(actual, ref, atol=0 if exact else 1e-3, rtol=0 if exact else 1e-3)
                if not np.all(ok):
                    i, j = np.argwhere(~ok)[0]
                    raise ValueError(f"{pattern} [{i},{j}]: {actual[i,j]} vs {ref[i,j]}")
                return dict(max_abs=float(error.max()), max_rel=float((error / np.maximum(abs(ref), 1e-12)).max()),
                            rel_fro=float(np.linalg.norm(error) / max(np.linalg.norm(ref), 1e-12)))
            launch(0)
            errors = verify()
            fields = dict(n=n, tile=tile, kernel="aclnnMm" if library else "mm_tiles")
            record(kind="check", pattern=pattern, base=None if library else list(base), **fields, **errors)
            if benchmark:
                panels = n // tile
                input_bytes = output_bytes = 0
                for row in range(0, n, tile):
                    for col in range(0, n, tile):
                        for k in range(0, n, base[2]):
                            input_bytes += 2 * (tile * base[2] + base[2] * tile)
                        output_bytes += 4 * tile * tile
                assert input_bytes + output_bytes == 4*n*n*(panels+1)
                measure(launch, verify, 1, **fields, base=None if library else list(base),
                        workers=None if library else workers, flops=2*n**3,
                        logical_bytes=None if library else input_bytes + output_bytes)
            if library_call:
                library_call.close()

        passed = []
        for tile in [32, 64]:
            try:
                for n in [64, 128]:
                    for pattern in ["zero", "identity", "precision", "cancellation", "random"]:
                        matrix_case(n, tile, pattern)
            except ValueError as exc:
                record(kind="M0", tile=tile, passed=False, reason=str(exc))
            else:
                passed.append(tile)
                record(kind="M0", tile=tile, passed=True)
        if not passed:
            raise RuntimeError("M0: no usable output tile")
        if args.stage == "M0":
            return
        if args.stage == "M2" and len(passed) != 2:
            raise RuntimeError("M2 requires both verified output tiles")
        sizes = [n for n in [64, 128, 256, 512, 1024] if n <= args.max_n]
        cases = [(512, tile) for tile in passed] if args.stage == "M2" else [(n, max(passed)) for n in sizes]
        random.Random(2026).shuffle(cases)
        for n, tile in cases:
            matrix_case(n, tile, "random", benchmark=True)
            if args.stage == "M3":
                matrix_case(n, tile, "precision", library=True)
                matrix_case(n, tile, "random", benchmark=True, library=True)


if __name__ == "__main__":
    main()
