# -*- coding: utf-8 -*-
"""
分派报表 API。
文件说明：提供分派报表查询接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/dispatch-reports
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.dispatch_report_service import DispatchReportService
from app.utils.response import error_response, success_response

dispatch_report_bp = Blueprint("dispatch_report", __name__)
service = DispatchReportService()


@dispatch_report_bp.route("/dispatch-reports", methods=["GET"])
def list_dispatch_reports() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询分派报表。"""
    try:
        result = service.list_reports(
            start_date=str(request.args.get("start_date") or "").strip(),
            end_date=str(request.args.get("end_date") or "").strip(),
            maintenance_id=request.args.get("maintenance_id"),
            custcard=request.args.get("custcard"),
            custnm=request.args.get("custnm"),
            accpectd_group=request.args.get("accpectd_group"),
            accpectder=request.args.get("accpectder"),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 20)),
        )

        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
