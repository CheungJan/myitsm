"""
库存预警与价格管理 API。

路由前缀：/api/v1/inventory
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.inventory import (
    AdjustPriceCreate,
    InventoryLimitCreate,
    InventoryLimitUpdate,
    PriceCreate,
    PriceUpdate,
)
from app.services.inventory_service import (
    AdjustPriceService,
    InventoryLimitService,
    PriceService,
)
from app.utils.response import error_response, success_response

__all__ = ["inventory_bp"]

inventory_bp = Blueprint("inventory", __name__)


# ---- 库存预警 ----


@inventory_bp.get("/inventory-limits")
@login_required
def list_limits():  # type: ignore[no-untyped-def]
    """库存预警列表。"""
    data = InventoryLimitService.list_all()
    return success_response(data=data)


@inventory_bp.get("/inventory-limits/<itemcd>")
@login_required
def get_limit(itemcd: str):  # type: ignore[no-untyped-def]
    """库存预警详情。"""
    data = InventoryLimitService.get(itemcd)
    if data is None:
        return error_response(message="预警规则不存在", code=404)
    return success_response(data=data)


@inventory_bp.post("/inventory-limits")
@login_required
def create_limit():  # type: ignore[no-untyped-def]
    """创建库存预警。"""
    body = InventoryLimitCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = InventoryLimitService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@inventory_bp.put("/inventory-limits/<itemcd>")
@login_required
def update_limit(itemcd: str):  # type: ignore[no-untyped-def]
    """更新库存预警。"""
    body = InventoryLimitUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = InventoryLimitService.update(itemcd, body.model_dump(exclude_none=True), user_cd)
    if data is None:
        return error_response(message="预警规则不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 价格规则 ----


@inventory_bp.get("/prices")
@login_required
def list_prices():  # type: ignore[no-untyped-def]
    """价格规则列表。"""
    data = PriceService.list_all()
    return success_response(data=data)


@inventory_bp.post("/prices")
@login_required
def create_price():  # type: ignore[no-untyped-def]
    """创建价格规则。"""
    body = PriceCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = PriceService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@inventory_bp.put("/prices/<itemcd>/<busityp>")
@login_required
def update_price(itemcd: str, busityp: str):  # type: ignore[no-untyped-def]
    """更新价格规则。"""
    body = PriceUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = PriceService.update(itemcd, busityp, body.model_dump(exclude_none=True), user_cd)
    if data is None:
        return error_response(message="价格规则不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 调价 ----


@inventory_bp.get("/adjust-prices/<pabillid>")
@login_required
def list_adjust_prices(pabillid: str):  # type: ignore[no-untyped-def]
    """调价记录列表。"""
    data = AdjustPriceService.list_by_bill(pabillid)
    return success_response(data=data)


@inventory_bp.post("/adjust-prices")
@login_required
def create_adjust_price():  # type: ignore[no-untyped-def]
    """创建调价记录。"""
    body = AdjustPriceCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = AdjustPriceService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)
