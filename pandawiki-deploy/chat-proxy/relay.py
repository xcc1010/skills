#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
透明转发桥 relay（零依赖，仅 Python3 标准库）

场景:
  Linux(内网/无外网) 装了 PandaWiki，够不到互联网上的模型 API；
  但这台机器(如 Windows) 既能被 Linux 局域网访问、又能上互联网。
  在这台机器上跑本脚本，把 Linux 发来的请求「路径原样」转发到互联网模型。
  （不改写路径，适用于模型本身就是标准 OpenAI 接口的情况）

  Linux(PandaWiki) --LAN--> 本机:PORT --Internet--> UPSTREAM

配置(环境变量):
  UPSTREAM   模型服务的 scheme+host，只到主机名，**不带路径**。
             例如真实地址是 https://xxxx/api/v1/chat/completions，这里填  https://xxxx
  PORT       监听端口，默认 8080
  INSECURE   =1 时跳过 TLS 证书校验(自签名内部证书才需要)

PandaWiki【对话模型】Base URL 填:
  http://<本机局域网IP>:<PORT> + 真实的 base 路径
  例:真实 base 是 https://xxxx/api/v1  →  http://<本机IP>:8080/api/v1
      （PandaWiki 会自动加 /chat/completions，转发后即 https://xxxx/api/v1/chat/completions）
"""
import os, ssl, urllib.parse, http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = os.environ.get("UPSTREAM", "https://CHANGE_ME")
PORT     = int(os.environ.get("PORT", "8080"))
INSECURE = os.environ.get("INSECURE") == "1"

_u    = urllib.parse.urlparse(UPSTREAM)
HTTPS = (_u.scheme == "https")
HOST  = _u.hostname
UPORT = _u.port or (443 if HTTPS else 80)
CTX   = ssl._create_unverified_context() if (HTTPS and INSECURE) else None


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _relay(self, method):
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b""
        try:
            if HTTPS:
                up = http.client.HTTPSConnection(HOST, UPORT, timeout=600, context=CTX)
            else:
                up = http.client.HTTPConnection(HOST, UPORT, timeout=600)
            headers = {}
            for k, v in self.headers.items():
                if k.lower() in ("host", "content-length", "connection",
                                 "keep-alive", "proxy-connection"):
                    continue
                headers[k] = v
            headers["Host"] = HOST
            headers["Content-Length"] = str(len(body))
            up.request(method, self.path, body=body, headers=headers)   # 路径原样透传
            resp = up.getresponse()
        except Exception as e:
            msg = ('{"error":"upstream failed: %s"}' % str(e).replace('"', "'")).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(msg)
            self.close_connection = True
            return

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

    def do_GET(self):  self._relay("GET")
    def do_POST(self): self._relay("POST")
    def log_message(self, *a): pass


if __name__ == "__main__":
    if "CHANGE_ME" in UPSTREAM:
        print("!! 先设置 UPSTREAM(只到主机名,不带路径),例如: UPSTREAM=https://xxxx")
    print(f">> relay 监听 0.0.0.0:{PORT}  ->  {UPSTREAM}   (路径原样透传, INSECURE={INSECURE})")
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
