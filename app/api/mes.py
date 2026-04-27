"""
生产制造 MES API（Tier-3 G7）。

路由前缀：/api/v1/mes
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.mes import (
    MaterialConsumeCreate,
    ProcessDefCreate,
    ProcessDefUpdate,
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkProcessCreate,
    WorkProcessUpdate,
)
from app.services.mes_service import (
    MaterialConsumeService,
    ProcessDefService,
    WorkOrderService,
    WorkProcessService,
)
from app.utils.response import error_response, success_response

__all__ = ["mes_bp"]

mes_bp = Blueprint("mes", __name__)


# ---- 生产工单 ----


@mes_bp.get("/work-orders")
@login_required
def list_work_orders():  # type: ignore[no-untyped-def]
    """工单列表。"""
    status = request.args.get("status")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = WorkOrderService.list_all(status=status, page=page, per_page=per_page)
    return success_response(data=data)


@mes_bp.get("/work-orders/<wo_id>")
@login_required
def get_work_order(wo_id: str):  # type: ignore[no-untyped-def]
    """工单详情（含工序）。"""
    data = WorkOrderService.get(wo_id)
    if data is None:
        return error_response(message="工单不存在", code=404)
    return success_response(data=data)


@mes_bp.post("/work-orders")
@login_required
def create_work_order():  # type: ignore[no-untyped-def]
    """创建工单。"""
    body = WorkOrderCreate(**request.get_json(force=True))
    data = WorkOrderService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


@mes_bp.put("/work-orders/<wo_id>")
@login_required
def update_work_order(wo_id: str):  # type: ignore[no-untyped-def]
    """更新工单。"""
    body = WorkOrderUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = WorkOrderService.update(wo_id, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="工单不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 工序定义 ----


@mes_bp.get("/processes")
@login_required
def list_processes():  # type: ignore[no-untyped-def]
    """工序定义列表。"""
    data = ProcessDefService.list_all()
    return success_response(data=data)


@mes_bp.post("/processes")
@login_required
def create_process():  # type: ignore[no-untyped-def]
    """创建工序定义。"""
    body = ProcessDefCreate(**request.get_json(force=True))
    data = ProcessDefService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


@mes_bp.put("/processes/<process_cd>")
@login_required
def update_process(process_cd: str):  # type: ignore[no-untyped-def]
    """更新工序定义。"""
    body = ProcessDefUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = ProcessDefService.update(process_cd, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="工序不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 工单工序 ----


@mes_bp.get("/work-orders/<wo_id>/processes")
@login_required
def list_work_processes(wo_id: str):  # type: ignore[no-untyped-def]
    """工单工序列表。"""
    data = WorkProcessService.list_by_wo(wo_id)
    return success_response(data=data)


@mes_bp.post("/work-processes")
@login_required
def create_work_process():  # type: ignore[no-untyped-def]
    """创建工单工序。"""
    body = WorkProcessCreate(**request.get_json(force=True))
    data = WorkProcessService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


@mes_bp.put("/work-processes/<int:wp_id>")
@login_required
def update_work_process(wp_id: int):  # type: ignore[no-untyped-def]
    """更新工单工序。"""
    body = WorkProcessUpdate(**request.get_json(force=True))
    data = WorkProcessService.update(wp_id, body.model_dump(exclude_unset=True))
    if data is None:
        return error_response(message="工序不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 物料消耗 ----


@mes_bp.get("/work-orders/<wo_id>/materials")
@login_required
def list_materials(wo_id: str):  # type: ignore[no-untyped-def]
    """物料消耗列表。"""
    data = MaterialConsumeService.list_by_wo(wo_id)
    return success_response(data=data)


@mes_bp.post("/materials")
@login_required
def create_material():  # type: ignore[no-untyped-def]
    """创建物料消耗。"""
    body = MaterialConsumeCreate(**request.get_json(force=True))
    data = MaterialConsumeService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)
