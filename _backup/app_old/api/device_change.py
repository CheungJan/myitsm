# -*- coding: utf-8 -*-
"""
设备变更单API
文件说明：提供设备变更单管理端点，包含磁卡号变更历史查询优化
作者：Cascade
创建时间：2026-04-08

端点列表：
- GET /api/v1/device-changes：变更单列表
- GET /api/v1/device-changes/<id>：变更单详情
- GET /api/v1/device-changes/<id>/transitions：允许的状态流转
- POST /api/v1/device-changes：创建变更单
- POST /api/v1/device-changes/<id>/transition：通用状态流转
- POST /api/v1/device-changes/<id>/complete：完成变更单（执行变更逻辑）
- POST /api/v1/device-changes/<id>/cancel：取消变更单
- GET /api/v1/device-changes/history/store/<store_id>：门店变更历史
- GET /api/v1/device-changes/history/card/<custcard>：磁卡号变更历史（核心优化功能）
"""

from flask import Blueprint, request, g
from typing import Dict, Any

from app.services.device_change_service import DeviceChangeService
from app.services.state_machine import MaintenanceState

# 创建蓝图
device_change_bp = Blueprint("device_change", __name__)

# 服务实例
service = DeviceChangeService()


def make_response(success: bool, data: Dict[str, Any] = None, error: str = None) -> Dict[str, Any]:
    """统一响应格式"""
    resp = {"success": success, "request_id": getattr(g, "request_id", None)}
    if data:
        resp["data"] = data
    if error:
        resp["error"] = error
    return resp


@device_change_bp.route("/device-changes", methods=["GET"])
def list_device_changes():
    """
    获取设备变更单列表
    
    Query参数：
    - store_id: 门店ID过滤
    - change_type: 变更类型过滤（CK/BQ/BG）
    - status: 状态过滤
    - page: 页码（默认1）
    - page_size: 每页数量（默认20）
    """
    try:
        store_id = request.args.get("store_id")
        custcard = request.args.get("custcard")
        begin_date = request.args.get("begin_date")
        end_date = request.args.get("end_date")
        device_change_id = request.args.get("device_change_id")
        new_store_card = request.args.get("new_store_card")
        new_tel = request.args.get("new_tel")
        change_type = request.args.get("change_type")
        status = request.args.get("status")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))

        result = service.list_device_changes(
            store_id=store_id,
            custcard=custcard,
            begin_date=begin_date,
            end_date=end_date,
            device_change_id=device_change_id,
            new_store_card=new_store_card,
            new_tel=new_tel,
            change_type=change_type,
            status=status,
            page=page,
            page_size=page_size,
        )

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@device_change_bp.route("/device-changes/<device_change_id>", methods=["GET"])
def get_device_change(device_change_id: str):
    """
    获取设备变更单详情
    
    Args:
        device_change_id: 变更单ID
    """
    try:
        result = service.get_device_change(device_change_id)
        if not result:
            return make_response(False, error="Device change not found"), 404

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@device_change_bp.route("/device-changes/<device_change_id>/transitions", methods=["GET"])
def get_allowed_transitions(device_change_id: str):
    """
    获取允许的状态流转
    
    Args:
        device_change_id: 变更单ID
    """
    try:
        result = service.get_allowed_transitions(device_change_id)
        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@device_change_bp.route("/device-changes", methods=["POST"])
def create_device_change():
    """
    创建设备变更单
    
    Body参数：
    - device_change_id: 变更单ID（必填）
    - store_id: 门店ID（必填）
    - change_type: 变更类型（必填，CK/BQ/BG）
    - device_id: 整机ID（可选）
    - new_contactor: 变更后联系人（BQ类型必填）
    - new_tel: 变更后电话（BQ类型必填）
    - new_address: 变更后地址（BQ类型必填）
    - new_store_card: 变更后磁卡号（CK类型必填）
    - new_store_id: 变更后门店ID（BG类型必填）
    - is_store_inside_change: 是否店内移机（可选，默认N）
    - remark: 备注（可选）
    """
    try:
        data = request.get_json()
        if not data:
            return make_response(False, error="Request body required"), 400

        # 必填字段校验
        required_fields = ["device_change_id", "store_id", "change_type"]
        for field in required_fields:
            if field not in data:
                return make_response(False, error=f"Missing required field: {field}"), 400

        # 根据类型校验必填字段
        change_type = data.get("change_type")
        if change_type == "CK" and not data.get("new_store_card"):
            return make_response(False, error="new_store_card is required for CK type"), 400
        if change_type == "BQ" and not data.get("new_contactor"):
            return make_response(False, error="new_contactor is required for BQ type"), 400
        if change_type == "BG" and not data.get("new_store_id"):
            return make_response(False, error="new_store_id is required for BG type"), 400

        result = service.create_device_change(
            device_change_id=data.get("device_change_id"),
            store_id=data.get("store_id"),
            change_type=change_type,
            device_id=data.get("device_id"),
            new_contactor=data.get("new_contactor"),
            new_tel=data.get("new_tel"),
            new_address=data.get("new_address"),
            new_store_card=data.get("new_store_card"),
            new_store_id=data.get("new_store_id"),
            is_store_inside_change=data.get("is_store_inside_change", "N"),
            oper_cd=getattr(g, "user_cd", None),
            remark=data.get("remark"),
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result), 201

    except Exception as e:
        return make_response(False, error=str(e)), 500


@device_change_bp.route("/device-changes/<device_change_id>/transition", methods=["POST"])
def transition_state(device_change_id: str):
    """
    通用状态流转
    
    Body参数：
    - to_status: 目标状态（必填）
    """
    try:
        data = request.get_json()
        if not data or "to_status" not in data:
            return make_response(False, error="to_status is required"), 400

        to_status = data.get("to_status")

        # 如果是流转到COMPLETED，调用complete_change
        if to_status == MaintenanceState.COMPLETED.value:
            result = service.complete_change(
                device_change_id=device_change_id,
                oper_cd=getattr(g, "user_cd", None),
            )
        else:
            result = service.transition_state(
                device_change_id=device_change_id,
                to_status=to_status,
                oper_cd=getattr(g, "user_cd", None),
            )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@device_change_bp.route("/device-changes/<device_change_id>/complete", methods=["POST"])
def complete_change(device_change_id: str):
    """
    完成设备变更单
    
    执行实际的变更逻辑：
    - CK类型：执行磁卡号变更（保存历史+更新主表）
    - BQ类型：更新门店信息
    - BG类型：执行设备迁移
    """
    try:
        result = service.complete_change(
            device_change_id=device_change_id,
            oper_cd=getattr(g, "user_cd", None),
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@device_change_bp.route("/device-changes/<device_change_id>/cancel", methods=["POST"])
def cancel_change(device_change_id: str):
    """
    取消设备变更单
    """
    try:
        result = service.cancel_change(
            device_change_id=device_change_id,
            oper_cd=getattr(g, "user_cd", None),
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@device_change_bp.route("/device-changes/history/store/<store_id>", methods=["GET"])
def get_store_change_history(store_id: str):
    """
    获取门店变更历史
    
    Args:
        store_id: 门店ID
        
    Query参数：
    - change_type: 变更类型过滤（CK/BQ/BG/INIT）
    - page: 页码（默认1）
    - page_size: 每页数量（默认20）
    """
    try:
        change_type = request.args.get("change_type")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))

        result = service.get_store_change_history(
            store_id=store_id,
            change_type=change_type,
            page=page,
            page_size=page_size,
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500


@device_change_bp.route("/device-changes/history/card/<custcard>", methods=["GET"])
def get_card_change_history(custcard: str):
    """
    根据磁卡号查询变更历史（核心优化功能）
    
    支持查询：
    - 当前磁卡号的变更历史
    - 已变更的旧磁卡号历史
    
    Args:
        custcard: 磁卡号
        
    Query参数：
    - page: 页码（默认1）
    - page_size: 每页数量（默认20）
    """
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))

        result = service.get_card_change_history(
            custcard=custcard,
            page=page,
            page_size=page_size,
        )

        if not result["success"]:
            return make_response(False, error=result.get("error")), 400

        return make_response(True, result)

    except Exception as e:
        return make_response(False, error=str(e)), 500
