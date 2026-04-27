"""
ITSM 核心业务 API。

路由前缀：/api/v1/itsm
单据类型：日常维护(MD)/新机开通(MO)/旧机翻新(MR)/设备变更(BG)/门店关闭(GB)
公用附表：上门服务(D2D)/回访(RV)/配件更新/关单/分派
"""

from __future__ import annotations

from flask import Blueprint, request

from app.api.auth import login_required
from app.schemas.itsm import (
    AccessoriesUpdateCreate,
    CloseBillCreate,
    D2DCreate,
    DeviceChangeCreate,
    DispatchCreate,
    MaintenanceDailyCreate,
    MaintenanceDailyUpdate,
    MaintenanceOpenCreate,
    MaintenanceQuery,
    MaintenanceRenovateCreate,
    RVCreate,
    StatusTransition,
    StoreCloseCreate,
)
from app.services.itsm_service import (
    AccessoriesUpdateService,
    CloseBillService,
    D2DService,
    DeviceChangeService,
    DispatchService,
    MaintenanceDailyService,
    MaintenanceOpenService,
    MaintenanceRenovateService,
    RVService,
    StoreCloseService,
)
from app.utils.response import error_response, success_response

__all__ = ["itsm_bp"]

itsm_bp = Blueprint("itsm", __name__)

_daily_svc = MaintenanceDailyService()
_open_svc = MaintenanceOpenService()
_renovate_svc = MaintenanceRenovateService()
_device_change_svc = DeviceChangeService()
_store_close_svc = StoreCloseService()


# ---- 日常维护单 (MD) ----


@itsm_bp.get("/maintenance-daily")
@login_required
def list_daily():  # type: ignore[no-untyped-def]
    """日常维护单列表。"""
    params = MaintenanceQuery.model_validate(request.args.to_dict())
    data = MaintenanceDailyService.list_records(
        status=params.status,
        store_id=params.store_id,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@itsm_bp.get("/maintenance-daily/<maintenance_id>")
@login_required
def get_daily(maintenance_id: str):  # type: ignore[no-untyped-def]
    """日常维护单详情。"""
    data = MaintenanceDailyService.get(maintenance_id)
    if data is None:
        return error_response(message="维护单不存在", code=404)
    return success_response(data=data)


@itsm_bp.post("/maintenance-daily")
@login_required
def create_daily():  # type: ignore[no-untyped-def]
    """创建日常维护单。"""
    body = MaintenanceDailyCreate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = MaintenanceDailyService.create(
        body.model_dump(exclude_none=True),
        creator=user_cd,
    )
    return success_response(data=data, code=201)


@itsm_bp.put("/maintenance-daily/<maintenance_id>")
@login_required
def update_daily(maintenance_id: str):  # type: ignore[no-untyped-def]
    """更新日常维护单。"""
    body = MaintenanceDailyUpdate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = MaintenanceDailyService.update(
        maintenance_id,
        body.model_dump(exclude_none=True),
        updator=user_cd,
    )
    if data is None:
        return error_response(message="维护单不存在", code=404)
    return success_response(data=data)


@itsm_bp.post("/maintenance-daily/<maintenance_id>/transition")
@login_required
def transition_daily(maintenance_id: str):  # type: ignore[no-untyped-def]
    """日常维护单状态流转。"""
    body = StatusTransition(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    result = _daily_svc.transition(
        maintenance_id,
        to_status=body.to_status,
        operator=user_cd,
        remark=body.remark,
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


# ---- 新机开通 (MO) ----


@itsm_bp.get("/maintenance-open")
@login_required
def list_open():  # type: ignore[no-untyped-def]
    """新机开通单列表。"""
    params = MaintenanceQuery.model_validate(request.args.to_dict())
    data = MaintenanceOpenService.list_records(
        status=params.status,
        store_id=params.store_id,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@itsm_bp.get("/maintenance-open/<opening_id>")
@login_required
def get_open(opening_id: str):  # type: ignore[no-untyped-def]
    """新机开通单详情。"""
    data = MaintenanceOpenService.get(opening_id)
    if data is None:
        return error_response(message="开通单不存在", code=404)
    return success_response(data=data)


@itsm_bp.post("/maintenance-open")
@login_required
def create_open():  # type: ignore[no-untyped-def]
    """创建新机开通单。"""
    body = MaintenanceOpenCreate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = MaintenanceOpenService.create(
        body.model_dump(exclude_none=True),
        creator=user_cd,
    )
    return success_response(data=data, code=201)


@itsm_bp.post("/maintenance-open/<opening_id>/transition")
@login_required
def transition_open(opening_id: str):  # type: ignore[no-untyped-def]
    """新机开通单状态流转。"""
    body = StatusTransition(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    result = _open_svc.transition(
        opening_id,
        to_status=body.to_status,
        operator=user_cd,
        remark=body.remark,
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


# ---- 旧机翻新 (MR) ----


@itsm_bp.get("/maintenance-renovate")
@login_required
def list_renovate():  # type: ignore[no-untyped-def]
    """旧机翻新单列表。"""
    params = MaintenanceQuery.model_validate(request.args.to_dict())
    data = MaintenanceRenovateService.list_records(
        status=params.status,
        store_id=params.store_id,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@itsm_bp.get("/maintenance-renovate/<renew_id>")
@login_required
def get_renovate(renew_id: str):  # type: ignore[no-untyped-def]
    """旧机翻新单详情。"""
    data = MaintenanceRenovateService.get(renew_id)
    if data is None:
        return error_response(message="翻新单不存在", code=404)
    return success_response(data=data)


@itsm_bp.post("/maintenance-renovate")
@login_required
def create_renovate():  # type: ignore[no-untyped-def]
    """创建旧机翻新单。"""
    body = MaintenanceRenovateCreate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = MaintenanceRenovateService.create(
        body.model_dump(exclude_none=True),
        creator=user_cd,
    )
    return success_response(data=data, code=201)


@itsm_bp.post("/maintenance-renovate/<renew_id>/transition")
@login_required
def transition_renovate(renew_id: str):  # type: ignore[no-untyped-def]
    """旧机翻新单状态流转。"""
    body = StatusTransition(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    result = _renovate_svc.transition(
        renew_id,
        to_status=body.to_status,
        operator=user_cd,
        remark=body.remark,
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


# ---- 设备变更 (BG) ----


@itsm_bp.get("/device-change")
@login_required
def list_device_change():  # type: ignore[no-untyped-def]
    """设备变更单列表。"""
    params = MaintenanceQuery.model_validate(request.args.to_dict())
    change_type = request.args.get("change_type")
    data = DeviceChangeService.list_records(
        status=params.status,
        store_id=params.store_id,
        change_type=change_type,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@itsm_bp.get("/device-change/<change_id>")
@login_required
def get_device_change(change_id: str):  # type: ignore[no-untyped-def]
    """设备变更单详情。"""
    data = DeviceChangeService.get(change_id)
    if data is None:
        return error_response(message="变更单不存在", code=404)
    return success_response(data=data)


@itsm_bp.post("/device-change")
@login_required
def create_device_change():  # type: ignore[no-untyped-def]
    """创建设备变更单。"""
    body = DeviceChangeCreate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = DeviceChangeService.create(
        body.model_dump(exclude_none=True),
        creator=user_cd,
    )
    return success_response(data=data, code=201)


@itsm_bp.post("/device-change/<change_id>/transition")
@login_required
def transition_device_change(change_id: str):  # type: ignore[no-untyped-def]
    """设备变更单状态流转。"""
    body = StatusTransition(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    result = _device_change_svc.transition(
        change_id,
        to_status=body.to_status,
        operator=user_cd,
        remark=body.remark,
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


# ---- 门店关闭 (GB) ----


@itsm_bp.get("/store-close")
@login_required
def list_store_close():  # type: ignore[no-untyped-def]
    """门店关闭单列表。"""
    params = MaintenanceQuery.model_validate(request.args.to_dict())
    data = StoreCloseService.list_records(
        status=params.status,
        store_id=params.store_id,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@itsm_bp.get("/store-close/<close_id>")
@login_required
def get_store_close(close_id: str):  # type: ignore[no-untyped-def]
    """门店关闭单详情。"""
    data = StoreCloseService.get(close_id)
    if data is None:
        return error_response(message="关闭单不存在", code=404)
    return success_response(data=data)


@itsm_bp.post("/store-close")
@login_required
def create_store_close():  # type: ignore[no-untyped-def]
    """创建门店关闭单。"""
    body = StoreCloseCreate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = StoreCloseService.create(
        body.model_dump(exclude_none=True),
        creator=user_cd,
    )
    return success_response(data=data, code=201)


@itsm_bp.post("/store-close/<close_id>/transition")
@login_required
def transition_store_close(close_id: str):  # type: ignore[no-untyped-def]
    """门店关闭单状态流转。"""
    body = StatusTransition(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    result = _store_close_svc.transition(
        close_id,
        to_status=body.to_status,
        operator=user_cd,
        remark=body.remark,
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


# ---- 公用附表 API ----


@itsm_bp.get("/d2d/<maintenance_id>")
@login_required
def list_d2d(maintenance_id: str):  # type: ignore[no-untyped-def]
    """查询上门服务记录。"""
    data = D2DService.list_by_maintenance_id(maintenance_id)
    return success_response(data=data)


@itsm_bp.post("/d2d")
@login_required
def create_d2d():  # type: ignore[no-untyped-def]
    """创建上门服务记录。"""
    body = D2DCreate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = D2DService.create(body.model_dump(exclude_none=True), creator=user_cd)
    return success_response(data=data, code=201)


@itsm_bp.get("/rv/<maintenance_id>")
@login_required
def list_rv(maintenance_id: str):  # type: ignore[no-untyped-def]
    """查询回访记录。"""
    data = RVService.list_by_maintenance_id(maintenance_id)
    return success_response(data=data)


@itsm_bp.post("/rv")
@login_required
def create_rv():  # type: ignore[no-untyped-def]
    """创建回访记录。"""
    body = RVCreate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = RVService.create(body.model_dump(exclude_none=True), creator=user_cd)
    return success_response(data=data, code=201)


@itsm_bp.get("/accessories/<maintenance_id>")
@login_required
def list_accessories(maintenance_id: str):  # type: ignore[no-untyped-def]
    """查询配件更新记录。"""
    data = AccessoriesUpdateService.list_by_maintenance_id(maintenance_id)
    return success_response(data=data)


@itsm_bp.post("/accessories")
@login_required
def create_accessories():  # type: ignore[no-untyped-def]
    """创建配件更新记录。"""
    body = AccessoriesUpdateCreate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = AccessoriesUpdateService.create(body.model_dump(exclude_none=True), creator=user_cd)
    return success_response(data=data, code=201)


@itsm_bp.get("/close-bill/<maintenance_id>")
@login_required
def list_close_bill(maintenance_id: str):  # type: ignore[no-untyped-def]
    """查询关单记录。"""
    data = CloseBillService.list_by_maintenance_id(maintenance_id)
    return success_response(data=data)


@itsm_bp.post("/close-bill")
@login_required
def create_close_bill():  # type: ignore[no-untyped-def]
    """创建关单记录。"""
    body = CloseBillCreate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = CloseBillService.create(body.model_dump(exclude_none=True), creator=user_cd)
    return success_response(data=data, code=201)


@itsm_bp.get("/dispatch/<maintenance_id>")
@login_required
def list_dispatch(maintenance_id: str):  # type: ignore[no-untyped-def]
    """查询分派记录。"""
    data = DispatchService.list_by_maintenance_id(maintenance_id)
    return success_response(data=data)


@itsm_bp.post("/dispatch")
@login_required
def create_dispatch():  # type: ignore[no-untyped-def]
    """创建分派记录。"""
    body = DispatchCreate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = DispatchService.create(body.model_dump(exclude_none=True), creator=user_cd)
    return success_response(data=data, code=201)
