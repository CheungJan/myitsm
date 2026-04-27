# -*- coding: utf-8 -*-
"""
日常维护年月汇总报表 API。
文件说明：提供日常维护年月汇总报表查询接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/rep-maintenance-daily-ym
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.rep_maintenance_daily_ym_service import RepMaintenanceDailyYmService
from app.utils.response import error_response, success_response

rep_maintenance_daily_ym_bp = Blueprint("rep_maintenance_daily_ym", __name__)
service = RepMaintenanceDailyYmService()


@rep_maintenance_daily_ym_bp.route("/rep-maintenance-daily-ym", methods=["GET"])
def list_rep_maintenance_daily_ym() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询日常维护年月汇总报表（参数 in_ym 格式 YYYYMM）。"""
    try:
        result = service.list_reports(
            in_ym=str(request.args.get("in_ym") or "").strip(),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
