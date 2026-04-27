# -*- coding: utf-8 -*-
"""
免责汇总 API。
文件说明：提供免责汇总列表、明细与批量审核接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/liability-summaries
- GET /api/v1/liability-summaries/<maintenance_id>/<liability_type>/details
- POST /api/v1/liability-summaries/audit
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.liability_sum_service import LiabilitySumService
from app.utils.response import error_response, success_response

liability_sum_bp = Blueprint("liability_sum", __name__)
service = LiabilitySumService()


@liability_sum_bp.route("/liability-summaries", methods=["GET"])
def list_liability_summaries() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询免责汇总列表。"""
    try:
        result = service.list_liability_summaries(
            begin_date=request.args.get("begin_date"),
            end_date=request.args.get("end_date"),
            store_id=request.args.get("store_id"),
            maintenance_id=request.args.get("maintenance_id"),
            deptnm=request.args.get("deptnm"),
            exemptflg=request.args.get("exemptflg"),
            liability_type=request.args.get("liability_type"),
            is_finish=request.args.get("is_finish"),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 20)),
        )
        return make_response(True, result)
    except Exception as exc:
        return make_response(False, error=str(exc)), 500


@liability_sum_bp.route(
    "/liability-summaries/<maintenance_id>/<liability_type>/details",
    methods=["GET"],
)
def list_liability_details(
    maintenance_id: str,
    liability_type: str,
) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询免责汇总明细。"""
    try:
        result = service.list_liability_details(
            maintenance_id=maintenance_id,
            liability_type=liability_type,
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@liability_sum_bp.route("/liability-summaries/audit", methods=["POST"])
def audit_liability_summaries() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """批量审核免责汇总。"""
    try:
        data = request.get_json() or {}
        records = data.get("records") or []
        oper_cd = str(data.get("oper_cd") or getattr(g, "user_cd", "")).strip()

        result = service.batch_audit(records=records, oper_cd=oper_cd)
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
