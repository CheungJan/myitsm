"""
IoT 数据监控 API（Tier-3 G8）。

路由前缀：/api/v1/iot
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.iot import (
    AlertAcknowledge,
    AlertRuleCreate,
    AlertRuleUpdate,
    DeviceConnCreate,
    DeviceConnUpdate,
    DeviceDataCreate,
)
from app.services.iot_service import (
    AlertLogService,
    AlertRuleService,
    DeviceConnService,
    DeviceDataService,
)
from app.utils.response import error_response, success_response

__all__ = ["iot_bp"]

iot_bp = Blueprint("iot", __name__)


# ---- 设备接入 ----


@iot_bp.get("/connections")
@login_required
def list_connections():  # type: ignore[no-untyped-def]
    """设备接入列表。"""
    online_status = request.args.get("online_status")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = DeviceConnService.list_all(online_status=online_status, page=page, per_page=per_page)
    return success_response(data=data)


@iot_bp.get("/connections/<conn_id>")
@login_required
def get_connection(conn_id: str):  # type: ignore[no-untyped-def]
    """设备接入详情。"""
    data = DeviceConnService.get(conn_id)
    if data is None:
        return error_response(message="接入记录不存在", code=404)
    return success_response(data=data)


@iot_bp.post("/connections")
@login_required
def create_connection():  # type: ignore[no-untyped-def]
    """创建设备接入。"""
    body = DeviceConnCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = DeviceConnService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@iot_bp.put("/connections/<conn_id>")
@login_required
def update_connection(conn_id: str):  # type: ignore[no-untyped-def]
    """更新设备接入。"""
    body = DeviceConnUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = DeviceConnService.update(conn_id, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="接入记录不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 设备数据 ----


@iot_bp.get("/data/<eid>")
@login_required
def list_device_data(eid: str):  # type: ignore[no-untyped-def]
    """设备数据查询。"""
    data_type = request.args.get("data_type")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "50"))
    data = DeviceDataService.list_by_eid(eid, data_type=data_type, page=page, per_page=per_page)
    return success_response(data=data)


@iot_bp.post("/data")
@login_required
def report_data():  # type: ignore[no-untyped-def]
    """上报设备数据。"""
    body = DeviceDataCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = DeviceDataService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="上报成功", code=201)


# ---- 报警规则 ----


@iot_bp.get("/alert-rules")
@login_required
def list_alert_rules():  # type: ignore[no-untyped-def]
    """报警规则列表。"""
    data = AlertRuleService.list_all()
    return success_response(data=data)


@iot_bp.post("/alert-rules")
@login_required
def create_alert_rule():  # type: ignore[no-untyped-def]
    """创建报警规则。"""
    body = AlertRuleCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = AlertRuleService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@iot_bp.put("/alert-rules/<rule_id>")
@login_required
def update_alert_rule(rule_id: str):  # type: ignore[no-untyped-def]
    """更新报警规则。"""
    body = AlertRuleUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = AlertRuleService.update(rule_id, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="规则不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 报警记录 ----


@iot_bp.get("/alerts")
@login_required
def list_alerts():  # type: ignore[no-untyped-def]
    """报警记录列表。"""
    eid = request.args.get("eid")
    status = request.args.get("status")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = AlertLogService.list_all(eid=eid, status=status, page=page, per_page=per_page)
    return success_response(data=data)


@iot_bp.put("/alerts/<int:log_id>/acknowledge")
@login_required
def acknowledge_alert(log_id: int):  # type: ignore[no-untyped-def]
    """确认/解决报警。"""
    body = AlertAcknowledge(**request.get_json(force=True))
    data = AlertLogService.acknowledge(log_id, body.model_dump(exclude_unset=True))
    if data is None:
        return error_response(message="报警记录不存在", code=404)
    return success_response(data=data, message="操作成功")
