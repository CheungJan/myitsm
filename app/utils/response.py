"""统一响应工具。"""

from __future__ import annotations

from typing import Any

from flask import g, jsonify


def success_response(
    data: Any = None,
    message: str = "操作成功",
    code: int = 200,
) -> tuple[Any, int]:
    """返回统一成功响应。"""
    return (
        jsonify(
            {
                "code": code,
                "message": message,
                "data": data,
                "request_id": getattr(g, "request_id", ""),
            }
        ),
        code,
    )


def error_response(
    message: str = "操作失败",
    code: int = 500,
    data: Any = None,
    http_status: int | None = None,
) -> tuple[Any, int]:
    """返回统一错误响应。"""
    status = http_status if http_status is not None else (code if 100 <= code <= 599 else 500)
    return (
        jsonify(
            {
                "code": code,
                "message": message,
                "data": data,
                "request_id": getattr(g, "request_id", ""),
            }
        ),
        status,
    )
