---
description: 在 WSL2 的 Ubuntu 环境中安装 CANN 9.1.0，并确认当前环境已正确加载对应的 Ascend C 工具链。
creat_time: 2026-11-20
last_edit_time: 2026-11-20
---


本地执行环境与目标版本：

- WSL2，Ubuntu 24.04.4 LTS，x86_64架构。
- CMake 3.28.3
- 目标安装版本为 CANN Toolkit 与 910B ops 9.1.0

# 1. 确认 WSL 和主机架构

在 Windows PowerShell 执行 `wsl -l -v`。需要新装发行版时，先用 `wsl --list --online` 核对名称，再在管理员 PowerShell 执行 `wsl --install -d Ubuntu-24.04`，按提示完成初始化。 参考链接：[Microsoft WSL 安装说明](https://learn.microsoft.com/en-us/windows/wsl/install)

后续命令在 Ubuntu 的 Bash 中执行。`uname -m` 应显示 `x86_64`。官方要求安装位置有超过 10 GB 可用空间。 参考链接：[CANN 安装说明](https://www.hiascend.com/doc_center/source/en/CANNCommunityEdition/910/softwareinst/instg/instg_0054.html)

```bash
uname -m
cat /etc/os-release
df -h "$HOME"
sudo apt update
sudo apt install build-essential cmake python3 python3-pip
```

预期结果：
- `wsl -l -v` 中 Ubuntu 对应的 `VERSION` 为 `2`。
- Ubuntu Bash 中，`uname -m` 输出 `x86_64`，`/etc/os-release` 显示 Ubuntu 24.04 LTS，`df -h "$HOME"` 显示安装位置的剩余空间。

APT 更新完成后，四项依赖应显示已安装或已是最新版本。

# 2. 安装 Toolkit 和 910B ops

把两个安装包下载到同一目录。下面以 WSL 内的 `$HOME/Downloads/cann-9.1.0` 为例，执行前把 `package_dir` 改成实际存放位置。如果从 Windows 下载目录直接读取安装包，使用 WSL 路径，例如 `/mnt/c/Users/你的用户名/Downloads`。`x86_64` 对应 WSL 的主机架构，`910b` 标识所安装的 910B ops 包。以同一个普通用户先安装 Toolkit，再安装同版本 ops，默认安装到 `$HOME/Ascend`。若机器已有 CANN，先查明现有版本与安装位置。 参考链接：[昇腾下载中心](https://www.hiascend.com/developer/download/cann) · [CANN 9.1.0 安装命令](https://www.hiascend.com/doc_center/source/en/CANNCommunityEdition/910/softwareinst/instg/instg_0008.html)

```bash
package_dir="$HOME/Downloads/cann-9.1.0"
toolkit=Ascend-cann-toolkit_9.1.0_linux-x86_64.run
ops=Ascend-cann-910b-ops_9.1.0_linux-x86_64.run

# 子命令执行检查和安装
(
  cd "$package_dir" &&
  bash "./$toolkit" --check &&
  bash "./$ops" --check &&
  bash "./$toolkit" --install &&
  bash "./$ops" --install
)
```

`./` 由 `cd` 后的目录解析。切换目录和两项完整性检查都通过后才开始安装，命令块结束后回到原目录。安装程序出现华为最终用户许可协议（EULA）时，在 WSL 终端点接受。工具包安装成功后，命令块才会继续安装 910B ops。

预期结果：

- 两个安装包均通过完整性检查。随后 Toolkit 和 910B ops 依次安装并成功退出。
- 使用普通用户的默认路径时，安装后可在 `$HOME/Ascend/cann/` 找到 `set_env.sh`。

# 3. 加载环境并验收

在用于编译的 Bash 中加载 `set_env.sh`。使用自定义安装目录时换成实际脚本路径。新开终端需要重新加载。 参考链接：[CANN 环境变量说明](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/maintenref/envvar/envref_07_0003.html)

```bash
source "$HOME/Ascend/cann/set_env.sh"
printf 'ASCEND_HOME_PATH=%s\n' "$ASCEND_HOME_PATH"
command -v ccec
ccec --version
cmake --version
find -L "$ASCEND_HOME_PATH" -maxdepth 3 -name '*install.info' -type f \
  -exec grep -HE '^(version|arch)=' {} +
```

预期结果：

- `ASCEND_HOME_PATH` 指向所选安装，`command -v ccec` 显示的编译器来自同一套工具链，`ccec --version` 和 `cmake --version` 能正常输出版本。
- Toolkit 与 ops 的安装信息均应显示 `9.1.0` 和 `x86_64`。

本机执行输出如下，用户主目录统一写为 `$HOME`。

```text
ASCEND_HOME_PATH=$HOME/Ascend/cann-9.1.0
$HOME/Ascend/cann-9.1.0/bin/ccec
2026-07-30T20:53:21+08:00 clang version 15.0.5 (clang-5c68a1cb1231 flang-5c68a1cb1231)
Target: x86_64-unknown-linux-gnu
Thread model: posix
InstalledDir: $HOME/Ascend/cann-9.1.0/bin
cmake version 3.28.3

CMake suite maintained and supported by Kitware (kitware.com/cmake).
$HOME/Ascend/cann-9.1.0/x86_64-linux/ascend_ops_install.info:version=9.1.0
$HOME/Ascend/cann-9.1.0/x86_64-linux/ascend_ops_install.info:arch=x86_64
$HOME/Ascend/cann-9.1.0/x86_64-linux/ascend_toolkit_install.info:version=9.1.0
$HOME/Ascend/cann-9.1.0/x86_64-linux/ascend_toolkit_install.info:arch=x86_64
```

