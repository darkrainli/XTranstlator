#!/bin/bash
# 一键启动本地服务器，解决浏览器 CORS 限制
cd "$(dirname "$0")"
PORT=8765
echo ""
echo "  Lumina Translate — 本地服务器"
echo "  ──────────────────────────────────────"
echo "  启动成功后，请用浏览器打开："
echo ""
echo "    http://localhost:$PORT/translator.html"
echo ""
echo "  按 Ctrl+C 停止服务器"
echo ""
python3 server.py
