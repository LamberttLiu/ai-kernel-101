#!/usr/bin/env bash

# 执行方式：
# bash lab/hello-world/verify.sh cpu|sim|npu [source-directory]
# 例如：
# bash lab/hello-world/verify.sh cpu
# bash lab/hello-world/verify.sh sim
# bash lab/hello-world/verify.sh npu /path/to/sample

# Resolve the requested run mode and sample source.
set -eo pipefail
mode=${1:?Specify cpu, sim, or npu}
case "$mode" in cpu | sim | npu) ;; *)
    echo "Invalid mode: $mode" >&2
    exit 2
    ;;
esac
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
sample=${2:-"$repo/src/hello_world"}

# Load the CANN environment and create a workspace for verification evidence.
if [[ -n ${CANN_ENV:-} ]]; then
    source "$CANN_ENV"
else
    for candidate in "$HOME/Ascend/cann/set_env.sh" \
        "$HOME/Ascend/ascend-toolkit/set_env.sh" \
        /usr/local/Ascend/ascend-toolkit/set_env.sh; do
        if [[ -f "$candidate" ]]; then
            source "$candidate"
            break
        fi
    done
fi
set -u
arch=${HELLO_ARCH:-dav-2201}
work=$(mktemp -d "/tmp/hello-world-${mode}.XXXXXX")
exec > >(tee "$work/session.txt") 2>&1

# Record host, compiler, and CANN installation details.
echo "=== Environment ==="
date -Iseconds
uname -m
grep -E '^(PRETTY_NAME|VERSION_ID)=' /etc/os-release
echo "mode=$mode arch=$arch sample=$sample work=$work"
echo "CANN=${ASCEND_HOME_PATH:-unset}"
ccec --version
cmake --version | head -1
if [[ -n ${ASCEND_HOME_PATH:-} ]]; then
    while IFS= read -r info; do
        echo "install_info=$info"
        grep -Ei '^(version|arch|os|install_type|package_type)=' "$info" || true
    done < <(find -L "$ASCEND_HOME_PATH" -maxdepth 3 -name '*install.info' -type f 2>/dev/null)
fi

# Check device visibility and ACL runtime initialization for NPU runs.
if [[ "$mode" == npu ]]; then
    npu-smi info
    python3 - <<'PY'
import ctypes
acl = ctypes.CDLL('libascendcl.so')
acl.aclrtGetSocName.restype = ctypes.c_char_p
for name, args in [('aclInit', (None,)), ('aclrtSetDevice', (0,))]:
    result = getattr(acl, name)(*args)
    print(f'probe_{name}={result}', flush=True)
    if result:
        raise SystemExit(1)
print('runtime_soc=' + str(acl.aclrtGetSocName().decode()), flush=True)
for name, args in [('aclrtResetDevice', (0,)), ('aclFinalize', ())]:
    result = getattr(acl, name)(*args)
    print(f'probe_{name}={result}', flush=True)
    if result:
        raise SystemExit(1)
PY
fi

# Allow environment-only checks to exit before build and execution.
if [[ ${HELLO_PROBE_ONLY:-0} == 1 ]]; then exit 0; fi

# Configure and build the sample, then require exactly one demo executable.
echo "=== Build ==="
cmake -S "$sample" -B "$work/build" \
    -DCMAKE_ASC_RUN_MODE="$mode" -DCMAKE_ASC_ARCHITECTURES="$arch"
cmake --build "$work/build" --parallel 4
mapfile -t binaries < <(find "$work/build" -type f -name demo -executable)
if [[ ${#binaries[@]} != 1 ]]; then
    echo 'Expected exactly one demo binary' >&2
    exit 2
fi
echo "binary=${binaries[0]}"
mkdir "$work/run"
cd "$work/run"

# Run the executable and preserve its output and process status.
echo "=== Run ==="
set +e
timeout 120s "${binaries[0]}" >"$work/run.txt" 2>&1
run_exit=$?
set -e
cat "$work/run.txt"
echo "process_exit=$run_exit"

# Validate block output, ACL lifecycle calls, and simulator shutdown when applicable.
echo "=== Check ==="
python3 - "$work/run.txt" "$run_exit" "$mode" <<'PY'
import collections
import re
import sys
text = open(sys.argv[1], encoding='utf-8', errors='replace').read()
blocks = collections.Counter(map(int, re.findall(r'\[Block \((\d+)/8\)\]: Hello World!!!', text)))
stages = ['aclInit', 'aclrtSetDevice', 'aclrtCreateStream', 'aclrtSynchronizeStream',
          'aclrtDestroyStream', 'aclrtResetDevice', 'aclFinalize']
missing = [s for s in stages if f'[HOST][OK] {s}: ret=0' not in text]
passed = blocks == collections.Counter(range(8)) and not missing and '[HOST][ERROR]' not in text and int(sys.argv[2]) == 0
if sys.argv[3] == 'sim':
    model_stopped = '[INFO] Model stopped successfully.' in text
    print('model_stopped=' + str(model_stopped))
    passed = passed and model_stopped
print('block_counts=' + str(dict(sorted(blocks.items()))))
print('missing_acl_stages=' + str(missing))
print('verification=' + ('PASS' if passed else 'FAIL'))
sys.exit(0 if passed else 1)
PY

# Print the path containing the complete captured evidence.
echo "Full temporary evidence: $work"
