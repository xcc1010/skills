#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
透明转发桥 relay（零依赖，仅 Python3 标准库）—— 多路由版

场景:
  Linux(内网/无外网) 装了 PandaWiki，够不到某些地址(互联网模型、内网博客…)；
  但这台机器(如 Windows) 既能被 Linux 局域网访问、又能访问那些地址。
  在这台机器上跑本脚本，按「路径前缀」把 Linux 发来的请求分流转发到不同目标。

  一个脚本 / 一个端口 / 一条防火墙规则，同时桥接多个后端:
    Linux ──LAN──> 本机:PORT ──►  /model/... 转发到模型主机
                                   /blog/...  转发到博客主机

用法(以 PandaWiki / 采集为例):
  真实地址            http://本机IP:PORT<前缀> 后面接真实路径
  模型 base https://m.com/api/v1     ->  http://本机IP:8080/model/api/v1
  博客文章 http://b.com/post/123     ->  http://本机IP:8080/blog/post/123
  即: 把「协议+主机」换成「http://本机IP:PORT + 前缀」，后面路径不动。
"""
import os, ssl, urllib.parse, http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ============================ 直接改这里 ============================
# 路由表:  "路径前缀" : "目标 协议+主机(只到主机名,不带路径)"
#   想加更多后端,照着再加一行即可。
ROUTES = {
    "/model": "https://CHANGE_ME_MODEL",   # 对话 / 文档分析模型
    "/blog":  "http://CHANGE_ME_BLOG",     # 内网/外网博客
}
PORT     = 8080          # 监听端口(所有后端共用这一个)
INSECURE = False         # 目标是自签名 https 证书、报 SSL 错时改成 True
# ==================================================================
# (可选)环境变量覆盖: PORT / INSECURE / ROUTE_model / ROUTE_blog ...
PORT     = int(os.environ.get("PORT", PORT))
INSECURE = (str(os.environ.get("INSECURE", "1" if INSECURE else "0")) == "1")
for k in list(ROUTES):
    ev = os.environ.get("ROUTE_" + k.lstrip("/"))
    if ev:
        ROUTES[k] = ev


def _parse(u):
    p = urllib.parse.urlparse(u)
    https = (p.scheme == "https")
    return {
        "https": https,
        "host":  p.hostname,
        "port":  p.port or (443 if https else 80),
        "base":  p.path.rstrip("/"),   # 一般为空;若填了路径会拼在前面
    }

TARGETS = {prefix: _parse(url) for prefix, url in ROUTES.items()}


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _err(self, code, text):
        b = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(b)
        self.close_connection = True

    def _pick(self):
        # 最长前缀匹配
        for prefix in sorted(TARGETS, key=len, reverse=True):
            if self.path == prefix or self.path.startswith(prefix + "/"):
                remaining = self.path[len(prefix):] or "/"
                return prefix, remaining
        return None, None

    def _relay(self, method):
        prefix, remaining = self._pick()
        if prefix is None:
            return self._err(404, '{"error":"no route for %s (可用前缀: %s)"}'
                             % (self.path, ", ".join(TARGETS)))
        t = TARGETS[prefix]
        fwd_path = (t["base"] + remaining) or "/"

        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b""
        try:
            if t["https"]:
                ctx = ssl._create_unverified_context() if INSECURE else None
                up = http.client.HTTPSConnection(t["host"], t["port"], timeout=600, context=ctx)
            else:
                up = http.client.HTTPConnection(t["host"], t["port"], timeout=600)
            headers = {}
            for k, v in self.headers.items():
                if k.lower() in ("host", "content-length", "connection",
                                 "keep-alive", "proxy-connection"):
                    continue
                headers[k] = v
            headers["Host"] = t["host"]
            headers["Content-Length"] = str(len(body))
            up.request(method, fwd_path, body=body, headers=headers)
            resp = up.getresponse()
        except Exception as e:
            return self._err(502, '{"error":"upstream failed: %s"}'
                             % str(e).replace('"', "'"))

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
    def do_PUT(self):  self._relay("PUT")
    def log_message(self, *a): pass


if __name__ == "__main__":
    print(f">> relay 监听 0.0.0.0:{PORT}   (INSECURE={INSECURE})")
    for prefix, url in ROUTES.items():
        flag = "  <-- 待填!" if "CHANGE_ME" in url else ""
        print(f"   {('http://本机IP:%d' % PORT)+prefix:<28} ->  {url}{flag}")
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
