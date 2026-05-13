# -*- coding: utf-8 -*-
"""
纸张平均报表 API。
文件说明：提供工程师达标率/纸张平均报表查询接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/paper-average-reports
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.paper_average_report_service import PaperAverageReportService
from app.utils.response import error_response, success_response

paper_average_report_bp = Blueprint("paper_average_report", __name__)
service = PaperAverageReportService()


@paper_average_report_bp.route("/paper-average-reports", methods=["GET"])
def list_paper_average_reports() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询纸张平均报表。"""
    try:
        result = service.list_reports(
            start_date=str(request.args.get("start_date") or "").strip(),
            end_date=str(request.args.get("end_date") or "").strip(),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 50)),
        )

        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
