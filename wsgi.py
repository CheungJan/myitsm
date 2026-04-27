"""
WSGI 启动入口。
作者：Cascade
创建时间：2026-03-24
变更时间：2026-03-24
注意事项：生产部署请通过 WSGI Server 调用 app 对象。
"""

from app import create_app

app = create_app()
