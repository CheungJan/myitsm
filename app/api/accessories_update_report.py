# -*- coding: utf-8 -*-
"""
配件更新报表 API。
文件说明：提供配件更新报表查询接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/accessories-update-reports
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.accessories_update_report_service import (
    AccessoriesUpdateReportService,
)
from app.utils.response import error_response, success_response

accessories_update_report_bp = Blueprint("accessories_update_report", __name__)
service = AccessoriesUpdateReportService()


@accessories_update_report_bp.route("/accessories-update-reports", methods=["GET"])
def list_accessories_update_reports() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询配件更新报表。"""
    try:
        result = service.list_reports(
            start_date=str(request.args.get("start_date") or "").strip(),
            end_date=str(request.args.get("end_date") or "").strip(),
            maintenance_id=request.args.get("maintenance_id"),
            store_id=request.args.get("store_id"),
            custcard=request.args.get("custcard"),
            itemcd=request.args.get("itemcd"),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 20)),
        )

        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
