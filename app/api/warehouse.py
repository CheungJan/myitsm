"""
仓储管理 API。

路由前缀：/api/v1/warehouse
统一入库/出库模型（优化5），通过 invtyp 区分16种出入库类型。
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
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
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


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
    details = [StockInDetailCreate.model_validate(d).model_dump() for d in raw_details]
    user_cd: str = g.current_user
    data = StockInService.create(body.model_dump(exclude_none=True), details, user_cd)
    return success_response(data=data, message="创建成功", code=201)


@warehouse_bp.post("/stock-in/<inbillid>/audit")
@login_required
def audit_stock_in(inbillid: str):  # type: ignore[no-untyped-def]
    """审核入库单（审核后更新库存）。支持传入 whcd 覆盖入库仓库。"""
    json_data = request.get_json(silent=True) or {}
    whcd: str = json_data.get("whcd", "")
    checkmemo: str = json_data.get("checkmemo", "")
    user_cd: str = g.current_user
    result = StockInService.audit(inbillid, user_cd, whcd=whcd, checkmemo=checkmemo)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


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
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


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
    details_eid = [StockOutDetailCreate.model_validate(d).model_dump() for d in raw_eid]
    details_prd = [StockOutDetailCreate.model_validate(d).model_dump() for d in raw_prd]
    user_cd: str = g.current_user
    data = StockOutService.create(
        body.model_dump(exclude_none=True), details_eid, details_prd, user_cd
    )
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
    details = [OverLostDetailCreate.model_validate(d).model_dump() for d in raw_details]
    eid_details = [OverLostEidDetailCreate.model_validate(d).model_dump() for d in raw_eid_details]
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
