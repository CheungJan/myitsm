# -*- coding: utf-8 -*-
"""
统一响应工具函数。
提供 { code, message, data } 标准响应结构。
"""

from typing import Any, Dict


def success_response(data: Any = None, message: str = "操作成功", code: int = 200) -> Dict[str, Any]:
    """
    成功响应。

    Args:
        data: 响应数据
        message: 响应消息
        code: 响应码（默认 200）

    Returns:
        统一格式的响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data,
    }


def error_response(message: str = "操作失败", code: int = 500, data: Any = None) -> Dict[str, Any]:
    """
    错误响应。

    Args:
        message: 错误消息
        code: 错误码（默认 500）
        data: 附加数据（可选）

    Returns:
        统一格式的响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data,
    }
