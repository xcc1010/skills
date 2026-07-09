#!/usr/bin/env bash
# 在【能上网的 SUSE VM】上以 root 运行，产出可搬进内网的离线包。
# 用法:
#   sudo bash build-offline-bundle.sh --prep      # 首次: 安装/启动 docker
#   sudo bash build-offline-bundle.sh             # 打包
set -euo pipefail

OUTDIR="${OUTDIR:-$HOME/pandawiki-offline}"
INSTALLER="https://release.baizhi.cloud/panda-wiki/manager.sh"

# ---- 可选: 在 SUSE 上装 docker + compose ----
if [ "${1:-}" = "--prep" ]; then
  echo ">> 安装 docker / docker-compose (zypper)…"
  zypper --non-interactive install docker docker-compose || true
  systemctl enable --now docker
  docker version
  docker compose version || docker-compose version
  echo ">> prep 完成，请重新运行(不带 --prep)开始打包。"
  exit 0
fi

command -v docker >/dev/null || { echo "!! 没有 docker，先跑: sudo bash $0 --prep"; exit 1; }
systemctl is-active --quiet docker || systemctl start docker
mkdir -p "$OUTDIR"

# ---- 1. 跑官方安装器: 拉取正确镜像 + 生成 compose ----
echo ">> 运行官方安装器(会联网拉镜像，可能需要交互确认)…"
bash -c "$(curl -fsSLk "$INSTALLER")"

# ---- 2. 定位 compose 工程 ----
echo ">> 定位 compose 文件…"
CFG=""
if docker compose ls --format json >/tmp/_cl.json 2>/dev/null; then
  CFG=$(python3 - <<'PY' 2>/dev/null || true
import json,sys
try:
    d=json.load(open('/tmp/_cl.json'))
    print(d[0].get('ConfigFiles','') if d else '')
except Exception:
    print('')
PY
)
fi
[ -z "$CFG" ] && CFG=$(find / -maxdepth 7 \( -iname 'docker-compose*.y*ml' -o -iname 'compose.y*ml' \) 2>/dev/null | grep -i -m1 panda || true)
echo "   compose = ${CFG:-<未找到, 将回退保存全部镜像>}"

# ---- 3. 收集镜像清单 ----
if [ -n "$CFG" ]; then
  mapfile -t IMAGES < <(docker compose -f "$CFG" config --images 2>/dev/null | sort -u)
  mkdir -p "$OUTDIR/compose"; cp -a "$(dirname "$CFG")/." "$OUTDIR/compose/"
else
  mapfile -t IMAGES < <(docker images --format '{{.Repository}}:{{.Tag}}' | grep -v '<none>' | sort -u)
fi
[ "${#IMAGES[@]}" -eq 0 ] && { echo "!! 没有可保存的镜像，安装器可能没拉成功"; exit 1; }
printf '%s\n' "${IMAGES[@]}" | tee "$OUTDIR/images.txt"

# ---- 4. 保存镜像(大步骤) ----
echo ">> docker save 打包镜像(体积大，耐心等)…"
docker save "${IMAGES[@]}" -o "$OUTDIR/pandawiki-images.tar"

# ---- 5. 生成内网侧一键部署脚本 ----
cat > "$OUTDIR/deploy-offline.sh" <<'EOS'
#!/usr/bin/env bash
# 在【内网、离线】主机以 root 运行: 加载镜像并启动
set -euo pipefail
cd "$(dirname "$0")"
command -v docker >/dev/null || { echo "内网主机需已装 docker + compose(可离线 rpm 安装)"; exit 1; }
echo ">> 加载镜像…"; docker load -i pandawiki-images.tar
CFG=$(find ./compose \( -iname 'docker-compose*.y*ml' -o -iname 'compose.y*ml' \) 2>/dev/null | head -1)
[ -z "$CFG" ] && { echo "!! 未找到 compose 文件"; exit 1; }
echo ">> 启动: $CFG"; docker compose -f "$CFG" up -d
echo ">> 完成。打开 http://<本机IP>:2443 用 admin 登录，再配置内网模型 Base URL/API Key、导入文档。"
EOS
chmod +x "$OUTDIR/deploy-offline.sh"

# ---- 6. 打成一个 tar.gz ----
echo ">> 打包整个离线包…"
tar czf "${OUTDIR}.tar.gz" -C "$(dirname "$OUTDIR")" "$(basename "$OUTDIR")"
echo
echo "================ 完成 ================"
echo "离线包: ${OUTDIR}.tar.gz"
echo "搬进内网后: 解压 → sudo bash deploy-offline.sh"
echo "(内网主机需预先装好 docker+compose；没有的话也用离线 rpm 装)"
echo "====================================="
