# -*- coding: utf-8 -*-
"""
免费更换单 API。
文件说明：提供 TIT28_FREE_REPLACE/TIT28_FREE_REPLACE_DT 的查询、创建、作废、关单接口。
作者：Cascade
创建时间：2026-04-20

端点列表：
- GET /api/v1/free-replaces：免费更换单列表
- GET /api/v1/free-replaces/<renew_id>：免费更换单详情
- GET /api/v1/free-replaces/<renew_id>/details：免费更换设备明细
- POST /api/v1/free-replaces：创建免费更换单
- POST /api/v1/free-replaces/<renew_id>/details：新增免费更换设备明细
- POST /api/v1/free-replaces/<renew_id>/cancel：作废免费更换单
- POST /api/v1/free-replaces/<renew_id>/close：关闭免费更换单
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.free_replace_service import FreeReplaceService
from app.utils.response import error_response, success_response

free_replace_bp = Blueprint("free_replace", __name__)
service = FreeReplaceService()


@free_replace_bp.route("/free-replaces", methods=["GET"])
def list_free_replaces() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """获取免费更换单列表。"""
    try:
        store_id = request.args.get("store_id")
        current_status = request.args.get("current_status")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))

        result = service.list_free_replaces(
            store_id=store_id,
            current_status=current_status,
            page=page,
            page_size=page_size,
        )
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@free_replace_bp.route("/free-replaces/<renew_id>", methods=["GET"])
def get_free_replace(renew_id: str) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """获取免费更换单详情。"""
    try:
        result = service.get_free_replace(renew_id)
        if not result:
            return error_response(message="Free replace not found"), 404
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@free_replace_bp.route("/free-replaces/<renew_id>/details", methods=["GET"])
def list_free_replace_details(
    renew_id: str,
) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """获取免费更换设备明细。"""
    try:
        result = service.list_free_replace_details(renew_id)
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@free_replace_bp.route("/free-replaces", methods=["POST"])
def create_free_replace() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """创建免费更换单。"""
    try:
        data = request.get_json() or {}
        required_fields = ["renew_id", "store_id"]
        for field in required_fields:
            if field not in data or not str(data.get(field)).strip():
                return error_response(
                    message=f"Missing required field: {field}"
                ), 400

        creator = str(data.get("creator") or getattr(g, "user_cd", "")).strip()
        if not creator:
            return error_response(message="creator is required"), 400

        count_value = data.get("count")
        if count_value is not None:
            try:
                count_value = int(count_value)
            except (TypeError, ValueError):
                return error_response(message="count must be integer"), 400

        result = service.create_free_replace(
            renew_id=str(data.get("renew_id")).strip(),
            store_id=str(data.get("store_id")).strip(),
            creator=creator,
            company_id=data.get("company_id"),
            request_time=data.get("request_time"),
            request_paper_id=data.get("request_paper_id"),
            old_device_id=data.get("old_device_id"),
            new_device_id=data.get("new_device_id"),
            deliver_no=data.get("deliver_no"),
            count=count_value,
            expected_completion_time=data.get("expected_completion_time"),
            short_description=data.get("short_description"),
            detail_description=data.get("detail_description"),
            current_status=str(data.get("current_status", "1")).strip() or "1",
            is_success=data.get("is_success"),
            is_old=str(data.get("is_old", "0")).strip() or "0",
            is_back=data.get("is_back"),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result), 201
    except Exception as exc:
        return error_response(message=str(exc)), 500


@free_replace_bp.route("/free-replaces/<renew_id>/details", methods=["POST"])
def create_free_replace_detail(
    renew_id: str,
) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """新增免费更换设备明细。"""
    try:
        data = request.get_json() or {}
        if "business_operation_id" not in data:
            return error_response(
                message="Missing required field: business_operation_id"
            ), 400

        try:
            business_operation_id = int(data.get("business_operation_id"))
        except (TypeError, ValueError):
            return error_response(
                message="business_operation_id must be integer"
            ), 400

        creator = str(data.get("creator") or getattr(g, "user_cd", "")).strip()
        if not creator:
            return error_response(message="creator is required"), 400

        result = service.create_free_replace_detail(
            renew_id=renew_id,
            business_operation_id=business_operation_id,
            creator=creator,
            device_id=data.get("device_id"),
            new_device_id=data.get("new_device_id"),
            delivery_id=data.get("delivery_id"),
            is_finish=str(data.get("is_finish", "0")).strip() or "0",
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result), 201
    except Exception as exc:
        return error_response(message=str(exc)), 500


@free_replace_bp.route("/free-replaces/<renew_id>/cancel", methods=["POST"])
def cancel_free_replace(renew_id: str) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """作废免费更换单。"""
    try:
        oper_cd = str(
            (request.get_json() or {}).get("oper_cd") or getattr(g, "user_cd", "")
        ).strip()
        if not oper_cd:
            return error_response(message="oper_cd is required"), 400

        result = service.cancel_free_replace(renew_id=renew_id, oper_cd=oper_cd)
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@free_replace_bp.route("/free-replaces/<renew_id>/close", methods=["POST"])
def close_free_replace(renew_id: str) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """关闭免费更换单。"""
    try:
        oper_cd = str(
            (request.get_json() or {}).get("oper_cd") or getattr(g, "user_cd", "")
        ).strip()
        if not oper_cd:
            return error_response(message="oper_cd is required"), 400

        result = service.close_free_replace(renew_id=renew_id, oper_cd=oper_cd)
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
