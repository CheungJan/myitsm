"""
仓储管理 API。

路由前缀：/api/v1/warehouse
统一入库/出库模型（优化5），通过 invtyp 区分16种出入库类型。
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.warehouse import (
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
    data = WarehouseService.list_all()
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
    """审核入库单（审核后更新库存）。"""
    user_cd: str = g.current_user
    result = StockInService.audit(inbillid, user_cd)
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
    """审核出库单（审核后扣减库存）。"""
    user_cd: str = g.current_user
    result = StockOutService.audit(outbillid, user_cd)
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
