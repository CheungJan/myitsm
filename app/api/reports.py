"""
报表查询 API。

路由前缀：/api/v1/reports
提供库存快照/预警/流水、EID 生命周期、销售状态汇总、BOM 结构树等报表端点。
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.report import (
    BOMTreeQuery,
    EidLifecycleQuery,
    InventorySnapshotQuery,
    MovementLogQuery,
    SalesReportQuery,
)
from app.services.report_service import (
    BOMReportService,
    EidReportService,
    InventoryReportService,
    SalesReportService,
)
from app.utils.response import error_response, success_response

__all__ = ["report_bp"]

report_bp = Blueprint("reports", __name__)

# ── 库存报表 ──


@report_bp.get("/inventory/snapshot")
@login_required
def inventory_snapshot():  # type: ignore[no-untyped-def]
    """库存快照：当前各仓库各物料库存余量。"""
    params = InventorySnapshotQuery.model_validate(request.args.to_dict())
    data = InventoryReportService.snapshot(
        whcd=params.whcd,
        itemtyp=params.itemtyp,
        itemcd=params.itemcd,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@report_bp.get("/inventory/alert")
@login_required
def inventory_alert():  # type: ignore[no-untyped-def]
    """库存预警清单：当前库存低于预警下限的物料。"""
    data = InventoryReportService.alert_items()
    return success_response(data=data)


@report_bp.get("/inventory/movement-log")
@login_required
def inventory_movement_log():  # type: ignore[no-untyped-def]
    """库存变动流水查询。"""
    params = MovementLogQuery.model_validate(request.args.to_dict())
    data = InventoryReportService.movement_log(
        whcd=params.whcd,
        itemcd=params.itemcd,
        start_date=params.start_date,
        end_date=params.end_date,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


# ── EID 追踪 ──


@report_bp.get("/eid/lifecycle")
@login_required
def eid_lifecycle():  # type: ignore[no-untyped-def]
    """EID 全生命周期追踪列表。"""
    params = EidLifecycleQuery.model_validate(request.args.to_dict())
    data = EidReportService.lifecycle(
        eid_val=params.eid,
        itemcd_val=params.itemcd,
        custcd=params.custcd,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@report_bp.get("/eid/<eid>/tracks")
@login_required
def eid_tracks(eid: str):  # type: ignore[no-untyped-def]
    """单个 EID 变更追溯明细。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    data = EidReportService.tracks(eid, page=page, per_page=per_page)
    return success_response(data=data)


# ── 销售报表 ──


@report_bp.get("/sales/status-summary")
@login_required
def sales_status_summary():  # type: ignore[no-untyped-def]
    """销售状态汇总统计。"""
    params = SalesReportQuery.model_validate(request.args.to_dict())
    data = SalesReportService.status_summary(
        start_date=params.start_date,
        end_date=params.end_date,
    )
    return success_response(data=data)


@report_bp.get("/sales/open-bills")
@login_required
def sales_open_bills():  # type: ignore[no-untyped-def]
    """未结单据清单（预计划+销售+延期）。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    data = SalesReportService.open_bills(page=page, per_page=per_page)
    return success_response(data=data)


# ── BOM 报表 ──


@report_bp.get("/bom/tree")
@login_required
def bom_tree():  # type: ignore[no-untyped-def]
    """BOM 结构树查询：主物料→子物料清单。"""
    params = BOMTreeQuery.model_validate(request.args.to_dict())
    data = BOMReportService.bom_tree(
        itemcd_val=params.itemcd,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)
