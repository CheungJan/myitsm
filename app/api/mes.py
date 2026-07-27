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


@mes_bp.get("/work-orders/<wo_id>/lifecycle")
@login_required
def get_work_order_lifecycle(wo_id: str):  # type: ignore[no-untyped-def]
    """工单全生命周期聚合：一次性返回工单头、BOM、物料消耗、更换历史、质检概要、出入库单据流水。

    供工单详情页按「下达→领料→生产→质检→补料→入库」时间轴展现。
    """
    data = WorkOrderService.get_lifecycle(wo_id)
    if data is None:
        return error_response(message="工单不存在", code=404)
    return success_response(data=data)


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
    from app.extensions import db
    from app.models.mes import ReplaceRecord
    from app.models.system import User as SysUser
    from sqlalchemy import func

    records = db.session.query(
        ReplaceRecord.id,
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
        ReplaceRecord.replace_date.desc().nullslast(),
        ReplaceRecord.id.desc()
    ).all()

    data = [
        {
            "id": r.id,
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


@mes_bp.get("/work-orders/<wo_id>/replenish-available")
@login_required
def get_available_replenish(wo_id: str):  # type: ignore[no-untyped-def]
    """查询工单 FQC 不良品关联的、且已审核的补料明细（用于物料更换自动填充）。

    业务逻辑：
    1. FQC 录入时，每个不良品(BF/BH/TH)会关联一个补料出库单(replenish_ov_billid)。
    2. 物料更换自动填充时，只能使用这些关联补料单中【已审核】的单据明细。
    3. 若关联补料单全部未审核，返回空明细并提示未审核单号，避免误填其他批次补料。
    """
    from app.extensions import db
    from app.models.warehouse import (
        QcResult,
        QcResultDt,
        QcResultEid,
        StockOut,
        StockOutDetailEid,
        StockOutDetailPrd,
    )

    # 1. 找该工单的 FQC 质检单（optyp='FQ'，未审核/已退回草稿）
    fqc_bills = (
        db.session.query(QcResult.qcbillid)
        .filter(
            QcResult.refbillid == wo_id,
            QcResult.optyp == "FQ",
        )
        .all()
    )
    fqc_ids = [b.qcbillid for b in fqc_bills]
    if not fqc_ids:
        return success_response(data={"items": [], "audited_billids": [], "pending_billids": []})

    # 2. 收集 FQC 不良品(BF/BH/TH)关联的补料出库单号
    defect_status = ("BF", "BH", "TH")
    eid_ov = (
        db.session.query(QcResultEid.replenish_ov_billid)
        .filter(
            QcResultEid.qcbillid.in_(fqc_ids),
            QcResultEid.qcstatus.in_(defect_status),
            QcResultEid.replenish_ov_billid.isnot(None),
            QcResultEid.replenish_ov_billid != "",
        )
        .all()
    )
    prd_ov = (
        db.session.query(QcResultDt.replenish_ov_billid)
        .filter(
            QcResultDt.qcbillid.in_(fqc_ids),
            QcResultDt.qcstatus.in_(defect_status),
            QcResultDt.replenish_ov_billid.isnot(None),
            QcResultDt.replenish_ov_billid != "",
        )
        .all()
    )
    related_ovs = {r.replenish_ov_billid for r in eid_ov} | {r.replenish_ov_billid for r in prd_ov}
    if not related_ovs:
        return success_response(data={"items": [], "audited_billids": [], "pending_billids": []})

    # 3. 区分关联补料单的审核状态（auditflg='2' 为已审核）
    ov_rows = (
        db.session.query(StockOut.outbillid, StockOut.auditflg)
        .filter(StockOut.outbillid.in_(list(related_ovs)))
        .all()
    )
    audited = [r.outbillid for r in ov_rows if r.auditflg == "2"]
    pending = [r.outbillid for r in ov_rows if r.auditflg != "2"]

    if not audited:
        # 关联补料单全部未审核：返回空明细 + 未审核单号供前端提示
        return success_response(data={"items": [], "audited_billids": [], "pending_billids": pending})

    # 4. 取已审核补料单的明细（EID + 批次）
    available_items: list[dict[str, object]] = []

    eid_details = (
        db.session.query(
            StockOutDetailEid.outbillid,
            StockOutDetailEid.itemcd,
            StockOutDetailEid.eid,
            StockOutDetailEid.prddate,
            StockOutDetailEid.itemtyp,
            StockOutDetailEid.outqty,
        )
        .filter(StockOutDetailEid.outbillid.in_(audited))
        .all()
    )
    for d in eid_details:
        eid_val = d.eid.strip() if d.eid else ""
        for _ in range(d.outqty or 1):
            available_items.append({
                "outbillid": d.outbillid,
                "itemcd": d.itemcd,
                "eid": eid_val or None,
                "prddate": d.prddate.isoformat() if d.prddate else None,
                "itemtyp": d.itemtyp,
                "typ": "eid",
            })

    prd_details = (
        db.session.query(
            StockOutDetailPrd.outbillid,
            StockOutDetailPrd.itemcd,
            StockOutDetailPrd.prddate,
            StockOutDetailPrd.itemtyp,
            StockOutDetailPrd.outqty,
        )
        .filter(StockOutDetailPrd.outbillid.in_(audited))
        .all()
    )
    for d in prd_details:
        for _ in range(d.outqty or 1):
            available_items.append({
                "outbillid": d.outbillid,
                "itemcd": d.itemcd,
                "eid": None,
                "prddate": d.prddate.isoformat() if d.prddate else None,
                "itemtyp": d.itemtyp,
                "typ": "batch",
            })

    return success_response(data={
        "items": available_items,
        "audited_billids": audited,
        "pending_billids": pending,
    })


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
