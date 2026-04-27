# -*- coding: utf-8 -*-
"""
日常维护月度汇总报表 API。
文件说明：提供日常维护月度汇总报表查询接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/rep-maintenance-daily-m
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.rep_maintenance_daily_m_service import RepMaintenanceDailyMService
from app.utils.response import error_response, success_response

rep_maintenance_daily_m_bp = Blueprint("rep_maintenance_daily_m", __name__)
service = RepMaintenanceDailyMService()


@rep_maintenance_daily_m_bp.route("/rep-maintenance-daily-m", methods=["GET"])
def list_rep_maintenance_daily_m() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询日常维护月度汇总报表。"""
    try:
        result = service.list_reports(
            start_date=str(request.args.get("start_date") or "").strip(),
            end_date=str(request.args.get("end_date") or "").strip(),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
