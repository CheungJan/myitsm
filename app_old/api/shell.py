"""
主框架菜单 API。
作者：Cascade
创建时间：2026-03-24
变更时间：2026-03-24
注意事项：仅负责协议转换与返回组装，不承载业务逻辑。
"""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from app.services.shell_service import ShellService

__all__ = ["shell_bp"]

shell_bp = Blueprint("shell", __name__)
_service = ShellService()


def _bad_request(message: str):
    """
    生成统一 400 响应。

    参数：
        message: 错误提示。

    返回值：
        tuple[Response, int]: 统一结构响应。
    """
    payload = {
        "code": 400,
        "message": message,
        "data": {
            "request_id": getattr(g, "request_id", ""),
        },
    }
    return jsonify(payload), 400


@shell_bp.get("/menus")
def get_menus():
    """
    获取主框架菜单树。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        GET /api/v1/menus
    """
    user_id = request.args.get("user_id", "")
    if user_id.strip() == "":
        return _bad_request("缺少参数 user_id")

    menus = _service.list_menus(user_id=user_id)
    payload = {
        "code": 0,
        "message": "成功",
        "data": menus,
    }
    return jsonify(payload), 200


@shell_bp.get("/menus/<menu_code>/open-object")
def get_open_object(menu_code: str):
    """
    获取菜单对应的可打开对象信息。

    参数：
        menu_code: 菜单编码。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        GET /api/v1/menus/M002/open-object?user_id=U001
    """
    user_id = request.args.get("user_id", "")
    if user_id.strip() == "":
        return _bad_request("缺少参数 user_id")

    open_info = _service.get_open_object_info(user_id=user_id, menu_code=menu_code)
    payload = {
        "code": 0,
        "message": "成功",
        "data": open_info,
    }
    return jsonify(payload), 200


@shell_bp.get("/opened-modules")
def list_opened_modules():
    """
    获取用户已打开的模块列表。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        GET /api/v1/opened-modules?user_id=U001
    """
    user_id = request.args.get("user_id", "")
    if user_id.strip() == "":
        return _bad_request("缺少参数 user_id")

    modules = _service.list_opened_modules(user_id=user_id)
    payload = {
        "code": 0,
        "message": "成功",
        "data": modules,
    }
    return jsonify(payload), 200


@shell_bp.post("/opened-modules")
def open_module():
    """
    打开指定菜单对应的对象。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        POST /api/v1/opened-modules
        {"user_id": "U001", "menu_code": "M002", "multi_open": false}
    """
    body = request.get_json(silent=True) or {}
    user_id = body.get("user_id", "").strip()
    menu_code = body.get("menu_code", "").strip()
    multi_open = body.get("multi_open", False)

    if user_id == "":
        return _bad_request("缺少参数 user_id")
    if menu_code == "":
        return _bad_request("缺少参数 menu_code")

    result = _service.open_object(
        user_id=user_id,
        menu_code=menu_code,
        multi_open=bool(multi_open),
    )
    if result is None:
        payload = {
            "code": 404,
            "message": "菜单不可打开或不存在",
            "data": {"request_id": getattr(g, "request_id", "")},
        }
        return jsonify(payload), 404

    payload = {
        "code": 0,
        "message": "成功",
        "data": result,
    }
    return jsonify(payload), 200


@shell_bp.delete("/opened-modules/<object_name>")
def close_module(object_name: str):
    """
    关闭指定对象。

    参数：
        object_name: 对象名称。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        DELETE /api/v1/opened-modules/w_r_mc_user?user_id=U001
    """
    user_id = request.args.get("user_id", "")
    if user_id.strip() == "":
        return _bad_request("缺少参数 user_id")

    success = _service.close_object(user_id=user_id, object_name=object_name)
    payload = {
        "code": 0 if success else 404,
        "message": "成功" if success else "对象未找到",
        "data": {"closed": success},
    }
    return jsonify(payload), 200 if success else 404


@shell_bp.delete("/opened-modules/active")
def close_active_module():
    """
    关闭当前活动对象（最后打开的模块）。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        DELETE /api/v1/opened-modules/active?user_id=U001
    """
    user_id = request.args.get("user_id", "")
    if user_id.strip() == "":
        return _bad_request("缺少参数 user_id")

    result = _service.close_active_object(user_id=user_id)
    if result is None:
        payload = {
            "code": 404,
            "message": "没有活动对象可关闭",
            "data": {"request_id": getattr(g, "request_id", "")},
        }
        return jsonify(payload), 404

    payload = {
        "code": 0,
        "message": "成功",
        "data": result,
    }
    return jsonify(payload), 200
