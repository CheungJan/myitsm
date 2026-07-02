#!/bin/bash
# 重启 Flask 后端和 Vite 前端服务

# 先按端口杀（不管什么进程，占3000的都清掉）
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:5001 | xargs kill -9 2>/dev/null

# 再清残留
pkill -f "flask run"
pkill -f "vite"

# 启动
cd /Users/cheungjan/myitsm && nohup uv run flask run > /tmp/flask.log 2>&1 &
cd /Users/cheungjan/myitsm/frontend && nohup npx vite --host --port 3000 > /tmp/vite.log 2>&1 &

echo "服务已重启，日志："
echo "  Flask: tail -f /tmp/flask.log"
echo "  Vite:  tail -f /tmp/vite.log"
