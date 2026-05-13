# -*- coding: utf-8 -*-
"""
免费更换配置更新 API。
文件说明：提供配置更新待确认列表、旧新配件明细与确认接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/pos-r-eid-updates
- GET /api/v1/pos-r-eid-updates/<renew_id>/<business_operation_id>
- GET /api/v1/pos-r-eid-updates/<renew_id>/<business_operation_id>/choices
- POST /api/v1/pos-r-eid-updates/confirm
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.pos_r_eid_update_service import PosREidUpdateService
from app.utils.response import error_response, success_response

pos_r_eid_update_bp = Blueprint("pos_r_eid_update", __name__)
service = PosREidUpdateService()


@pos_r_eid_update_bp.route("/pos-r-eid-updates", methods=["GET"])
def list_pos_r_eid_updates() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询配置更新待确认列表。"""
    try:
        result = service.list_updates(
            begin_date=request.args.get("begin_date"),
            end_date=request.args.get("end_date"),
            custcard=request.args.get("custcard"),
            renew_id=request.args.get("renew_id"),
            is_finish=request.args.get("is_finish"),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 20)),
        )
        return make_response(True, result)
    except Exception as exc:
        return make_response(False, error=str(exc)), 500


@pos_r_eid_update_bp.route(
    "/pos-r-eid-updates/<renew_id>/<int:business_operation_id>",
    methods=["GET"],
)
def get_pos_r_eid_update(
    renew_id: str,
    business_operation_id: int,
) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询单条配置更新记录。"""
    try:
        result = service.get_update(renew_id, business_operation_id)
        if not result:
            return make_response(False, error="record not found"), 404
        return make_response(True, result)
    except Exception as exc:
        return make_response(False, error=str(exc)), 500


@pos_r_eid_update_bp.route(
    "/pos-r-eid-updates/<renew_id>/<int:business_operation_id>/choices",
    methods=["GET"],
)
def get_pos_r_eid_choices(
    renew_id: str,
    business_operation_id: int,
) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询旧新配件选择明细。"""
    try:
        old_eid = str(request.args.get("old_eid") or "").strip()
        new_eid = str(request.args.get("new_eid") or "").strip()
        result = service.get_choices(
            renew_id=renew_id,
            business_operation_id=business_operation_id,
            old_eid=old_eid,
            new_eid=new_eid,
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@pos_r_eid_update_bp.route("/pos-r-eid-updates/confirm", methods=["POST"])
def confirm_pos_r_eid_update() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """确认配置更新。"""
    try:
        data = request.get_json() or {}

        renew_id = str(data.get("renew_id") or "").strip()
        old_eid = str(data.get("old_eid") or "").strip()
        new_eid = str(data.get("new_eid") or "").strip()
        oper_cd = str(data.get("oper_cd") or getattr(g, "user_cd", "")).strip()

        if not renew_id:
            return make_response(False, error="renew_id is required"), 400
        if not old_eid or not new_eid:
            return make_response(False, error="old_eid/new_eid is required"), 400

        try:
            business_operation_id = int(data.get("business_operation_id"))
        except (TypeError, ValueError):
            return make_response(
                False, error="business_operation_id must be integer"
            ), 400

        result = service.confirm_update(
            renew_id=renew_id,
            business_operation_id=business_operation_id,
            old_eid=old_eid,
            new_eid=new_eid,
            oper_cd=oper_cd,
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
