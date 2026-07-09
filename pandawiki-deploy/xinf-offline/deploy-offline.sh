#!/bin/sh
set -e
cd "$(dirname "$0")"
command -v docker >/dev/null 2>&1 || { echo "!! 需要 docker + compose v2"; exit 1; }
echo ">> load image (~10GB, 几分钟)"; docker load -i xinference-image.tar
[ -d cache ] || { echo ">> 解开模型缓存(~7GB)"; tar xzf xinference-cache.tar.gz; }
echo ">> 启动 xinference"; docker compose up -d
echo ">> 等待就绪"; for i in $(seq 1 72); do curl -fsS http://127.0.0.1:9997/v1/models >/dev/null 2>&1 && break; sleep 5; done
echo ">> 从本地缓存加载模型(离线, 需要主机 >=6GB 内存)"
docker exec xinference env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 xinference launch --model-name bge-m3 --model-type embedding
docker exec xinference env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 xinference launch --model-name bge-reranker-v2-m3 --model-type rerank
echo ">> OK"
echo "   向量: http://<本机IP>:9997/v1/embeddings   model=bge-m3"
echo "   重排: http://<本机IP>:9997/v1/rerank        model=bge-reranker-v2-m3"
echo ">> 注意: 主机/容器重启后需重跑本脚本的两条 launch (xinference 不自动重载)"
