# 本脚本在项目根目录下运行

# 先执行实际安装路径下的脚本，按照环境配置
source /home/developer/Ascend/cann/set_env.sh

set -e
set -o pipefail

record="$PWD/lab/hello_world/results/npu-build"
mkdir -p "$record"
printf '==== Record Dir: %s ====\n' "$record"
printf '==== Start configure and build ====\n'

cmake -S "$PWD/lab/hello_world/src" -B "$record/build" \
  -DCMAKE_ASC_RUN_MODE=npu -DCMAKE_ASC_ARCHITECTURES=dav-2201 \
  2>&1 | tee "$record/configure.log"

cmake --build "$record/build" --verbose --parallel 1 2>&1 | tee "$record/build.log"

./lab/hello_world/results/npu-build/build/demo 2>&1 | tee "$record/run.log"