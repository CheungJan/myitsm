"""健康检查接口。"""

from __future__ import annotations

from flask import Blueprint

from app.utils.response import success_response

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():  # type: ignore[no-untyped-def]
    """健康检查。"""
    return success_response(data={"status": "ok"}, message="服务正常")
