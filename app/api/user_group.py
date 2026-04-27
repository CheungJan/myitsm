"""
用户组与权限 API。
作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08
注意事项：对应 PB app_system.pbl 权限模块，提供统一权限查询接口。
"""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from app.services.user_group_service import UserGroupService

__all__ = ["user_group_bp"]

user_group_bp = Blueprint("user_group", __name__)
_service = UserGroupService()


def _bad_request(message: str):
    """生成统一 400 响应。"""
    payload = {
        "code": 400,
        "message": message,
        "data": {"request_id": getattr(g, "request_id", "")},
    }
    return jsonify(payload), 400


@user_group_bp.get("/groups")
def list_groups():
    """
    获取用户组列表。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        GET /api/v1/groups
    """
    groups = _service.list_groups()
    payload = {
        "code": 0,
        "message": "成功",
        "data": groups,
    }
    return jsonify(payload), 200


@user_group_bp.get("/groups/<group_cd>")
def get_group_detail(group_cd: str):
    """
    获取用户组详情（含成员和权限）。

    参数：
        group_cd: 用户组编码。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        GET /api/v1/groups/ADMIN
    """
    detail = _service.get_group_detail(group_cd)
    if detail is None:
        payload = {
            "code": 404,
            "message": "用户组不存在",
            "data": {"request_id": getattr(g, "request_id", "")},
        }
        return jsonify(payload), 404

    payload = {
        "code": 0,
        "message": "成功",
        "data": detail,
    }
    return jsonify(payload), 200


@user_group_bp.get("/users/<user_id>/groups")
def get_user_groups(user_id: str):
    """
    获取用户所属的用户组。

    参数：
        user_id: 用户编码。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        GET /api/v1/users/U001/groups
    """
    groups = _service.get_user_groups(user_id)
    payload = {
        "code": 0,
        "message": "成功",
        "data": groups,
    }
    return jsonify(payload), 200


@user_group_bp.get("/users/<user_id>/menus")
def get_user_menus(user_id: str):
    """
    获取用户有权限的菜单列表。

    参数：
        user_id: 用户编码。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        GET /api/v1/users/U001/menus
    """
    menus = _service.get_user_menus_with_rights(user_id)
    payload = {
        "code": 0,
        "message": "成功",
        "data": menus,
    }
    return jsonify(payload), 200


@user_group_bp.get("/users/<user_id>/menu-tree")
def get_user_menu_tree(user_id: str):
    """
    获取用户有权限的菜单树（层级结构）。

    参数：
        user_id: 用户编码。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        GET /api/v1/users/U001/menu-tree
    """
    tree = _service.build_user_menu_tree(user_id)
    payload = {
        "code": 0,
        "message": "成功",
        "data": tree,
    }
    return jsonify(payload), 200


@user_group_bp.get("/users/<user_id>/menu-rights/<menu_code>")
def check_menu_right(user_id: str, menu_code: str):
    """
    检查用户对指定菜单的权限。

    参数：
        user_id: 用户编码。
        menu_code: 菜单编码。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        GET /api/v1/users/U001/menu-rights/M002
    """
    result = _service.check_menu_right(user_id, menu_code)
    payload = {
        "code": 0,
        "message": "成功",
        "data": result,
    }
    return jsonify(payload), 200
