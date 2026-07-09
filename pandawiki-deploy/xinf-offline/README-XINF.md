# 离线 Embedding + Rerank (Xinference CPU) —— 给 PandaWiki 用

镜像+模型权重(bge-m3 / bge-reranker-v2-m3)已烤进本包, 内网无需联网。
注意: 未在打包机上做加载自测(打包 VM 内存不足), 请在内网主机首次部署时验证。

## 前置
- x86-64 Linux + Docker + compose v2
- 建议 >= 8GB 内存 (两个 bge 模型 CPU 加载需要内存)

## 部署
    sudo sh deploy-offline.sh
- 向量: http://<本机IP>:9997/v1/embeddings   模型 bge-m3
- 重排: http://<本机IP>:9997/v1/rerank        模型 bge-reranker-v2-m3

## 在 PandaWiki 控制台
- 向量模型: Base URL=http://<本机IP>:9997/v1 , 模型=bge-m3 , API Key 任意
- 重排模型: Base URL=http://<本机IP>:9997/v1 , 模型=bge-reranker-v2-m3
- 对话模型仍填你们内网 LLM 网关

## 注意
- CPU 推理, 索引量大时偏慢。
- 主机重启后模型不自动加载, 需重跑 deploy-offline.sh 的两条 launch (可做 systemd)。
