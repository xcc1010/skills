# chat-proxy —— 给「非标准路径」的内网网关套一层 OpenAI 兼容外壳

## 解决什么问题

你的内网大模型网关是 **OpenAI 兼容**(请求 `{model,messages}`、返回 `{choices:[{message:{content}}]}`),
但对话端点在**自定义路径**,例如 `http://网关/api/`,**没有** `/v1/chat/completions`。

PandaWiki(以及所有 OpenAI 兼容客户端)只会往 `{BaseURL}/chat/completions` 发请求,
所以直接填网关地址对不上。本代理做一次**路径改写**:

```
PandaWiki --> http://<代理>:8080/v1/chat/completions --> [代理] --> http://网关/api/
```

body 和返回原样透传(含流式 SSE),只改路径。

---

## 一、启动代理(两种方式，任选其一)

先确认你网关**能 curl 通的完整地址**,记为 `GATEWAY_URL`(必须带到 `/api/` 那一层)。

### 方式 A：主机有 python3(最简单)

```bash
GATEWAY_URL=http://10.0.0.5:8000/api/  MODEL=你的模型名  PORT=8080 \
  python3 chatproxy.py
# 后台常驻可用: nohup ... >proxy.log 2>&1 &   或做成 systemd
```

### 方式 B：用容器跑(复用已 load 的 Xinference 镜像，无需装 python)

```bash
docker run -d --name chat-proxy --restart always -p 8080:8080 \
  -e GATEWAY_URL=http://10.0.0.5:8000/api/ \
  -e MODEL=你的模型名 \
  -v "$(pwd)/chatproxy.py:/chatproxy.py:ro" \
  xprobe/xinference:latest-cpu  python3 /chatproxy.py
```

> `GATEWAY_URL` 换成你真实网关地址;`MODEL` 换成你要用的模型名。

---

## 二、自测代理是否通

```bash
# 走代理调对话(应返回和直连网关一样的 JSON)
curl http://127.0.0.1:8080/v1/chat/completions \
  -H "Authorization: Bearer 你的key" \
  -H "Content-Type: application/json" \
  -d '{"model":"你的模型名","messages":[{"role":"user","content":"你好"}]}'

# 探测 models(PandaWiki 测试连接会用到)
curl http://127.0.0.1:8080/v1/models
```

通了再去配 PandaWiki。

---

## 三、PandaWiki 控制台【对话模型】填法

| 字段 | 值 |
|---|---|
| Base URL | `http://<代理机器IP>:8080/v1`  ← 注意末尾是 `/v1`,不带 `/`,不带 `chat/completions` |
| 模型名 | 你的模型名（与上面 `MODEL` 一致） |
| API Key | 你网关的 key（代理会原样透传给网关） |

> embedding / rerank **不走本代理**,仍直接指向 Xinference:`http://<xinf机器IP>:9997/v1`。

---

## 常见问题

- **PandaWiki 测试连接失败但 curl 能通**:多半是它探测 `/v1/models`。本代理已返回静态
  model 列表(取 `MODEL` 值),确保 `MODEL` 和你在 PandaWiki 填的模型名**一致**。
- **代理容器连不到网关**:确认容器能访问内网网关 IP(同网段/路由可达);必要时
  给 `docker run` 加 `--add-host` 或用 `--network host`。
- **流式无输出/超时**:本代理用「读到 EOF + 关闭连接」透传流式,通常无需额外配置;
  若你网关本身不支持流式,在 PandaWiki 里关掉流式即可。
- **返回不是 OpenAI 格式**(比如 `{result:...}` 而非 `{choices:...}`):那就不是情况①,
  需要做「字段转换」的适配器,找我加。
