"""
客户自助服务门户 API（Tier-2 G9）。

路由前缀：/api/v1/portal
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.portal import (
    PortalUserCreate,
    PortalUserUpdate,
    RepairRequestCreate,
    RepairRequestUpdate,
    ServiceRatingCreate,
)
from app.services.portal_service import (
    PortalUserService,
    RepairRequestService,
    ServiceRatingService,
)
from app.utils.response import error_response, success_response

__all__ = ["portal_bp"]

portal_bp = Blueprint("portal", __name__)


# ---- 门户用户 ----


@portal_bp.get("/users")
@login_required
def list_portal_users():  # type: ignore[no-untyped-def]
    """门户用户列表。"""
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = PortalUserService.list_all(page=page, per_page=per_page)
    return success_response(data=data)


@portal_bp.get("/users/<portal_uid>")
@login_required
def get_portal_user(portal_uid: str):  # type: ignore[no-untyped-def]
    """门户用户详情。"""
    data = PortalUserService.get(portal_uid)
    if data is None:
        return error_response(message="用户不存在", code=404)
    return success_response(data=data)


@portal_bp.post("/users")
@login_required
def create_portal_user():  # type: ignore[no-untyped-def]
    """创建门户用户。"""
    body = PortalUserCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = PortalUserService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@portal_bp.put("/users/<portal_uid>")
@login_required
def update_portal_user(portal_uid: str):  # type: ignore[no-untyped-def]
    """更新门户用户。"""
    body = PortalUserUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = PortalUserService.update(portal_uid, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="用户不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 自助报修 ----


@portal_bp.get("/repairs")
@login_required
def list_repairs():  # type: ignore[no-untyped-def]
    """报修工单列表。"""
    custcd = request.args.get("custcd")
    status = request.args.get("status")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = RepairRequestService.list_all(custcd=custcd, status=status, page=page, per_page=per_page)
    return success_response(data=data)


@portal_bp.get("/repairs/<request_id>")
@login_required
def get_repair(request_id: str):  # type: ignore[no-untyped-def]
    """报修工单详情。"""
    data = RepairRequestService.get(request_id)
    if data is None:
        return error_response(message="报修工单不存在", code=404)
    return success_response(data=data)


@portal_bp.post("/repairs")
@login_required
def create_repair():  # type: ignore[no-untyped-def]
    """创建报修工单。"""
    body = RepairRequestCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = RepairRequestService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@portal_bp.put("/repairs/<request_id>")
@login_required
def update_repair(request_id: str):  # type: ignore[no-untyped-def]
    """更新报修工单。"""
    body = RepairRequestUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = RepairRequestService.update(request_id, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="报修工单不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 服务评价 ----


@portal_bp.get("/ratings")
@login_required
def list_ratings():  # type: ignore[no-untyped-def]
    """服务评价列表。"""
    custcd = request.args.get("custcd")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = ServiceRatingService.list_all(custcd=custcd, page=page, per_page=per_page)
    return success_response(data=data)


@portal_bp.post("/ratings")
@login_required
def create_rating():  # type: ignore[no-untyped-def]
    """创建服务评价。"""
    body = ServiceRatingCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = ServiceRatingService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)
