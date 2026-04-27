"""
SLA 服务级别管理 API（Tier-1 扩展）。

路由前缀：/api/v1/sla
SLA 定义 + 工单监控 + 达标率统计。
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.sla import (
    SlaAttachRequest,
    SlaDefinitionCreate,
    SlaDefinitionUpdate,
    SlaResponseRequest,
    SlaTicketQuery,
)
from app.services.sla_service import (
    SlaDefinitionService,
    SlaTicketService,
)
from app.utils.response import error_response, success_response

__all__ = ["sla_bp"]

sla_bp = Blueprint("sla", __name__)


# ---- SLA 定义 ----


@sla_bp.get("/definitions")
@login_required
def list_definitions():  # type: ignore[no-untyped-def]
    """SLA定义列表。"""
    data = SlaDefinitionService.list_all()
    return success_response(data=data)


@sla_bp.get("/definitions/<sla_id>")
@login_required
def get_definition(sla_id: str):  # type: ignore[no-untyped-def]
    """SLA定义详情。"""
    data = SlaDefinitionService.get(sla_id)
    if data is None:
        return error_response(message="SLA定义不存在", code=404)
    return success_response(data=data)


@sla_bp.post("/definitions")
@login_required
def create_definition():  # type: ignore[no-untyped-def]
    """创建SLA定义。"""
    body = SlaDefinitionCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    data = SlaDefinitionService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@sla_bp.put("/definitions/<sla_id>")
@login_required
def update_definition(sla_id: str):  # type: ignore[no-untyped-def]
    """更新SLA定义。"""
    body = SlaDefinitionUpdate.model_validate(request.get_json(silent=True) or {})
    data = SlaDefinitionService.update(sla_id, body.model_dump(exclude_unset=True))
    if data is None:
        return error_response(message="SLA定义不存在", code=404)
    return success_response(data=data)


# ---- SLA 工单监控 ----


@sla_bp.get("/tickets")
@login_required
def list_tickets():  # type: ignore[no-untyped-def]
    """SLA工单监控列表。"""
    params = SlaTicketQuery.model_validate(request.args.to_dict())
    data = SlaTicketService.list_records(
        sla_status=params.sla_status,
        sla_id=params.sla_id,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@sla_bp.post("/tickets/attach")
@login_required
def attach_sla():  # type: ignore[no-untyped-def]
    """为工单绑定SLA。"""
    body = SlaAttachRequest.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    result = SlaTicketService.attach_sla(
        maintenance_id=body.maintenance_id,
        maintenance_type=body.maintenance_type,
        priority=body.priority,
        creator=user_cd,
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result, message="绑定成功", code=201)


@sla_bp.post("/tickets/response")
@login_required
def record_response():  # type: ignore[no-untyped-def]
    """记录首次响应。"""
    body = SlaResponseRequest.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    result = SlaTicketService.record_response(
        maintenance_id=body.maintenance_id,
        maintenance_type=body.maintenance_type,
        operator=user_cd,
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


@sla_bp.post("/tickets/resolve")
@login_required
def record_resolution():  # type: ignore[no-untyped-def]
    """记录解决并关闭SLA监控。"""
    body = SlaResponseRequest.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    result = SlaTicketService.record_resolution(
        maintenance_id=body.maintenance_id,
        maintenance_type=body.maintenance_type,
        operator=user_cd,
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


# ---- 达标率统计 ----


@sla_bp.get("/stats")
@login_required
def compliance_stats():  # type: ignore[no-untyped-def]
    """SLA达标率统计。"""
    sla_id = request.args.get("sla_id")
    data = SlaTicketService.get_compliance_stats(sla_id=sla_id)
    return success_response(data=data)
