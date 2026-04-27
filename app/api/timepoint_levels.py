# -*- coding: utf-8 -*-
"""
时间点等级 API。
文件说明：提供等级定义维护、客户等级分配与清空接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/timepoint-levels
- POST /api/v1/timepoint-levels/save
- GET /api/v1/timepoint-levels/<levels>/customers
- POST /api/v1/timepoint-levels/assign-customers
- POST /api/v1/timepoint-levels/clear-customers
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.timepoint_levels_service import TimepointLevelsService
from app.utils.response import error_response, success_response

timepoint_levels_bp = Blueprint("timepoint_levels", __name__)
service = TimepointLevelsService()


@timepoint_levels_bp.route("/timepoint-levels", methods=["GET"])
def list_levels() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询等级定义列表。"""
    try:
        include_invalid = str(request.args.get("include_invalid", "0")).strip() in {
            "1",
            "true",
            "True",
        }
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))

        result = service.list_levels(
            include_invalid=include_invalid,
            page=page,
            page_size=page_size,
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@timepoint_levels_bp.route("/timepoint-levels/save", methods=["POST"])
def save_level() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """保存等级定义。"""
    try:
        data = request.get_json() or {}
        opercd = str(data.get("opercd") or getattr(g, "user_cd", "")).strip()
        beforetm = data.get("beforetm")
        aftertm = data.get("aftertm")

        result = service.save_level(
            levels=str(data.get("levels") or "").strip(),
            explain=str(data.get("explain") or "").strip(),
            opercd=opercd,
            timepoint=str(data.get("timepoint") or "").strip() or None,
            beforetm=float(beforetm)
            if beforetm is not None and str(beforetm).strip() != ""
            else None,
            aftertm=float(aftertm)
            if aftertm is not None and str(aftertm).strip() != ""
            else None,
            useflg=str(data.get("useflg", "1")).strip() or "1",
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@timepoint_levels_bp.route("/timepoint-levels/<levels>/customers", methods=["GET"])
def list_customers_by_level(levels: str) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """按等级查询客户。"""
    try:
        custcd = request.args.get("custcd")
        custnm = request.args.get("custnm")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))

        result = service.list_customers_by_level(
            levels=levels,
            custcd=custcd,
            custnm=custnm,
            page=page,
            page_size=page_size,
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@timepoint_levels_bp.route("/timepoint-levels/assign-customers", methods=["POST"])
def assign_customers() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """批量分配客户等级。"""
    try:
        data = request.get_json() or {}
        opercd = str(data.get("opercd") or getattr(g, "user_cd", "")).strip()

        result = service.assign_level_to_customers(
            levels=str(data.get("levels") or "").strip(),
            custcd_list=data.get("custcd_list") or [],
            opercd=opercd,
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@timepoint_levels_bp.route("/timepoint-levels/clear-customers", methods=["POST"])
def clear_customers() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """批量清空客户等级。"""
    try:
        data = request.get_json() or {}
        opercd = str(data.get("opercd") or getattr(g, "user_cd", "")).strip()

        result = service.clear_customer_levels(
            custcd_list=data.get("custcd_list") or [],
            opercd=opercd,
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
