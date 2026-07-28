"""
仓储管理 API。

路由前缀：/api/v1/warehouse
统一入库/出库模型（优化5），通过 invtyp 区分16种出入库类型。
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.extensions import db
from app.schemas.warehouse import (
    OverLostCreate,
    OverLostDetailCreate,
    OverLostEidDetailCreate,
    StockInCreate,
    StockInDetailCreate,
    StockOutCreate,
    StockOutDetailCreate,
    StockQuery,
    WarehouseCreate,
    WarehouseQuery,
    WarehouseUpdate,
)
from app.services.warehouse_service import (
    AssetCheckService,
    OverLostService,
    PosChangeService,
    StockBalanceService,
    StockInService,
    StockOutService,
    WarehouseService,
)
from app.utils.response import error_response, success_response

__all__ = ["warehouse_bp"]

warehouse_bp = Blueprint("warehouse", __name__)


# ---- 仓库主数据 ----


@warehouse_bp.get("/warehouses")
@login_required
def list_warehouses():  # type: ignore[no-untyped-def]
    """仓库列表。"""
    useflg = request.args.get("useflg", default=None)
    data = WarehouseService.list_all(useflg=useflg)
    return success_response(data=data)


@warehouse_bp.get("/warehouses/<whcd>")
@login_required
def get_warehouse(whcd: str):  # type: ignore[no-untyped-def]
    """仓库详情。"""
    data = WarehouseService.get(whcd)
    if data is None:
        return error_response(message="仓库不存在", code=404)
    return success_response(data=data)


@warehouse_bp.post("/warehouses")
@login_required
def create_warehouse():  # type: ignore[no-untyped-def]
    """创建仓库。"""
    body = WarehouseCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    data = WarehouseService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@warehouse_bp.put("/warehouses/<whcd>")
@login_required
def update_warehouse(whcd: str):  # type: ignore[no-untyped-def]
    """更新仓库。"""
    body = WarehouseUpdate.model_validate(request.get_json(silent=True) or {})
    data = WarehouseService.update(whcd, body.model_dump(exclude_unset=True))
    if data is None:
        return error_response(message="仓库不存在", code=404)
    return success_response(data=data)


# ---- 入库单 ----


@warehouse_bp.get("/stock-in")
@login_required
def list_stock_in():  # type: ignore[no-untyped-def]
    """入库单列表。"""
    params = WarehouseQuery.model_validate(request.args.to_dict())
    data = StockInService.list_records(
        whcd=params.whcd,
        invtyp=params.invtyp,
        auditflg=params.auditflg,
        inbillid=params.inbillid,
        indate_from=params.indate_from,
        indate_to=params.indate_to,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@warehouse_bp.get("/stock-in/transferable-orders")
@login_required
def list_transferable_orders():  # type: ignore[no-untyped-def]
    """可调拨入库的调拨出库单列表（已审核且有未入库数量）。"""
    return success_response(data=StockInService.list_transferable_orders())

@warehouse_bp.get("/stock-in/receivable-orders")
@login_required
def list_receivable_orders():  # type: ignore[no-untyped-def]
    """可入库的采购订单列表（已审核且仍有未入库数量）。"""
    return success_response(data=StockInService.list_receivable_orders())


@warehouse_bp.get("/stock-in/service-returnable")
@login_required
def list_service_returnable():  # type: ignore[no-untyped-def]
    """ITSM 工单中可返还的自有资产旧配件（asset_owner != 客户资产）。"""
    return success_response(data=StockInService.list_service_returnable())


@warehouse_bp.get("/stock-in/service-skip-info/<maintenance_id>")
@login_required
def get_service_skip_info(maintenance_id: str):  # type: ignore[no-untyped-def]
    """查询某ITSM工单的不入库明细。"""
    from app.models.itsm import AccessoriesUpdate
    rows = (
        db.session.query(AccessoriesUpdate)
        .filter(
            AccessoriesUpdate.maintenance_id == maintenance_id,
            AccessoriesUpdate.in_wh == "2",
        )
        .all()
    )
    return success_response(data=[
        {"eid": r.old_accessories_id, "reason": (r.description or "").replace("[不入库: ", "").rstrip("]")}
        for r in rows
    ])


@warehouse_bp.post("/stock-in/service-return-confirm")
@login_required
def confirm_service_return():  # type: ignore[no-untyped-def]
    """确认ITSM配件变更并生成服务返还入库草稿。"""
    json_data = request.get_json(silent=True) or {}
    maintenance_ids: list[str] = json_data.get("maintenance_ids", [])
    if not maintenance_ids:
        return error_response(message="请选择要确认的ITSM工单", code=400)
    user_cd: str = g.current_user
    result = StockInService.confirm_service_return(maintenance_ids, user_cd)
    return success_response(data=result, message=f"已确认 {result['created']} 个工单")


@warehouse_bp.post("/stock-in/service-return-skip")
@login_required
def skip_service_return():  # type: ignore[no-untyped-def]
    """按EID标记ITSM配件变更为不入库（耗材、实物不符等）。"""
    json_data = request.get_json(silent=True) or {}
    maintenance_id: str = json_data.get("maintenance_id", "")
    eids: list[str] = json_data.get("eids", [])
    reason: str = json_data.get("reason", "")
    if not maintenance_id or not reason:
        return error_response(message="缺少工单号或不入库原因", code=400)
    result = StockInService.skip_service_return(maintenance_id, reason, eids if eids else None)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result, message="已标记不入库")


@warehouse_bp.get("/stock-in/receivable-order-lines/<rgstbillid>")
@login_required
def get_receivable_order_lines(rgstbillid: str):  # type: ignore[no-untyped-def]
    """某采购订单的可入库明细行。"""
    return success_response(data=StockInService.get_receivable_order_lines(rgstbillid))


@warehouse_bp.get("/stock-in/<inbillid>")
@login_required
def get_stock_in(inbillid: str):  # type: ignore[no-untyped-def]
    """入库单详情。"""
    data = StockInService.get(inbillid)
    if data is None:
        return error_response(message="入库单不存在", code=404)
    return success_response(data=data)


@warehouse_bp.post("/stock-in")
@login_required
def create_stock_in():  # type: ignore[no-untyped-def]
    """创建入库单。"""
    json_data = request.get_json(silent=True) or {}
    body = StockInCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    details = [StockInDetailCreate.model_validate(d).model_dump(exclude_none=True) for d in raw_details]
    body_dict = body.model_dump(exclude_none=True)
    custom_auditflg = body_dict.pop("auditflg", None)
    user_cd: str = g.current_user
    data = StockInService.create(body_dict, details, user_cd)
    if not data.get("success", True):
        return error_response(message=str(data.get("error", "创建失败")), code=400)
    # 如果传了自定义 auditflg（如全部不入库标记 S），覆盖
    if custom_auditflg:
        from app.models.warehouse import StockIn as StockInModel
        record = db.session.get(StockInModel, data.get("inbillid"))
        if record:
            record.auditflg = custom_auditflg
            db.session.commit()
    return success_response(data=data, message="创建成功", code=201)


@warehouse_bp.post("/stock-in/<inbillid>/audit")
@login_required
def audit_stock_in(inbillid: str):  # type: ignore[no-untyped-def]
    """审核入库单。auditflg: 2=审核通过, 8=审核退回"""
    json_data = request.get_json(silent=True) or {}
    whcd: str = json_data.get("whcd", "")
    checkmemo: str = json_data.get("checkmemo", "")
    auditflg: str = json_data.get("auditflg", "2")
    user_cd: str = g.current_user
    result = StockInService.audit(inbillid, user_cd, whcd=whcd, checkmemo=checkmemo, auditflg=auditflg)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


@warehouse_bp.post("/stock-in/<inbillid>/unaudit")
@login_required
def unaudit_stock_in(inbillid: str):  # type: ignore[no-untyped-def]
    """反审核入库单：回退库存、作废下游 OV 草稿、重置为草稿状态。"""
    user_cd: str = g.current_user
    result = StockInService.unaudit(inbillid, user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


@warehouse_bp.put("/stock-in/<inbillid>")
@login_required
def update_stock_in(inbillid: str):  # type: ignore[no-untyped-def]
    """编辑入库单（仅未审核/已退回可编辑）。"""
    json_data = request.get_json(silent=True) or {}
    raw_details = json_data.get("details", [])
    details = [StockInDetailCreate.model_validate(d).model_dump(exclude_none=True) for d in raw_details]
    whcd: str = json_data.get("whcd", "")
    memo: str = json_data.get("memo", "")
    indate: str = json_data.get("indate", "")
    user_cd: str = g.current_user
    result = StockInService.update(inbillid, user_cd, whcd=whcd, memo=memo, indate=indate, details=details)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result, message="更新成功")


@warehouse_bp.post("/stock-in/<inbillid>/void")
@login_required
def void_stock_in(inbillid: str):  # type: ignore[no-untyped-def]
    """作废入库单（仅未审核/已退回可作废）。"""
    user_cd: str = g.current_user
    result = StockInService.void(inbillid, user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result, message="已作废")


# ---- 出库单 ----


@warehouse_bp.get("/stock-out")
@login_required
def list_stock_out():  # type: ignore[no-untyped-def]
    """出库单列表。"""
    params = WarehouseQuery.model_validate(request.args.to_dict())
    data = StockOutService.list_records(
        whcd=params.whcd,
        invtyp=params.invtyp,
        auditflg=params.auditflg,
        outbillid=params.outbillid,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@warehouse_bp.get("/stock-out/returnable-orders")
@login_required
def list_returnable_orders():  # type: ignore[no-untyped-def]
    """可退货出库的采购退货单列表（已审核且有未退数量）。"""
    return success_response(data=StockOutService.list_returnable_orders())


@warehouse_bp.get("/stock-out/returnable-order-lines/<pcbillid>")
@login_required
def get_returnable_order_lines(pcbillid: str):  # type: ignore[no-untyped-def]
    """某退货单的可退货出库明细行。"""
    return success_response(data=StockOutService.get_returnable_order_lines(pcbillid))


@warehouse_bp.get("/stock-out/<outbillid>")
@login_required
def get_stock_out(outbillid: str):  # type: ignore[no-untyped-def]
    """出库单详情。"""
    data = StockOutService.get(outbillid)
    if data is None:
        return error_response(message="出库单不存在", code=404)
    return success_response(data=data)


@warehouse_bp.post("/stock-out")
@login_required
def create_stock_out():  # type: ignore[no-untyped-def]
    """创建出库单。"""
    json_data = request.get_json(silent=True) or {}
    body = StockOutCreate.model_validate(json_data)
    raw_eid = json_data.get("details_eid", [])
    raw_prd = json_data.get("details_prd", [])
    details_eid = [StockOutDetailCreate.model_validate(d).model_dump(exclude_none=True) for d in raw_eid]
    details_prd = [StockOutDetailCreate.model_validate(d).model_dump(exclude_none=True) for d in raw_prd]
    user_cd: str = g.current_user
    data = StockOutService.create(
        body.model_dump(exclude_none=True), details_eid, details_prd, user_cd
    )
    if not data.get("success", True):
        return error_response(message=str(data.get("error", "创建失败")), code=400)
    return success_response(data=data, message="创建成功", code=201)


@warehouse_bp.post("/stock-out/<outbillid>/audit")
@login_required
def audit_stock_out(outbillid: str):  # type: ignore[no-untyped-def]
    """审核出库单。审核通过扣库存，退回不扣。"""
    json_data = request.get_json(silent=True) or {}
    auditflg = json_data.get("auditflg", "2")
    checkmemo: str = json_data.get("checkmemo", "")
    user_cd: str = g.current_user
    result = StockOutService.audit(outbillid, user_cd, auditflg, checkmemo=checkmemo)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


@warehouse_bp.put("/stock-out/<outbillid>")
@login_required
def update_stock_out(outbillid: str):  # type: ignore[no-untyped-def]
    """编辑出库单（仅未审核/已退回可编辑）。"""
    json_data = request.get_json(silent=True) or {}
    raw_eid = json_data.get("details_eid", [])
    raw_prd = json_data.get("details_prd", [])
    details_eid = [StockOutDetailCreate.model_validate(d).model_dump(exclude_none=True) for d in raw_eid]
    details_prd = [StockOutDetailCreate.model_validate(d).model_dump(exclude_none=True) for d in raw_prd]
    whcd: str = json_data.get("whcd", "")
    memo: str = json_data.get("memo", "")
    outdate: str = json_data.get("outdate", "")
    user_cd: str = g.current_user
    result = StockOutService.update(outbillid, user_cd, whcd=whcd, memo=memo, outdate=outdate,
                                     details_eid=details_eid, details_prd=details_prd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result, message="更新成功")


@warehouse_bp.post("/stock-out/<outbillid>/unaudit")
@login_required
def unaudit_stock_out(outbillid: str):  # type: ignore[no-untyped-def]
    """反审核出库单：回退库存、清理TMS04、重置为草稿。"""
    user_cd: str = g.current_user
    result = StockOutService.unaudit(outbillid, user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


@warehouse_bp.post("/stock-out/<outbillid>/void")
@login_required
def void_stock_out(outbillid: str):  # type: ignore[no-untyped-def]
    """作废出库单（仅未审核/已退回可作废）。"""
    user_cd: str = g.current_user
    result = StockOutService.void(outbillid, user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result, message="已作废")


@warehouse_bp.post("/stock-out/<outbillid>/close-lines")
@login_required
def close_stock_out_lines(outbillid: str):  # type: ignore[no-untyped-def]
    """出库单行级结案（标记指定明细行不再等待入库）。"""
    json_data = request.get_json(silent=True) or {}
    lines = json_data.get("lines", [])
    reason = json_data.get("reason", "")
    if not lines:
        return error_response(message="请选择要结案的明细行", code=400)
    if not reason:
        return error_response(message="请填写结案原因", code=400)
    user_cd: str = g.current_user
    result = StockOutService.close_lines(outbillid, lines, reason, user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result, message="结案成功")


# ---- 单据选择器 (Phase B) ----

@warehouse_bp.get("/stock-in/lendable-orders")
@login_required
def list_lendable_orders():  # type: ignore[no-untyped-def]
    """可归还的借出出库单列表（已审核且未完全归还）。"""
    from app.repositories.warehouse_repository import StockInRepository
    rows = StockInRepository.find_lendable_orders()
    return success_response(data=rows)


@warehouse_bp.get("/stock-in/lendable-order-lines/<outbillid>")
@login_required
def get_lendable_order_lines(outbillid: str):  # type: ignore[no-untyped-def]
    """某借出出库单中尚未归还的明细行。"""
    return success_response(data=StockInService.get_lendable_order_lines(outbillid))


@warehouse_bp.get("/stock-in/qc-returnable")
@login_required
def list_qc_returnable():  # type: ignore[no-untyped-def]
    """可质检入库的质检出库单列表（OV=5 已审核且未完全入库，供 IV=11 选单）。"""
    return success_response(data=StockInService.list_qc_returnable())


@warehouse_bp.get("/stock-in/qc-returnable-lines/<outbillid>")
@login_required
def get_qc_returnable_lines(outbillid: str):  # type: ignore[no-untyped-def]
    """某质检出库单中尚未入库的明细行（供 IV=11 选择）。"""
    return success_response(data=StockInService.get_qc_returnable_lines(outbillid))


@warehouse_bp.get("/stock-out/qc-pending")
@login_required
def list_qc_pending():  # type: ignore[no-untyped-def]
    """已审核采购入库单列表（供质检出库 OV=5 选单）。"""
    return success_response(data=StockInService.list_qc_out_pending())

@warehouse_bp.get("/stock-out/ov5-qc-pending")
@login_required
def list_ov5_for_qc():  # type: ignore[no-untyped-def]
    """未完全QC的 OV=5 质检出库单列表（供质检录入选单）。"""
    return success_response(data=StockInService.list_ov5_for_qc())


@warehouse_bp.get("/stock-out/qc-pending-lines/<inbillid>")
@login_required
def get_qc_pending_lines(inbillid: str):  # type: ignore[no-untyped-def]
    """某采购入库单的物料明细（供 OV=5 质检出库选择）。"""
    return success_response(data=StockInService.get_qc_pending_lines(inbillid))


@warehouse_bp.get("/stock-in/sales-returnable")
@login_required
def list_sales_returnable():  # type: ignore[no-untyped-def]
    """可销售退货入库的销售出库单列表（OV=1 已审核且未完全退货，供 IV=2 选单）。"""
    return success_response(data=StockInService.list_sales_returnable())


@warehouse_bp.get("/stock-in/sales-returnable-lines/<outbillid>")
@login_required
def get_sales_returnable_lines(outbillid: str):  # type: ignore[no-untyped-def]
    """某销售出库单中尚未退货的明细行（供 IV=2 选择）。"""
    return success_response(data=StockInService.get_sales_returnable_lines(outbillid))


@warehouse_bp.get("/stock-in/renovation-returnable")
@login_required
def list_renovation_returnable():  # type: ignore[no-untyped-def]
    """可翻新入库的翻新出库单列表（OV=10 已审核且未完全入库，供 IV=6 选单）。"""
    return success_response(data=StockInService.list_renovation_returnable())


@warehouse_bp.get("/stock-in/renovation-returnable-lines/<outbillid>")
@login_required
def get_renovation_returnable_lines(outbillid: str):  # type: ignore[no-untyped-def]
    """某翻新出库单中尚未入库的明细行（供 IV=6 选择）。"""
    return success_response(data=StockInService.get_renovation_returnable_lines(outbillid))


@warehouse_bp.get("/stock-in/repair-returnable")
@login_required
def list_repair_returnable():  # type: ignore[no-untyped-def]
    """可返修入库的返修出库单列表（已审核且未完全入库）。"""
    rows = StockInService.list_repair_returnable()
    return success_response(data=rows)


@warehouse_bp.get("/stock-in/production-returnable")
@login_required
def list_production_returnable():  # type: ignore[no-untyped-def]
    """可生产入库的生产出库单列表（已审核且未完全入库）。"""
    return success_response(data=StockInService.list_production_returnable())


@warehouse_bp.get("/stock-in/production-returnable-lines/<outbillid>")
@login_required
def get_production_returnable_lines(outbillid: str):  # type: ignore[no-untyped-def]
    """某生产出库单中尚未入库的明细行。"""
    return success_response(data=StockInService.get_production_returnable_lines(outbillid))


@warehouse_bp.get("/stock-in/repair-returnable-lines/<outbillid>")
@login_required
def get_repair_returnable_lines(outbillid: str):  # type: ignore[no-untyped-def]
    """某返修出库单中尚未入库的明细行。"""
    return success_response(data=StockInService.get_repair_returnable_lines(outbillid))


# ---- 库存查询 ----


@warehouse_bp.get("/stock")
@login_required
def list_stock():  # type: ignore[no-untyped-def]
    """库存明细列表。"""
    params = StockQuery.model_validate(request.args.to_dict())
    if params.itemcd:
        data = StockBalanceService.get_balance(params.whcd, params.itemcd)
    else:
        data = StockBalanceService.list_stock(
            whcd=params.whcd, page=params.page, per_page=params.per_page
        )
    return success_response(data=data)


@warehouse_bp.get("/stock-movement")
@login_required
def list_stock_movements():  # type: ignore[no-untyped-def]
    """库存流水查询。"""
    whcd = request.args.get("whcd")
    itemcd = request.args.get("itemcd")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    billid = request.args.get("billid")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    data = StockBalanceService.list_movements(
        whcd=whcd, itemcd=itemcd, start_date=start_date,
        end_date=end_date, billid=billid, page=page, per_page=per_page,
    )
    return success_response(data=data)


# ---- 仓库报表 ----


@warehouse_bp.get("/reports/inventory-summary")
@login_required
def inventory_summary():  # type: ignore[no-untyped-def]
    """收发存汇总：期初+入库-出库=期末，按月×仓库×物料。"""
    whcd = request.args.get("whcd", "")
    period = request.args.get("period", "")  # YYYY-MM, 默认当月
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    data = StockBalanceService.inventory_summary(whcd=whcd or None, period=period, page=page, per_page=per_page)
    return success_response(data=data)


@warehouse_bp.get("/reports/daily-snapshot")
@login_required
def daily_snapshot():  # type: ignore[no-untyped-def]
    """库存日报：指定日期的库存快照。"""
    whcd = request.args.get("whcd", "")
    date_str = request.args.get("date", "")  # YYYY-MM-DD, 默认今天
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    data = StockBalanceService.daily_snapshot(whcd=whcd or None, date_str=date_str, page=page, per_page=per_page)
    return success_response(data=data)


@warehouse_bp.get("/reports/aging")
@login_required
def inventory_aging():  # type: ignore[no-untyped-def]
    """库龄分析：物料在库时间分布。"""
    whcd = request.args.get("whcd", "")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    data = StockBalanceService.inventory_aging(whcd=whcd or None, page=page, per_page=per_page)
    return success_response(data=data)


# ---- 资产盘点 ----


@warehouse_bp.get("/asset-check")
@login_required
def list_asset_checks():  # type: ignore[no-untyped-def]
    """资产盘点列表。"""
    page: int = request.args.get("page", 1, type=int)
    per_page: int = request.args.get("per_page", 20, type=int)
    data = AssetCheckService.list_records(
        page=page, per_page=per_page
    )
    return success_response(data=data)


@warehouse_bp.get("/asset-check/<opbillid>")
@login_required
def get_asset_check(opbillid: str):  # type: ignore[no-untyped-def]
    """资产盘点详情。"""
    record = AssetCheckService.get(opbillid)
    if record is None:
        return error_response("盘点单不存在", code=404)
    return success_response(data=record)


@warehouse_bp.post("/asset-check")
@login_required
def create_asset_check():  # type: ignore[no-untyped-def]
    """创建资产盘点单。"""
    body = request.get_json(silent=True) or {}
    creator: str = g.current_user
    record = AssetCheckService.create(body, creator)
    return success_response(data=record, code=201)


@warehouse_bp.put("/asset-check/<opbillid>")
@login_required
def update_asset_check(opbillid: str):  # type: ignore[no-untyped-def]
    """更新资产盘点单。"""
    body = request.get_json(silent=True) or {}
    record = AssetCheckService.update(opbillid, body)
    if record is None:
        return error_response("盘点单不存在", code=404)
    return success_response(data=record)


@warehouse_bp.post("/asset-check/<opbillid>/audit")
@login_required
def audit_asset_check(opbillid: str):  # type: ignore[no-untyped-def]
    """审核资产盘点单。"""
    auditor: str = g.current_user
    record = AssetCheckService.audit(opbillid, auditor)
    if record is None:
        return error_response("盘点单不存在", code=404)
    return success_response(data=record)


# ---- POS设备变更 ----


@warehouse_bp.get("/pos-change")
@login_required
def list_pos_changes():  # type: ignore[no-untyped-def]
    """POS设备变更列表。"""
    page: int = request.args.get("page", 1, type=int)
    per_page: int = request.args.get("per_page", 20, type=int)
    data = PosChangeService.list_records(
        page=page, per_page=per_page
    )
    return success_response(data=data)


@warehouse_bp.get("/pos-change/<int:pk>")
@login_required
def get_pos_change(pk: int):  # type: ignore[no-untyped-def]
    """POS设备变更详情。"""
    record = PosChangeService.get(pk)
    if record is None:
        return error_response("变更记录不存在", code=404)
    return success_response(data=record)


@warehouse_bp.post("/pos-change")
@login_required
def create_pos_change():  # type: ignore[no-untyped-def]
    """创建POS设备变更。"""
    body = request.get_json(silent=True) or {}
    creator: str = g.current_user
    record = PosChangeService.create(body, creator)
    return success_response(data=record, code=201)


@warehouse_bp.put("/pos-change/<int:pk>")
@login_required
def update_pos_change(pk: int):  # type: ignore[no-untyped-def]
    """更新POS设备变更。"""
    body = request.get_json(silent=True) or {}
    record = PosChangeService.update(pk, body)
    if record is None:
        return error_response("变更记录不存在", code=404)
    return success_response(data=record)


# ---- 盘盈盘亏 (TWH17_OVERLOST) ----


@warehouse_bp.get("/overlost")
@login_required
def list_overlost():  # type: ignore[no-untyped-def]
    """盘盈盘亏列表。"""
    whcd = request.args.get("whcd")
    oltyp = request.args.get("oltyp")
    auditflg = request.args.get("auditflg")
    page: int = request.args.get("page", 1, type=int)
    per_page: int = request.args.get("per_page", 20, type=int)
    data = OverLostService.list_records(
        whcd=whcd, oltyp=oltyp, auditflg=auditflg, page=page, per_page=per_page
    )
    return success_response(data=data)


@warehouse_bp.get("/overlost/<olbillid>")
@login_required
def get_overlost(olbillid: str):  # type: ignore[no-untyped-def]
    """盘盈盘亏详情。"""
    data = OverLostService.get(olbillid)
    if data is None:
        return error_response(message="盘点单不存在", code=404)
    return success_response(data=data)


@warehouse_bp.post("/overlost")
@login_required
def create_overlost():  # type: ignore[no-untyped-def]
    """创建盘盈盘亏单。"""
    json_data = request.get_json(silent=True) or {}
    body = OverLostCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    raw_eid_details = json_data.get("eid_details", [])
    details = [OverLostDetailCreate.model_validate(d).model_dump(exclude_none=True) for d in raw_details]
    eid_details = [OverLostEidDetailCreate.model_validate(d).model_dump(exclude_none=True) for d in raw_eid_details]
    user_cd: str = g.current_user
    data = OverLostService.create(body.model_dump(exclude_none=True), details, eid_details, user_cd)
    return success_response(data=data, message="创建成功", code=201)


@warehouse_bp.post("/overlost/<olbillid>/audit")
@login_required
def audit_overlost(olbillid: str):  # type: ignore[no-untyped-def]
    """审核盘盈盘亏单。"""
    user_cd: str = g.current_user
    result = OverLostService.audit(olbillid, user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)
