# -*- coding: utf-8 -*-
"""
责任认定报表 API。
文件说明：提供责任认定报表主列表与明细查询接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/rep-liability-reports
- GET /api/v1/rep-liability-reports/<maintenance_id>/<liability_type>/details
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.rep_liability_report_service import RepLiabilityReportService
from app.utils.response import error_response, success_response

rep_liability_report_bp = Blueprint("rep_liability_report", __name__)
service = RepLiabilityReportService()


@rep_liability_report_bp.route("/rep-liability-reports", methods=["GET"])
def list_rep_liability_reports() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询责任认定报表主列表。"""
    try:
        result = service.list_reports(
            start_date=str(request.args.get("start_date") or "").strip(),
            end_date=str(request.args.get("end_date") or "").strip(),
            maintenance_id=request.args.get("maintenance_id"),
            store_id=request.args.get("store_id"),
            liability_type=request.args.get("liability_type"),
            exemptflg=request.args.get("exemptflg"),
            is_finish=request.args.get("is_finish"),
            deptnm=request.args.get("deptnm"),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 20)),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@rep_liability_report_bp.route(
    "/rep-liability-reports/<maintenance_id>/<liability_type>/details",
    methods=["GET"],
)
def list_rep_liability_report_details(
    maintenance_id: str,
    liability_type: str,
) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询责任认定报表明细。"""
    try:
        result = service.list_report_details(
            maintenance_id=maintenance_id,
            liability_type=liability_type,
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
