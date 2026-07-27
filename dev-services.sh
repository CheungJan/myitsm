#!/bin/bash
# 开发模式启动 Flask 后端和 Vite 前端服务
# Flask 开启 debug/reloader；不使用 nohup，终端关闭后服务结束。

# 先按端口杀（不管什么进程，占3000/5001的都清掉）
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:5001 | xargs kill -9 2>/dev/null

# 再清残留
pkill -f "flask run"
pkill -f "vite"

# 启动 Flask 开发模式（后台，保留 debug/reloader）
cd /Users/cheungjan/myitsm && FLASK_DEBUG=1 uv run flask run &
FLASK_PID=$!

# 启动 Vite 开发服务（前台，便于查看日志）
cd /Users/cheungjan/myitsm/frontend && npx vite --host --port 3000

# Vite 退出后同步结束 Flask 后台进程
kill "$FLASK_PID" 2>/dev/null
