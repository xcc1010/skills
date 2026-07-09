# PandaWiki 内网部署 Runbook

目标：在内网用 Docker 部署 PandaWiki，部署后**在控制台填入内部模型 API key + 导入内部文档**即可使用。

> 关键点：PandaWiki 的官方「Docker 版」是一个**安装脚本**（`manager.sh`），它内部用
> Docker Compose 拉起全部服务。**API key 不写进 Docker，而是首次登录在 Web 控制台里配**
> —— 把「对话模型」的 Base URL 指向你们**内网模型网关**，LLM 流量就不出网（契合合规要求）。

---

## 0. 环境要求（官方）

- Linux 主机，**root** 权限
- Docker **20.10.14+**，Docker Compose **2.0.0+**
- 推荐 **2 核 CPU / 4␣GB 内存 / 40␣GB 磁盘**（正式使用建议 4C/8G 起步，向量库+bge 模型吃资源）
- 开放端口 **2443**（管理控制台）；安装器还会暴露门户/Web 端口，**以安装完成时终端打印为准**

---

## 1. 部署（二选一）

### 路径 A：主机能访问外网（或有代理）—— 最简单

在目标 Linux 主机以 root 执行：

```bash
bash -c "$(curl -fsSLk https://release.baizhi.cloud/panda-wiki/manager.sh)"
```

（或直接跑本目录的 `install.sh`，它会先校验 Docker 版本再调用官方安装器。）

安装完成后终端会打印：
- 控制台地址：`http://<主机IP>:2443`
- 默认账号 `admin` + **随机生成的密码**（**当场记下来**）

### 路径 B：内网完全离线（无外网出口）

官方安装器会从 `release.baizhi.cloud` 和镜像仓库拉取，离线环境需要**搬运镜像**：

1. 找一台**同 OS/架构、能上网**的机器，按路径 A 装一遍，让它生成 compose 目录并拉全镜像。
2. 导出镜像与配置：
   ```bash
   docker compose -f <安装器生成的compose路径> config --images | sort -u > images.txt
   xargs -a images.txt docker save -o pandawiki-images.tar
   ```
   同时打包安装器生成的 compose 目录（含 .env、数据初始化等）。
3. 把 `pandawiki-images.tar` + compose 目录拷进内网主机：
   ```bash
   docker load -i pandawiki-images.tar
   docker compose -f <compose路径> up -d
   ```
4. 具体离线步骤以官方「安装升级」文档为准（见文末链接）——**镜像清单以安装器生成的 compose 为准**，不要用手写清单。

> 拿不准就先在一台能上网的测试机跑路径 A 验证通，再按上面导出到内网。

---

## 2. 部署后配置（你的「接 apikey」步骤）

打开 `http://<主机IP>:2443`，用 `admin` + 随机密码登录。首次登录会要求配置 AI 模型：

| 模型角色 | 怎么填 |
|---|---|
| **对话模型（Chat）** | 选「OpenAI 兼容 / DeepSeek / 自定义」→ 填 **Base URL = 你们内网网关地址**、**API Key = 内部 key**、模型名。← **这就是你要的「接 apikey」** |
| **向量模型（Embedding）** | 内置 `bge-m3`，容器自带，**无需外部 key** |
| **重排模型（Rerank）** | 内置 `bge-reranker-v2-m3`，容器自带，**无需外部 key** |

**合规要点**：只要对话模型 Base URL 指向内网网关，问答/搜索的 LLM 调用就**全程走内网、不出网**；向量与重排本来就在本地容器跑。请先确认你们网关是 **OpenAI 兼容**（能正常响应 `/v1/chat/completions`）。

详见 `config-checklist.md`。

---

## 3. 导入文档（你的「接文档」步骤）

控制台里：**创建知识库 → 导入内容**，支持：
- 网页 **URL** 导入
- 网站 **Sitemap** 批量导入
- **RSS** 订阅
- **离线文件**导入（Markdown / Word / PDF 等）

文档在你们内网、我看不到，你按上面任一方式导入即可；导入后 AI 问答/搜索会基于这些文档做 RAG。

---

## 4. 注意事项

- **出网限制**：路径 A 需要主机能访问 `release.baizhi.cloud` 和镜像仓库；被墙就走路径 B 或配代理/镜像加速。**注意区分**：这是「拉安装包/镜像」需要的临时出网，和「运行时 LLM 调用」是两回事——运行时只要指向内网网关就不出网。
- **数据备份**：数据在 Docker 卷里（数据库/对象存储等），上线前定好卷备份策略。
- **License = AGPL-3.0**：内网自用合法；但若你们**修改源码并对外/跨网络提供服务**，AGPL 有开源回馈义务——纯内部用没问题，若要改造上线建议先过一下法务。
- **我没有手写 compose**：官方 compose 由安装器生成、且随版本变化，手写会写错服务/镜像。安装器**就是**官方支持的「Docker 版」。需要我帮你把安装器生成的真实 compose 抠出来做离线包，告诉我一声。

---

## 官方参考
- 仓库：https://github.com/chaitin/PandaWiki
- 文档首页：https://pandawiki.docs.baizhi.cloud/
- 快速上手（新手必读）：https://pandawiki.docs.baizhi.cloud/node/01971650-cb16-7957-96fd-26207f49f264
- 安装升级（含离线）：https://pandawiki.docs.baizhi.cloud/node/01971bb9-86a3-7661-89d2-5c6e5fea741b
