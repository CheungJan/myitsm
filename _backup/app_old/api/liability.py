# -*- coding: utf-8 -*-
"""
免责处理 API。
文件说明：提供 TIT10_MAINTENANCE_LIABILITY 的列表、详情、保存、审核及字典查询接口。
作者：Cascade
创建时间：2026-04-20

端点列表：
- GET /api/v1/liabilities：免责处理列表
- GET /api/v1/liabilities/<maintenance_id>/<liability_type>：免责处理详情
- POST /api/v1/liabilities/save：保存免责处理（分配/处理）
- POST /api/v1/liabilities/audit：批量审核免责处理
- GET /api/v1/liabilities/dictionary：免责科目字典
"""

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.liability_service import LiabilityService
from app.utils.response import error_response, success_response

liability_bp = Blueprint("liability", __name__)
service = LiabilityService()


@liability_bp.route("/liabilities", methods=["GET"])
def list_liabilities():
    """获取免责处理列表。"""
    try:
        begin_date = request.args.get("begin_date")
        end_date = request.args.get("end_date")
        maintenance_id = request.args.get("maintenance_id")
        exemptflg = request.args.get("exemptflg")
        liability_type = request.args.get("type")
        is_finish = request.args.get("is_finish")
        include_finished = str(request.args.get("include_finished", "0")).strip() in {
            "1",
            "true",
            "True",
        }
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))

        result = service.list_liabilities(
            begin_date=begin_date,
            end_date=end_date,
            maintenance_id=maintenance_id,
            exemptflg=exemptflg,
            liability_type=liability_type,
            is_finish=is_finish,
            include_finished=include_finished,
            page=page,
            page_size=page_size,
        )
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@liability_bp.route("/liabilities/<maintenance_id>/<liability_type>", methods=["GET"])
def get_liability(maintenance_id: str, liability_type: str):
    """获取免责处理详情。"""
    try:
        result = service.get_liability(
            maintenance_id=maintenance_id, liability_type=liability_type
        )
        if not result:
            return error_response(message="Liability not found"), 404
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@liability_bp.route("/liabilities/save", methods=["POST"])
def save_liability():
    """保存免责处理（分配/处理）。"""
    try:
        data = request.get_json() or {}
        required_fields = ["maintenance_id", "type", "scene"]
        for field in required_fields:
            if field not in data or not str(data.get(field)).strip():
                return error_response(
                    message=f"Missing required field: {field}"
                ), 400

        oper_cd = str(data.get("oper_cd") or getattr(g, "user_cd", "")).strip()
        if not oper_cd:
            return error_response(message="oper_cd is required"), 400

        result = service.save_liability(
            maintenance_id=str(data.get("maintenance_id")).strip(),
            liability_type=str(data.get("type")).strip(),
            oper_cd=oper_cd,
            scene=str(data.get("scene")).strip(),
            exceptionscd=data.get("exceptionscd"),
            exceptionsnm=data.get("exceptionsnm"),
            deptnm=data.get("deptnm"),
            assessflg=str(data.get("assessflg", "N")).strip() or "N",
            exemptflg=str(data.get("exemptflg", "N")).strip() or "N",
            useflg=str(data.get("useflg", "1")).strip() or "1",
            setfrom=data.get("setfrom"),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@liability_bp.route("/liabilities/audit", methods=["POST"])
def audit_liabilities():
    """批量审核免责处理（2->3）。"""
    try:
        data = request.get_json() or {}
        maintenance_ids = data.get("maintenance_ids") or []
        if not isinstance(maintenance_ids, list) or not maintenance_ids:
            return error_response(
                message="maintenance_ids is required and must be non-empty list"
            ), 400

        oper_cd = str(data.get("oper_cd") or getattr(g, "user_cd", "")).strip()
        if not oper_cd:
            return error_response(message="oper_cd is required"), 400

        cleaned_ids = [str(mid).strip() for mid in maintenance_ids if str(mid).strip()]
        if not cleaned_ids:
            return error_response(
                message="maintenance_ids is empty after clean"
            ), 400

        result = service.audit_liabilities(maintenance_ids=cleaned_ids, oper_cd=oper_cd)
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@liability_bp.route("/liabilities/dictionary", methods=["GET"])
def list_liability_dictionary():
    """查询免责科目字典。"""
    try:
        class_code_like = request.args.get("class_code")
        result = service.list_liability_dictionary(class_code_like=class_code_like)
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
