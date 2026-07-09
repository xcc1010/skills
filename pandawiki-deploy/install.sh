#!/usr/bin/env bash
# PandaWiki 内网部署助手 —— 校验环境后调用官方安装器。
# 用法（目标 Linux 主机，root）：  sudo bash install.sh
set -euo pipefail

OFFICIAL="https://release.baizhi.cloud/panda-wiki/manager.sh"

echo "== PandaWiki 部署前检查 =="

# 1) root
if [ "$(id -u)" -ne 0 ]; then
  echo "!! 请用 root 运行（sudo bash install.sh）"; exit 1
fi

# 2) Docker
if ! command -v docker >/dev/null 2>&1; then
  echo "!! 未检测到 docker，请先安装 Docker 20.10.14+"; exit 1
fi
DOCKER_V="$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo '0')"
echo "   docker server: ${DOCKER_V}"

# 3) Docker Compose v2
if docker compose version >/dev/null 2>&1; then
  echo "   compose: $(docker compose version --short 2>/dev/null || echo '?')"
else
  echo "!! 未检测到 'docker compose' (v2)，请安装 Docker Compose 2.0.0+"; exit 1
fi

# 4) 连通性提示（不阻塞：离线环境请改用 README 的路径 B）
if ! curl -fsSLkI "${OFFICIAL}" >/dev/null 2>&1; then
  echo "!! 无法访问 ${OFFICIAL}"
  echo "   —— 说明主机没有到 baizhi.cloud 的出网。请改用 README.md 的【路径 B：离线部署】。"
  exit 2
fi

echo
echo "== 环境 OK，调用官方安装器 =="
echo "   安装完成后请记下终端打印的：控制台地址(2443) / admin 密码"
echo
bash -c "$(curl -fsSLk "${OFFICIAL}")"

cat <<'NEXT'

================= 下一步 =================
1) 浏览器打开  http://<本机IP>:2443 ，用 admin + 随机密码登录
2) 首次登录配置【对话模型】：
     Base URL = 你们内网模型网关（OpenAI 兼容）
     API Key  = 内部 key
     模型名   = 网关上的模型
   （向量 bge-m3 / 重排 bge-reranker-v2-m3 已内置，无需外部 key）
3) 创建知识库 → 导入内容（URL / Sitemap / RSS / 离线文件）
详见 README.md 与 config-checklist.md
=========================================
NEXT
