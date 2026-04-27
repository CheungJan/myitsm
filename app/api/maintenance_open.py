# -*- coding: utf-8 -*-
"""
新机开通单API
文件说明：提供新机开通单管理端点
作者：Cascade
创建时间：2026-04-08

端点列表：
- GET /api/v1/maintenance-opens：开通单列表
- GET /api/v1/maintenance-opens/<id>：开通单详情
- GET /api/v1/maintenance-opens/<id>/transitions：允许的流转
- GET /api/v1/maintenance-opens/<id>/equipment-opens：开通设备明细列表
- POST /api/v1/maintenance-opens：创建开通单
- POST /api/v1/maintenance-opens/<id>/equipment-opens：新增开通设备明细
- POST /api/v1/maintenance-opens/<id>/transition：状态流转
- POST /api/v1/maintenance-opens/<id>/cancel：取消开通单
"""

from flask import Blueprint, request, g
from typing import Dict, Any

from app.services.maintenance_open_service import MaintenanceOpenService
from app.services.state_machine import MaintenanceState

maintenance_open_bp = Blueprint("maintenance_open", __name__)
service = MaintenanceOpenService()


def make_response(success: bool, data: Dict[str, Any] = None, error: str = None) -> Dict[str, Any]:
    """统一响应格式"""
    resp = {"success": success, "request_id": getattr(g, "request_id", None)}
    if data:
        resp["data"] = data
    if error:
        resp["error"] = error
    return resp


@maintenance_open_bp.route("/maintenance-opens", methods=["GET"])
def list_maintenance_opens():
    """获取开通单列表"""
    try:
        store_id = request.args.get("store_id")
        status = request.args.get("status")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))

        result = service.list_maintenance_opens(
            store_id=store_id,
            status=status,
            page=page,
            page_size=page_size,
        )

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_open_bp.route("/maintenance-opens/<new_opening_id>/equipment-opens", methods=["GET"])
def list_equipment_opens(new_opening_id: str):
    """获取开通设备明细列表（TIT14_EQUIPMENT_OPEN）"""
    try:
        result = service.list_equipment_opens(new_opening_id)
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400
        return make_response(True, result)
    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_open_bp.route("/maintenance-opens/<new_opening_id>/equipment-opens", methods=["POST"])
def create_equipment_open(new_opening_id: str):
    """新增开通设备明细（TIT14_EQUIPMENT_OPEN）"""
    try:
        data = request.get_json() or {}

        required_fields = ["business_operation_id", "device_id"]
        for field in required_fields:
            if field not in data:
                return make_response(False, error=f"Missing required field: {field}"), 400

        try:
            business_operation_id = int(data.get("business_operation_id"))
        except (TypeError, ValueError):
            return make_response(False, error="business_operation_id must be integer"), 400

        result = service.create_equipment_open(
            new_opening_id=new_opening_id,
            business_operation_id=business_operation_id,
            device_id=str(data.get("device_id", "")).strip(),
            creator=str(data.get("creator") or getattr(g, "user_cd", "")).strip(),
            price=data.get("price"),
            delivery_id=data.get("delivery_id"),
            is_finish=str(data.get("is_finish", "0")).strip() or "0",
            is_change=data.get("is_change"),
            change_eid=data.get("change_eid"),
            from_custcard=data.get("from_custcard"),
            to_custcard=data.get("to_custcard"),
            mobile_no=data.get("mobile_no"),
            oper_memo=data.get("oper_memo"),
            card_type=data.get("card_type"),
            cust_id=data.get("cust_id"),
        )
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result), 201
    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_open_bp.route("/maintenance-opens/<new_opening_id>", methods=["GET"])
def get_maintenance_open(new_opening_id: str):
    """获取开通单详情"""
    try:
        result = service.get_maintenance_open(new_opening_id)
        if not result:
            return make_response(False, error="Maintenance open not found"), 404

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_open_bp.route("/maintenance-opens/<new_opening_id>/transitions", methods=["GET"])
def get_allowed_transitions(new_opening_id: str):
    """获取允许的状态流转"""
    try:
        result = service.get_allowed_transitions(new_opening_id)
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_open_bp.route("/maintenance-opens", methods=["POST"])
def create_maintenance_open():
    """创建开通单"""
    try:
        data = request.get_json()
        if not data:
            return make_response(False, error="Request body required"), 400

        required_fields = ["new_opening_id", "store_id"]
        for field in required_fields:
            if field not in data:
                return make_response(False, error=f"Missing required field: {field}"), 400

        result = service.create_maintenance_open(
            new_opening_id=data.get("new_opening_id"),
            store_id=data.get("store_id"),
            device_id=data.get("device_id"),
            open_type=data.get("open_type"),
            oper_cd=getattr(g, "user_cd", None),
            remark=data.get("remark"),
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result), 201

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_open_bp.route("/maintenance-opens/<new_opening_id>/transition", methods=["POST"])
def transition_state(new_opening_id: str):
    """通用状态流转"""
    try:
        data = request.get_json()
        if not data or "to_status" not in data:
            return make_response(False, error="to_status is required"), 400

        result = service.transition_state(
            new_opening_id=new_opening_id,
            to_status=data.get("to_status"),
            oper_cd=getattr(g, "user_cd", None),
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_open_bp.route("/maintenance-opens/<new_opening_id>/cancel", methods=["POST"])
def cancel_open(new_opening_id: str):
    """取消开通单"""
    try:
        result = service.cancel_open(
            new_opening_id=new_opening_id,
            oper_cd=getattr(g, "user_cd", None),
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500
