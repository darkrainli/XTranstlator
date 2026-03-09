#!/usr/bin/env python3
"""
Lumina Translate — 本地代理服务器
解决浏览器 CORS 限制，将翻译请求转发给 GLM / Qwen API
"""
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

PORT = 8765
API_URLS = {
    "glm":  "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
}

class ProxyHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # only log errors, suppress 200 noise
        if args and str(args[1]) not in ("200", "304"):
            print(f"  {args[0]}  {args[1]}")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/proxy":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)

        try:
            payload = json.loads(body)
        except Exception:
            self._json(400, {"error": "Invalid JSON"})
            return

        provider = payload.pop("_provider", "glm")
        api_key  = payload.pop("_api_key", "")
        api_url  = API_URLS.get(provider, API_URLS["glm"])

        if not api_key:
            self._json(400, {"error": "API key is empty"})
            return

        req_body = json.dumps(payload).encode()
        req = urllib.request.Request(
            api_url,
            data=req_body,
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent":    "LuminaTranslate/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
                self._json_raw(resp.status, data)
        except urllib.error.HTTPError as e:
            data = e.read()
            print(f"  API error {e.code}: {data[:300]}")
            self._json_raw(e.code, data)
        except Exception as e:
            print(f"  Proxy error: {e}")
            self._json(502, {"error": str(e)})

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self._json_raw(code, data)

    def _json_raw(self, code, data):
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type",   "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(("localhost", PORT), ProxyHandler)
    print(f"\n  Lumina Translate 已启动")
    print(f"  ─────────────────────────────────────")
    print(f"  请用浏览器打开：http://localhost:{PORT}/translator.html")
    print(f"\n  按 Ctrl+C 停止服务器\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  服务器已停止")
