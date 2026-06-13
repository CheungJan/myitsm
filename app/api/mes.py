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
    user_cd: str = g.current_user
    data = WorkOrderService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@mes_bp.delete("/work-orders/<wo_id>")
@login_required
def delete_work_order(wo_id: str):  # type: ignore[no-untyped-def]
    """删除工单（仅草稿状态）。"""
    result = WorkOrderService.delete(wo_id)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(message="已删除")


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


@mes_bp.post("/work-orders/<wo_id>/transition")
@login_required
def transition_work_order(wo_id: str):  # type: ignore[no-untyped-def]
    """工单状态流转（DRAFT→RELEASED→PICKING→IN_PROGRESS→QC_PENDING）。

    请求体: {"target": "RELEASED"}
    """
    body = request.get_json(force=True) or {}
    target = body.get("target", "")
    if not target:
        return error_response(message="请传入 target 状态", code=400)
    user_cd: str = g.current_user
    result = WorkOrderService.transition(wo_id, target, user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "流转失败")), code=400)
    return success_response(data=result, message=f"已流转至 {target}")


@mes_bp.post("/work-orders/<wo_id>/replace")
@login_required
def replace_work_order_asset(wo_id: str):  # type: ignore[no-untyped-def]
    """工单物料更换：记录旧物料→新物料 EID 或批次号映射。"""
    body = request.get_json(force=True) or {}
    old_eid = body.get("old_eid", "")
    new_eid = body.get("new_eid", "")
    itemcd = body.get("itemcd", "")
    memo = body.get("memo", "")
    old_batch_no = body.get("old_batch_no", "")
    new_batch_no = body.get("new_batch_no", "")
    
    if not itemcd:
        return error_response(message="请提供物料编码", code=400)
    if not old_eid and not old_batch_no:
        return error_response(message="请提供旧物料EID或批次号", code=400)
    if not new_eid and not new_batch_no:
        return error_response(message="请提供新物料EID或批次号", code=400)
    
    user_cd: str = g.current_user
    result = WorkOrderService.replace_asset(wo_id, old_eid, new_eid, itemcd, memo, user_cd, old_batch_no, new_batch_no)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "更换失败")), code=400)
    return success_response(message="更换记录已保存")


@mes_bp.get("/work-orders/<wo_id>/replace-records")
@login_required
def get_replace_records(wo_id: str):  # type: ignore[no-untyped-def]
    """查询工单的物料更换历史记录。"""
    from app.models.mes import ReplaceRecord
    from app.models.master import SysUser
    from sqlalchemy import func
    
    records = db.session.query(
        ReplaceRecord.wo_id,
        ReplaceRecord.old_eid,
        ReplaceRecord.new_eid,
        ReplaceRecord.itemcd,
        ReplaceRecord.old_batch_no,
        ReplaceRecord.new_batch_no,
        ReplaceRecord.memo,
        ReplaceRecord.replace_date,
        ReplaceRecord.opercd,
        func.coalesce(SysUser.user_nm, ReplaceRecord.opercd).label("operator_name")
    ).join(
        SysUser, SysUser.user_cd == ReplaceRecord.opercd, isouter=True
    ).filter(
        ReplaceRecord.wo_id == wo_id
    ).order_by(
        ReplaceRecord.replace_date.desc()
    ).all()
    
    data = [
        {
            "wo_id": r.wo_id,
            "old_eid": r.old_eid,
            "new_eid": r.new_eid,
            "itemcd": r.itemcd,
            "old_batch_no": r.old_batch_no,
            "new_batch_no": r.new_batch_no,
            "memo": r.memo,
            "replace_date": r.replace_date.isoformat() if r.replace_date else None,
            "operator_cd": r.opercd,
            "operator_name": r.operator_name or r.opercd
        }
        for r in records
    ]
    
    return success_response(data=data)


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
    user_cd: str = g.current_user
    data = ProcessDefService.create(body.model_dump(exclude_none=True), user_cd)
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


@mes_bp.get("/work-processes")
@login_required
def list_all_work_processes():  # type: ignore[no-untyped-def]
    """工单工序列表（全部）。"""
    page: int = request.args.get("page", 1, type=int)
    per_page: int = request.args.get("per_page", 20, type=int)
    data = WorkProcessService.list_all(page=page, per_page=per_page)
    return success_response(data=data)


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
    user_cd: str = g.current_user
    data = WorkProcessService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@mes_bp.delete("/work-processes/<int:wp_id>")
@login_required
def delete_work_process(wp_id: int):  # type: ignore[no-untyped-def]
    """删除工单工序（仅 PENDING 状态）。"""
    result = WorkProcessService.delete(wp_id)
    if not result.get("success"): return error_response(message=str(result.get("error", "")), code=400)
    return success_response(message="已删除")


@mes_bp.put("/work-processes/<int:wp_id>")
@login_required
def update_work_process(wp_id: int):  # type: ignore[no-untyped-def]
    """更新工单工序。"""
    body = WorkProcessUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = WorkProcessService.update(wp_id, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="工序不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 物料消耗 ----


@mes_bp.get("/materials")
@login_required
def list_all_materials():  # type: ignore[no-untyped-def]
    """物料消耗列表（全部）。"""
    page: int = request.args.get("page", 1, type=int)
    per_page: int = request.args.get("per_page", 20, type=int)
    data = MaterialConsumeService.list_all(page=page, per_page=per_page)
    return success_response(data=data)


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
    user_cd: str = g.current_user
    data = MaterialConsumeService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)
