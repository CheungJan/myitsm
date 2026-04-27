# -*- coding: utf-8 -*-
"""
日常保养报表 API。
文件说明：提供日常保养单报表查询接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/rep-maintenance-daily
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.rep_maintenance_daily_service import RepMaintenanceDailyService
from app.utils.response import error_response, success_response

rep_maintenance_daily_bp = Blueprint("rep_maintenance_daily", __name__)
service = RepMaintenanceDailyService()


@rep_maintenance_daily_bp.route("/rep-maintenance-daily", methods=["GET"])
def list_rep_maintenance_daily() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询日常保养报表。"""
    try:
        result = service.list_reports(
            start_date=str(request.args.get("start_date") or "").strip(),
            end_date=str(request.args.get("end_date") or "").strip(),
            custcard=request.args.get("custcard"),
            classcd=request.args.get("classcd"),
            engineer_id=request.args.get("engineer_id"),
            current_status=request.args.get("current_status"),
            itemcd=request.args.get("itemcd"),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 50)),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
