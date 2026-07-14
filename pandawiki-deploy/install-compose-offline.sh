#!/usr/bin/env bash
# 内网离线安装 Docker Compose v2 插件（单个静态二进制，零依赖）
# PandaWiki 需要 compose 编排 12 个服务，必须先装它。
#
# 用法：
#   1) 在能上网的机器上下载对应架构的二进制：
#        x86_64 : docker-compose-linux-x86_64
#        arm64  : docker-compose-linux-aarch64
#      来源：https://github.com/docker/compose/releases/latest
#   2) 把该文件拷进内网，与本脚本放同目录，重命名为 docker-compose（或用 $1 传路径）
#   3) sudo bash install-compose-offline.sh [docker-compose二进制路径]
set -euo pipefail

BIN="${1:-./docker-compose}"
DEST="/usr/local/lib/docker/cli-plugins/docker-compose"

[ "$(id -u)" -eq 0 ] || { echo "!! 请用 root 运行 (sudo bash $0)"; exit 1; }
[ -f "$BIN" ] || { echo "!! 找不到二进制: $BIN"; echo "   先下载 docker-compose-linux-<arch> 并放到当前目录，或把路径作为参数传入。"; exit 1; }

install -d /usr/local/lib/docker/cli-plugins
install -m 0755 "$BIN" "$DEST"
# 同时软链一个 docker-compose(v1 风格命令)，两种写法都能用
ln -sf "$DEST" /usr/local/bin/docker-compose

echo ">> 安装完成，验证："
docker compose version
echo ">> OK: 'docker compose' 与 'docker-compose' 均可用"
