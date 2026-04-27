# -*- coding: utf-8 -*-
"""
免责分部门处理 API。
文件说明：提供分部门免责处理列表、明细与保存接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/liability-groups
- GET /api/v1/liability-groups/<maintenance_id>/<liability_type>/details
- POST /api/v1/liability-groups/save
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.liability_group_service import LiabilityGroupService
from app.utils.response import error_response, success_response

liability_group_bp = Blueprint("liability_group", __name__)
service = LiabilityGroupService()


@liability_group_bp.route("/liability-groups", methods=["GET"])
def list_liability_groups() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询分部门免责处理列表。"""
    try:
        user_cd = str(request.args.get("user_cd") or getattr(g, "user_cd", "")).strip()
        result = service.list_liability_groups(
            user_cd=user_cd,
            begin_date=request.args.get("begin_date"),
            end_date=request.args.get("end_date"),
            store_id=request.args.get("store_id"),
            maintenance_id=request.args.get("maintenance_id"),
            exemptflg=str(request.args.get("exemptflg", "%")),
            liability_type=str(request.args.get("liability_type", "%")),
            is_finish=str(request.args.get("is_finish", "1")),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 20)),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@liability_group_bp.route(
    "/liability-groups/<maintenance_id>/<liability_type>/details",
    methods=["GET"],
)
def list_liability_group_details(
    maintenance_id: str,
    liability_type: str,
) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询免责明细。"""
    try:
        result = service.list_details(
            maintenance_id=maintenance_id,
            liability_type=liability_type,
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@liability_group_bp.route("/liability-groups/save", methods=["POST"])
def save_liability_group_detail() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """保存免责明细。"""
    try:
        data = request.get_json() or {}

        maintenance_id = str(data.get("maintenance_id") or "").strip()
        liability_type = str(data.get("liability_type") or "").strip()
        oper_cd = str(data.get("oper_cd") or getattr(g, "user_cd", "")).strip()

        result = service.save_detail(
            maintenance_id=maintenance_id,
            liability_type=liability_type,
            oper_cd=oper_cd,
            exceptionscd=data.get("exceptionscd"),
            exceptionsnm=data.get("exceptionsnm"),
            deptnm=data.get("deptnm"),
            assessflg=str(data.get("assessflg", "N")),
            exemptflg=str(data.get("exemptflg", "N")),
        )

        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
