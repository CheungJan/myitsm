# -*- coding: utf-8 -*-
"""
日常保养单API
文件说明：提供日常保养单管理端点
作者：Cascade
创建时间：2026-04-08

端点列表：
- GET /api/v1/maintenance-dailies：保养单列表
- GET /api/v1/maintenance-dailies/<id>：保养单详情
- GET /api/v1/maintenance-dailies/<id>/cust-pos-dailies：保养设备明细
- GET /api/v1/maintenance-dailies/<id>/d2d-records：上门服务记录
- GET /api/v1/maintenance-dailies/<id>/transitions：允许的流转
- POST /api/v1/maintenance-dailies：创建保养单
- POST /api/v1/maintenance-dailies/<id>/cust-pos-dailies：新增保养设备明细
- POST /api/v1/maintenance-dailies/<id>/d2d-records：新增上门服务记录
- POST /api/v1/maintenance-dailies/<id>/transition：状态流转
- POST /api/v1/maintenance-dailies/<id>/cancel：取消保养单
"""

from flask import Blueprint, request, g
from typing import Dict, Any

from app.services.maintenance_daily_service import MaintenanceDailyService
from app.services.maintenance_d2d_service import MaintenanceD2DService
from app.services.state_machine import MaintenanceState

maintenance_daily_bp = Blueprint("maintenance_daily", __name__)
service = MaintenanceDailyService()
_d2d_service = MaintenanceD2DService()


def make_response(success: bool, data: Dict[str, Any] = None, error: str = None) -> Dict[str, Any]:
    """统一响应格式"""
    resp = {"success": success, "request_id": getattr(g, "request_id", None)}
    if data:
        resp["data"] = data
    if error:
        resp["error"] = error
    return resp


@maintenance_daily_bp.route("/maintenance-dailies", methods=["GET"])
def list_maintenance_dailies():
    """获取保养单列表"""
    try:
        store_id = request.args.get("store_id")
        status = request.args.get("status")
        maintenance_type = request.args.get("maintenance_type")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))

        result = service.list_maintenance_dailies(
            store_id=store_id,
            status=status,
            maintenance_type=maintenance_type,
            page=page,
            page_size=page_size,
        )

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_daily_bp.route("/maintenance-dailies/<daily_maintenance_id>", methods=["GET"])
def get_maintenance_daily(daily_maintenance_id: str):
    """获取保养单详情"""
    try:
        result = service.get_maintenance_daily(daily_maintenance_id)
        if not result:
            return make_response(False, error="Maintenance daily not found"), 404

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_daily_bp.route(
    "/maintenance-dailies/<daily_maintenance_id>/cust-pos-dailies",
    methods=["GET"],
)
def list_cust_pos_daily(daily_maintenance_id: str):
    """获取保养设备明细列表（TIT17_CUST_POS_DAILY）"""
    try:
        result = service.list_cust_pos_daily(daily_maintenance_id)
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400
        return make_response(True, result)
    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_daily_bp.route(
    "/maintenance-dailies/<daily_maintenance_id>/cust-pos-dailies",
    methods=["POST"],
)
def create_cust_pos_daily(daily_maintenance_id: str):
    """新增保养设备明细（TIT17_CUST_POS_DAILY）"""
    try:
        data = request.get_json() or {}

        required_fields = [
            "business_operation_id",
            "cust_cd",
            "eid",
            "item_cd",
            "typflg",
        ]
        for field in required_fields:
            if field not in data:
                return make_response(False, error=f"Missing required field: {field}"), 400

        try:
            business_operation_id = int(data.get("business_operation_id"))
        except (TypeError, ValueError):
            return make_response(False, error="business_operation_id must be integer"), 400

        result = service.create_cust_pos_daily(
            daily_maintenance_id=daily_maintenance_id,
            business_operation_id=business_operation_id,
            cust_cd=str(data.get("cust_cd", "")).strip(),
            eid=str(data.get("eid", "")).strip(),
            item_cd=str(data.get("item_cd", "")).strip(),
            typflg=str(data.get("typflg", "")).strip(),
            creator=str(data.get("creator") or getattr(g, "user_cd", "")).strip(),
            status=str(data.get("status", "1")).strip() or "1",
            start_date=data.get("start_date"),
            sys_info=data.get("sys_info"),
            soft_info=data.get("soft_info"),
            pos_upd_date=data.get("pos_upd_date"),
            pos_info=data.get("pos_info"),
            area=data.get("area"),
            maintenance_date=data.get("maintenance_date"),
            maintenance_typ=data.get("maintenance_typ"),
            request_enginner_id=data.get("request_enginner_id"),
            request_time=data.get("request_time"),
            short_description=data.get("short_description"),
            detail_description=data.get("detail_description"),
        )
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result), 201
    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_daily_bp.route("/maintenance-dailies/<daily_maintenance_id>/transitions", methods=["GET"])
def get_allowed_transitions(daily_maintenance_id: str):
    """获取允许的状态流转"""
    try:
        result = service.get_allowed_transitions(daily_maintenance_id)
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_daily_bp.route("/maintenance-dailies", methods=["POST"])
def create_maintenance_daily():
    """创建保养单"""
    try:
        data = request.get_json()
        if not data:
            return make_response(False, error="Request body required"), 400

        required_fields = ["daily_maintenance_id", "store_id"]
        for field in required_fields:
            if field not in data:
                return make_response(False, error=f"Missing required field: {field}"), 400

        result = service.create_maintenance_daily(
            daily_maintenance_id=data.get("daily_maintenance_id"),
            store_id=data.get("store_id"),
            maintenance_plan_id=data.get("maintenance_plan_id"),
            has_video_device=data.get("has_video_device", "N"),
            video_device_status=data.get("video_device_status"),
            maintenance_type=data.get("maintenance_type"),
            oper_cd=getattr(g, "user_cd", None),
            remark=data.get("remark"),
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result), 201

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_daily_bp.route("/maintenance-dailies/<daily_maintenance_id>/transition", methods=["POST"])
def transition_state(daily_maintenance_id: str):
    """通用状态流转"""
    try:
        data = request.get_json()
        if not data or "to_status" not in data:
            return make_response(False, error="to_status is required"), 400

        result = service.transition_state(
            daily_maintenance_id=daily_maintenance_id,
            to_status=data.get("to_status"),
            oper_cd=getattr(g, "user_cd", None),
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_daily_bp.route("/maintenance-dailies/<daily_maintenance_id>/cancel", methods=["POST"])
def cancel_daily(daily_maintenance_id: str):
    """取消保养单"""
    try:
        result = service.cancel_daily(
            daily_maintenance_id=daily_maintenance_id,
            oper_cd=getattr(g, "user_cd", None),
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_daily_bp.route("/maintenance-dailies/<daily_maintenance_id>/d2d-records", methods=["GET"])
def list_d2d_records(daily_maintenance_id: str):
    """获取上门服务记录列表（TIT23_MAINTENANCE_D2D，d2d_type='3'）"""
    try:
        result = _d2d_service.list_d2d_records(
            maintenance_id=daily_maintenance_id,
            d2d_type="3",
        )
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400
        return make_response(True, result)
    except Exception as e:
        return make_response(False, error=str(e)), 500


@maintenance_daily_bp.route("/maintenance-dailies/<daily_maintenance_id>/d2d-records", methods=["POST"])
def create_d2d_record(daily_maintenance_id: str):
    """新增上门服务记录（TIT23_MAINTENANCE_D2D，d2d_type='3'）"""
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
            maintenance_id=daily_maintenance_id,
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
            d2d_type="3",
            pos_status=data.get("pos_status"),
            pos_status1=data.get("pos_status1"),
        )
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result), 201
    except Exception as e:
        return make_response(False, error=str(e)), 500
