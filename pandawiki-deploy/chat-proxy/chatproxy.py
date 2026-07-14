#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI 兼容「路径改写」反向代理（零依赖，仅 Python3 标准库）

用途:
  你内网大模型网关是 OpenAI 兼容的(请求 {model,messages}、返回 {choices:[...]}),
  但对话端点在自定义路径(如 http://网关/api/),没有 /v1/chat/completions。
  PandaWiki 只会往 {BaseURL}/chat/completions 发,对不上。
  本代理把  POST /v1/chat/completions  转发到你网关的真实地址,并透传流式响应。

配置(环境变量):
  GATEWAY_URL  你网关能调通的完整地址,例如  http://10.0.0.5:8000/api/   (必填)
  MODEL        供 /v1/models 探测返回用的模型名(PandaWiki 测试连接时可能会查)
  PORT         监听端口,默认 8080

PandaWiki 里【对话模型】填:
  Base URL = http://<本机IP>:<PORT>/v1
  模型名   = 你的模型
  API Key  = 你网关的 key(会被原样透传到网关)

注意: embedding / rerank 不走这里,直接指向 Xinference 的 http://<xinf>:9997/v1 。
"""
import os, urllib.parse, http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

GATEWAY = os.environ.get("GATEWAY_URL", "http://CHANGE_ME/api/")
MODEL   = os.environ.get("MODEL", "default")
PORT    = int(os.environ.get("PORT", "8080"))

_gw     = urllib.parse.urlparse(GATEWAY)
GW_HTTPS = (_gw.scheme == "https")
GW_HOST  = _gw.hostname
GW_PORT  = _gw.port or (443 if GW_HTTPS else 80)
GW_PATH  = _gw.path or "/"          # 你网关的真实路径,如 /api/


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _json(self, code, text):
        b = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        self.wfile.write(b)

    def do_GET(self):
        # 连接测试常探测 /v1/models,给个静态返回避免测试失败
        if self.path.rstrip("/").endswith("/models"):
            return self._json(200,
                '{"object":"list","data":[{"id":"%s","object":"model","owned_by":"local"}]}' % MODEL)
        return self._json(404, '{"error":"not found"}')

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b""

        Conn = http.client.HTTPSConnection if GW_HTTPS else http.client.HTTPConnection
        try:
            up = Conn(GW_HOST, GW_PORT, timeout=600)
            headers = {"Host": self.headers.get("Host", GW_HOST)}
            for k in ("Content-Type", "Authorization", "Accept"):
                v = self.headers.get(k)
                if v:
                    headers[k] = v
            headers["Content-Length"] = str(len(body))
            up.request("POST", GW_PATH, body=body, headers=headers)  # -> 你网关真实路径
            resp = up.getresponse()
        except Exception as e:
            return self._json(502, '{"error":"upstream failed: %s"}' % str(e).replace('"', "'"))

        # 透传状态与响应头,用「读到 EOF 即结束 + 关闭连接」实现流式(SSE)透传
        self.send_response(resp.status)
        for k, v in resp.getheaders():
            if k.lower() in ("transfer-encoding", "connection", "content-length", "keep-alive"):
                continue
            self.send_header(k, v)
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        try:
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        finally:
            up.close()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    if "CHANGE_ME" in GATEWAY:
        print("!! 请先设置 GATEWAY_URL, 例如: GATEWAY_URL=http://10.0.0.5:8000/api/ python3 chatproxy.py")
    print(f">> chat-proxy 监听 :{PORT}  ->  {GATEWAY}   (models 探测返回 model={MODEL})")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
