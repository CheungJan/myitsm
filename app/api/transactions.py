"""
全模块事务查询与错账更正 API。

路由前缀：/api/v1/transactions
提供跨模块单据统一查询、错账冲销、进销存汇总。
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.transaction import AllBillQuery, ErrorCorrectionCreate, StockSummaryQuery
from app.services.transaction_service import (
    ErrorCorrectionService,
    StockSummaryService,
    TransactionService,
)
from app.utils.response import error_response, success_response

__all__ = ["transaction_bp"]

transaction_bp = Blueprint("transactions", __name__)

# ── 单据类型 ──


@transaction_bp.get("/bill-types")
@login_required
def get_bill_types():  # type: ignore[no-untyped-def]
    """获取所有单据类型列表。"""
    data = TransactionService.get_bill_types()
    return success_response(data=data)


# ── 全模块单据统一查询 ──


@transaction_bp.get("/bills")
@login_required
def list_all_bills():  # type: ignore[no-untyped-def]
    """跨模块联合查询所有单据。"""
    params = AllBillQuery.model_validate(request.args.to_dict())
    data = TransactionService.list_all_bills(
        bill_type=params.bill_type,
        store_id=params.store_id,
        status=params.status,
        start_date=params.start_date,
        end_date=params.end_date,
        keyword=params.keyword,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


# ── 错账更正（红蓝单冲销） ──


@transaction_bp.post("/error-correction")
@login_required
def reverse_bill():  # type: ignore[no-untyped-def]
    """红字冲销单据（标记原单为已冲销）。"""
    body = ErrorCorrectionCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    result = ErrorCorrectionService.reverse(body.table_name, body.record_id, user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result["data"], message="冲销成功")


# ── 进销存汇总 ──


@transaction_bp.get("/stock-summary")
@login_required
def get_stock_summary():  # type: ignore[no-untyped-def]
    """进销存汇总报表（按物料+仓库聚合期初/入库/出库/期末）。"""
    params = StockSummaryQuery.model_validate(request.args.to_dict())
    data = StockSummaryService.get_summary(
        whcd=params.whcd,
        itemtyp=params.itemtyp,
        start_date=params.start_date,
        end_date=params.end_date,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)
