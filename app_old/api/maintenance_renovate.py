# -*- coding: utf-8 -*-
"""
旧机翻新单API
文件说明：提供旧机翻新单管理端点
作者：Cascade
创建时间：2026-04-08

端点列表：
- GET /api/v1/maintenance-renovates：翻新单列表
- GET /api/v1/maintenance-renovates/<id>：翻新单详情
- GET /api/v1/maintenance-renovates/<id>/equipment-renovates：翻新设备明细
- GET /api/v1/maintenance-renovates/<id>/d2d-records：上门服务记录
- GET /api/v1/maintenance-renovates/<id>/transitions：允许的流转
- POST /api/v1/maintenance-renovates：创建翻新单
- POST /api/v1/maintenance-renovates/<id>/equipment-renovates：新增翻新设备明细
- POST /api/v1/maintenance-renovates/<id>/d2d-records：新增上门服务记录
- POST /api/v1/maintenance-renovates/<id>/transition：状态流转
- POST /api/v1/maintenance-renovates/<id>/cancel：取消翻新单
"""

from flask import Blueprint, request, g
from typing import Dict, Any

from app.services.maintenance_renovate_service import MaintenanceRenovateService
from app.services.maintenance_d2d_service import MaintenanceD2DService
from app.services.state_machine import MaintenanceState

maintenance_renovate_bp = Blueprint("maintenance_renovate", __name__)
service = MaintenanceRenovateService()
_d2d_service = MaintenanceD2DService()


def make_response(success: bool, data: Dict[str, Any] = None, error: str = None) -> Dict[str, Any]:
    """统一响应格式"""
    resp = {"success": success, "request_id": getattr(g, "request_id", None)}
    if data:
        resp["data"] = data
    if error:
        resp["error"] = error
    return resp


@maintenance_renovate_bp.route("/maintenance-renovates", methods=["GET"])
def list_maintenance_renovates():
    """获取翻新单列表"""
    try:
        store_id = request.args.get("store_id")
        status = request.args.get("status")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))

        result = service.list_maintenance_renovates(
            store_id=store_id,
            status=status,
            page=page,
            page_size=page_size,
        )

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_renovate_bp.route("/maintenance-renovates/<renovate_id>", methods=["GET"])
def get_maintenance_renovate(renovate_id: str):
    """获取翻新单详情"""
    try:
        result = service.get_maintenance_renovate(renovate_id)
        if not result:
            return make_response(False, error="Maintenance renovate not found"), 404

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_renovate_bp.route(
    "/maintenance-renovates/<renovate_id>/equipment-renovates",
    methods=["GET"],
)
def list_equipment_renovates(renovate_id: str):
    """获取翻新设备明细列表（TIT15_EQUIPMENT_RENOVATE）"""
    try:
        result = service.list_equipment_renovates(renovate_id)
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400
        return make_response(True, result)
    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_renovate_bp.route(
    "/maintenance-renovates/<renovate_id>/equipment-renovates",
    methods=["POST"],
)
def create_equipment_renovate(renovate_id: str):
    """新增翻新设备明细（TIT15_EQUIPMENT_RENOVATE）"""
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

        result = service.create_equipment_renovate(
            renovate_id=renovate_id,
            business_operation_id=business_operation_id,
            device_id=str(data.get("device_id", "")).strip(),
            creator=str(data.get("creator") or getattr(g, "user_cd", "")).strip(),
            new_device_id=data.get("new_device_id"),
            price=data.get("price"),
            delivery_id=data.get("delivery_id"),
            is_finish=str(data.get("is_finish", "0")).strip() or "0",
            is_change=data.get("is_change"),
            change_eid=data.get("change_eid"),
        )
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result), 201
    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_renovate_bp.route("/maintenance-renovates/<renovate_id>/transitions", methods=["GET"])
def get_allowed_transitions(renovate_id: str):
    """获取允许的状态流转"""
    try:
        result = service.get_allowed_transitions(renovate_id)
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_renovate_bp.route("/maintenance-renovates", methods=["POST"])
def create_maintenance_renovate():
    """创建翻新单"""
    try:
        data = request.get_json()
        if not data:
            return make_response(False, error="Request body required"), 400

        required_fields = ["renovate_id", "store_id"]
        for field in required_fields:
            if field not in data:
                return make_response(False, error=f"Missing required field: {field}"), 400

        result = service.create_maintenance_renovate(
            renovate_id=data.get("renovate_id"),
            store_id=data.get("store_id"),
            old_device_id=data.get("old_device_id"),
            new_device_id=data.get("new_device_id"),
            renovate_type=data.get("renovate_type"),
            oper_cd=getattr(g, "user_cd", None),
            remark=data.get("remark"),
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result), 201

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_renovate_bp.route("/maintenance-renovates/<renovate_id>/transition", methods=["POST"])
def transition_state(renovate_id: str):
    """通用状态流转"""
    try:
        data = request.get_json()
        if not data or "to_status" not in data:
            return make_response(False, error="to_status is required"), 400

        result = service.transition_state(
            renovate_id=renovate_id,
            to_status=data.get("to_status"),
            oper_cd=getattr(g, "user_cd", None),
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_renovate_bp.route("/maintenance-renovates/<renovate_id>/cancel", methods=["POST"])
def cancel_renovate(renovate_id: str):
    """取消翻新单"""
    try:
        result = service.cancel_renovate(
            renovate_id=renovate_id,
            oper_cd=getattr(g, "user_cd", None),
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_renovate_bp.route("/maintenance-renovates/<renovate_id>/d2d-records", methods=["GET"])
def list_d2d_records(renovate_id: str):
    """获取上门服务记录列表（TIT23_MAINTENANCE_D2D，d2d_type='2'）"""
    try:
        result = _d2d_service.list_d2d_records(
            maintenance_id=renovate_id,
            d2d_type="2",
        )
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400
        return make_response(True, result)
    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_renovate_bp.route("/maintenance-renovates/<renovate_id>/d2d-records", methods=["POST"])
def create_d2d_record(renovate_id: str):
    """新增上门服务记录（TIT23_MAINTENANCE_D2D，d2d_type='2'）"""
    try:
        data = request.get_json() or {}

        required_fields = ["business_operation_id"]
        for field in required_fields:
            if field not in data:
                return make_response(False, error=f"Missing required field: {field}"), 400

        try:
            business_operation_id = int(data.get("business_operation_id"))
        except (TypeError, ValueError):
            return make_response(False, error="business_operation_id must be integer"), 400

        result = _d2d_service.create_d2d_record(
            maintenance_id=renovate_id,
            business_operation_id=business_operation_id,
            creator=str(data.get("creator") or getattr(g, "user_cd", "")).strip(),
            d2d_engineer=data.get("d2d_engineer"),
            arrive_time=data.get("arrive_time"),
            leave_time=data.get("leave_time"),
            jjbz=data.get("jjbz"),
            d2d_description=data.get("d2d_description"),
            d2d_phone=data.get("d2d_phone"),
            old_business_id=data.get("old_business_id"),
            d2d_group=data.get("d2d_group"),
            d2d_type="2",
            pos_status=data.get("pos_status"),
            pos_status1=data.get("pos_status1"),
        )
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result), 201
    except Exception as e:
        return make_response(False, error=str(e)), 500
