"""
ITSM 核心业务 API。

路由前缀：/api/v1/itsm
单据类型：日常维护(MD)/新机开通(MO)/旧机翻新(MR)/设备变更(BG)/门店关闭(GB)
公用附表：上门服务(D2D)/回访(RV)/配件更新/关单/分派
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.itsm import (
    AccessoriesUpdateCreate,
    ArchiveCreate,
    ArchiveUpdate,
    CloseBillCreate,
    D2DCreate,
    DeviceChangeCreate,
    DeviceChangeUpdate,
    DispatchCreate,
    LiabilityRegCreate,
    LiabilityRegDetailCreate,
    MaintenanceAttcCreate,
    MaintenanceDailyCreate,
    MaintenanceDailyUpdate,
    MaintenanceLiabilityCreate,
    MaintenanceLiabilityUpdate,
    MaintenanceOpenCreate,
    MaintenanceOpenUpdate,
    MaintenancePlanCreate,
    MaintenancePlanUpdate,
    MaintenanceQuery,
    MaintenanceRenovateCreate,
    MaintenanceRenovateUpdate,
    NoCloseTrackCreate,
    OnChooseDtCreate,
    PayListCreate,
    PosDetailCreate,
    RecycleTaskCreate,
    RecycleTaskDtlCreate,
    RecycleTaskQuery,
    RecycleTaskUpdate,
    RepairInfoCreate,
    RVCreate,
    StatusTransition,
    StoreCloseCreate,
    StoreCloseUpdate,
    TimepointAreaCreate,
    TimepointAreaUpdate,
)
from app.services.archive_service import ArchiveService
from app.services.itsm_service import (
    AccessoriesUpdateService,
    ChargeService,
    CloseBillService,
    D2DService,
    DeviceChangeService,
    DispatchService,
    LiabilityRegService,
    MaintenanceAttcService,
    MaintenanceDailyService,
    MaintenanceDailyTrackService,
    MaintenanceLiabilityService,
    MaintenanceOpenService,
    MaintenancePlanService,
    MaintenanceRenovateService,
    MaintenanceT17Service,
    NoCloseTrackService,
    OnChooseDtService,
    PayListService,
    PosDetailService,
    RecycleTaskService,
    RepairInfoService,
    RVService,
    StoreCloseService,
    TimepointAreaService,
)
from app.utils.response import error_response, success_response

__all__ = ["itsm_bp"]

itsm_bp = Blueprint("itsm", __name__)

_daily_svc = MaintenanceDailyService()
_open_svc = MaintenanceOpenService()
_renovate_svc = MaintenanceRenovateService()
_device_change_svc = DeviceChangeService()
_recycle_svc = RecycleTaskService()
_store_close_svc = StoreCloseService()
_t17_svc = MaintenanceT17Service()


# ---- 日常维护单 (MD) ----


@itsm_bp.get("/maintenance-daily")
@login_required
def list_daily():  # type: ignore[no-untyped-def]
    """日常维护单列表（对齐 PB u_itsm_rep_maintenanceday 报表查询条件）。"""
    params = MaintenanceQuery.model_validate(request.args.to_dict())
    data = MaintenanceDailyService.list_records(
        status=params.status,
        current_status=params.current_status,
        store_id=params.store_id,
        maintenance_id=params.maintenance_id,
        company_id=params.company_id,
        area_cd=params.area_cd,
        firstor=params.firstor,
        cust_card=params.cust_card,
        cust_nm=params.cust_nm,
        address=params.address,
        fault_type=params.fault_type,
        short_description=params.short_description,
        request_begin=params.request_begin,
        request_end=params.request_end,
        first_begin=params.first_begin,
        first_end=params.first_end,
        dispatch_to=params.dispatch_to,
        area_user=params.area_user,
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


@itsm_bp.put("/maintenance-open/<opening_id>")
@login_required
def update_open(opening_id: str):  # type: ignore[no-untyped-def]
    """更新新机开通单。"""
    body = MaintenanceOpenUpdate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = MaintenanceOpenService.update(opening_id, body.model_dump(exclude_none=True), updator=user_cd)
    if data is None:
        return error_response(message="开通单不存在", code=404)
    return success_response(data=data)


# ---- TIT14 新机开通设备明细 ----
@itsm_bp.post("/maintenance-open/<opening_id>/equipments")
@login_required
def add_open_equipment(opening_id: str):  # type: ignore[no-untyped-def]
    """添加开通设备明细。"""
    body = request.get_json(force=True)
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = MaintenanceOpenService.add_equipment(opening_id, body, creator=user_cd)
    return success_response(data=data, code=201)


@itsm_bp.delete("/maintenance-open/<opening_id>/equipments/<int:eq_id>")
@login_required
def delete_open_equipment(opening_id: str, eq_id: int):  # type: ignore[no-untyped-def]
    """删除开通设备明细。"""
    ok = MaintenanceOpenService.delete_equipment(opening_id, eq_id)
    if not ok:
        return error_response(message="明细不存在", code=404)
    return success_response(message="已删除")


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


@itsm_bp.put("/maintenance-renovate/<renew_id>")
@login_required
def update_renovate(renew_id: str):  # type: ignore[no-untyped-def]
    """更新旧机翻新单。"""
    body = MaintenanceRenovateUpdate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = MaintenanceRenovateService.update(renew_id, body.model_dump(exclude_none=True), updator=user_cd)
    if data is None:
        return error_response(message="翻新单不存在", code=404)
    return success_response(data=data)


# ---- TIT15 翻新设备明细 ----
@itsm_bp.get("/maintenance-renovate/<renew_id>/equipments")
@login_required
def list_renovate_equipments(renew_id: str):  # type: ignore[no-untyped-def]
    """翻新设备明细列表。"""
    data = MaintenanceRenovateService.list_equipments(renew_id)
    return success_response(data=data)


@itsm_bp.post("/maintenance-renovate/<renew_id>/equipments")
@login_required
def add_renovate_equipment(renew_id: str):  # type: ignore[no-untyped-def]
    """添加翻新设备明细。"""
    body = request.get_json(force=True)
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = MaintenanceRenovateService.add_equipment(renew_id, body, creator=user_cd)
    return success_response(data=data, code=201)


@itsm_bp.delete("/maintenance-renovate/<renew_id>/equipments/<int:eq_id>")
@login_required
def delete_renovate_equipment(renew_id: str, eq_id: int):  # type: ignore[no-untyped-def]
    """删除翻新设备明细。"""
    ok = MaintenanceRenovateService.delete_equipment(renew_id, eq_id)
    if not ok:
        return error_response(message="明细不存在", code=404)
    return success_response(message="已删除")


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


@itsm_bp.put("/device-change/<change_id>")
@login_required
def update_device_change(change_id: str):  # type: ignore[no-untyped-def]
    """更新磁卡号变更单。"""
    body = DeviceChangeUpdate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = DeviceChangeService.update(change_id, body.model_dump(exclude_none=True), updator=user_cd)
    if data is None:
        return error_response(message="变更单不存在", code=404)
    return success_response(data=data)


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


@itsm_bp.put("/store-close/<close_id>")
@login_required
def update_store_close(close_id: str):  # type: ignore[no-untyped-def]
    """更新门店关闭单。"""
    body = StoreCloseUpdate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = StoreCloseService.update(close_id, body.model_dump(exclude_none=True), updator=user_cd)
    if data is None:
        return error_response(message="关闭单不存在", code=404)
    return success_response(data=data)


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


@itsm_bp.put("/d2d/<int:record_id>")
@login_required
def update_d2d(record_id: int):  # type: ignore[no-untyped-def]
    """更新上门服务记录。"""
    body = request.get_json(force=True)
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = D2DService.update(record_id, body, updator=user_cd)
    if data is None:
        return error_response(message="记录不存在", code=404)
    return success_response(data=data)


@itsm_bp.put("/rv/<int:record_id>")
@login_required
def update_rv(record_id: int):  # type: ignore[no-untyped-def]
    """更新回访记录。"""
    body = request.get_json(force=True)
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = RVService.update(record_id, body, updator=user_cd)
    if data is None:
        return error_response(message="记录不存在", code=404)
    return success_response(data=data)


@itsm_bp.put("/accessories/<int:record_id>")
@login_required
def update_accessories(record_id: int):  # type: ignore[no-untyped-def]
    """更新配件更新记录。"""
    body = request.get_json(force=True)
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = AccessoriesUpdateService.update(record_id, body, updator=user_cd)
    if data is None:
        return error_response(message="记录不存在", code=404)
    return success_response(data=data)


@itsm_bp.put("/dispatch/<int:record_id>")
@login_required
def update_dispatch(record_id: int):  # type: ignore[no-untyped-def]
    """更新分派记录。"""
    body = request.get_json(force=True)
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = DispatchService.update(record_id, body, updator=user_cd)
    if data is None:
        return error_response(message="记录不存在", code=404)
    return success_response(data=data)


@itsm_bp.put("/close-bill/<int:record_id>")
@login_required
def update_close_bill(record_id: int):  # type: ignore[no-untyped-def]
    """更新关单记录。"""
    body = request.get_json(force=True)
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = CloseBillService.update(record_id, body, updator=user_cd)
    if data is None:
        return error_response(message="记录不存在", code=404)
    return success_response(data=data)


@itsm_bp.put("/paylist/<int:record_id>")
@login_required
def update_paylist(record_id: int):  # type: ignore[no-untyped-def]
    """更新收费记录。"""
    body = request.get_json(force=True)
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = PayListService.update(record_id, body, updator=user_cd)
    if data is None:
        return error_response(message="记录不存在", code=404)
    db.session.commit()
    return success_response(data=data)


# ---- 回收任务 (TIT20，P0-1/优化4.2) ----


@itsm_bp.get("/recycle-task")
@login_required
def list_recycle_task():  # type: ignore[no-untyped-def]
    """回收任务列表。"""
    params = RecycleTaskQuery.model_validate(request.args.to_dict())
    data = RecycleTaskService.list_records(
        task_status=params.task_status,
        cust_cd=params.cust_cd,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@itsm_bp.get("/recycle-task/<recycle_id>")
@login_required
def get_recycle_task(recycle_id: str):  # type: ignore[no-untyped-def]
    """回收任务详情。"""
    data = RecycleTaskService.get(recycle_id)
    if data is None:
        return error_response(message="回收任务不存在", code=404)
    return success_response(data=data)


@itsm_bp.post("/recycle-task")
@login_required
def create_recycle_task():  # type: ignore[no-untyped-def]
    """创建回收任务。"""
    body = RecycleTaskCreate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = RecycleTaskService.create(body.model_dump(exclude_none=True), creator=user_cd)
    return success_response(data=data, code=201)


@itsm_bp.post("/recycle-task/<recycle_id>/transition")
@login_required
def transition_recycle_task(recycle_id: str):  # type: ignore[no-untyped-def]
    """回收任务状态流转。"""
    body = StatusTransition(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    result = _recycle_svc.transition(
        recycle_id, body.to_status, operator=user_cd, remark=body.remark
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


@itsm_bp.get("/recycle-task/<recycle_id>/details")
@login_required
def list_recycle_details(recycle_id: str):  # type: ignore[no-untyped-def]
    """回收任务明细列表。"""
    data = RecycleTaskService.list_details(recycle_id)
    return success_response(data=data)


@itsm_bp.post("/recycle-task/<recycle_id>/details")
@login_required
def add_recycle_detail(recycle_id: str):  # type: ignore[no-untyped-def]
    """添加回收任务明细。"""
    body = RecycleTaskDtlCreate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    _ = user_cd
    data = RecycleTaskService.add_detail(recycle_id, body.model_dump(exclude_none=True))
    return success_response(data=data, code=201)


@itsm_bp.put("/recycle-task/<recycle_id>")
@login_required
def update_recycle_task(recycle_id: str):  # type: ignore[no-untyped-def]
    """更新回收任务单。"""
    body = RecycleTaskUpdate(**request.get_json(force=True))
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = RecycleTaskService.update(recycle_id, body.model_dump(exclude_none=True), updator=user_cd)
    if data is None:
        return error_response(message="回收任务不存在", code=404)
    return success_response(data=data)


@itsm_bp.delete("/recycle-task/<recycle_id>/details/<asset_id>")
@login_required
def delete_recycle_detail(recycle_id: str, asset_id: str):  # type: ignore[no-untyped-def]
    """删除回收任务明细。"""
    ok = RecycleTaskService.delete_detail(recycle_id, asset_id)
    if not ok:
        return error_response(message="明细不存在", code=404)
    db.session.commit()
    return success_response(message="已删除")


# ---- 保养计划 (TIT17_PLAN) ----


@itsm_bp.get("/maintenance-plans")
@login_required
def list_maintenance_plans():  # type: ignore[no-untyped-def]
    """保养计划列表。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    data = MaintenancePlanService.list_records(page=page, per_page=per_page)
    return success_response(data=data)


@itsm_bp.get("/maintenance-plans/<int:plan_id>")
@login_required
def get_maintenance_plan(plan_id: int):  # type: ignore[no-untyped-def]
    """保养计划详情。"""
    data = MaintenancePlanService.get(plan_id)
    if data is None:
        return error_response(message="保养计划不存在", code=404)
    return success_response(data=data)


@itsm_bp.post("/maintenance-plans")
@login_required
def create_maintenance_plan():  # type: ignore[no-untyped-def]
    """创建保养计划。"""
    body = MaintenancePlanCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = MaintenancePlanService.create(body.model_dump(exclude_none=True), creator=user_cd)
    return success_response(data=data, message="创建成功", code=201)


@itsm_bp.put("/maintenance-plans/<int:plan_id>")
@login_required
def update_maintenance_plan(plan_id: int):  # type: ignore[no-untyped-def]
    """更新保养计划。"""
    body = MaintenancePlanUpdate.model_validate(request.get_json(silent=True) or {})
    data = MaintenancePlanService.update(plan_id, body.model_dump(exclude_unset=True))
    if data is None:
        return error_response(message="保养计划不存在", code=404)
    return success_response(data=data)


# ---- 日常保养工单 (TIT17_MAINTENANCE) ----


@itsm_bp.get("/maintenance")
@login_required
def list_t17_maintenance():  # type: ignore[no-untyped-def]
    """日常保养工单列表。"""
    params = MaintenanceQuery.model_validate(request.args.to_dict())
    data = MaintenanceT17Service.list_records(
        status=params.status,
        store_id=params.store_id,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@itsm_bp.get("/maintenance/<maintenance_id>")
@login_required
def get_t17_maintenance(maintenance_id: str):  # type: ignore[no-untyped-def]
    """日常保养工单详情。"""
    data = MaintenanceT17Service.get(maintenance_id)
    if data is None:
        return error_response(message="保养工单不存在", code=404)
    return success_response(data=data)


@itsm_bp.post("/maintenance/<maintenance_id>/transition")
@login_required
def transition_t17_maintenance(maintenance_id: str):  # type: ignore[no-untyped-def]
    """日常保养工单状态流转。"""
    body = StatusTransition(**request.get_json(force=True))
    user_cd: str = g.current_user
    result = _t17_svc.transition(
        maintenance_id,
        to_status=body.to_status,
        operator=user_cd,
        remark=body.remark,
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


# ---- ITSM 统计报表 ----


@itsm_bp.get("/stats/daily")
@login_required
def itsm_daily_stats():  # type: ignore[no-untyped-def]
    """日常维护日报：按状态统计数量。"""
    from sqlalchemy import func

    from app.extensions import db as _db
    from app.models.itsm import MaintenanceDaily
    rows = (
        _db.session.query(
            MaintenanceDaily.current_status,
            func.count(MaintenanceDaily.maintenance_id).label("cnt"),
        )
        .group_by(MaintenanceDaily.current_status)
        .all()
    )
    return success_response(data=[{"status": r[0], "count": r[1]} for r in rows])


@itsm_bp.get("/stats/no-close")
@login_required
def itsm_no_close_stats():  # type: ignore[no-untyped-def]
    """未关单统计：各类型工单未关闭数量。"""
    from sqlalchemy import func

    from app.extensions import db as _db
    from app.models.itsm import (
        DeviceChange,
        Maintenance,
        MaintenanceDaily,
        MaintenanceOpen,
        MaintenanceRenovate,
        StoreClose,
    )

    def _count_open(model, pk_attr):
        return _db.session.query(func.count(getattr(model, pk_attr))).filter(
            model.current_status.notin_(["3", "9", "5"])
        ).scalar() or 0

    data = {
        "maintenance_daily": _count_open(MaintenanceDaily, "maintenance_id"),
        "maintenance_open": _count_open(MaintenanceOpen, "new_opening_id"),
        "maintenance_renovate": _count_open(MaintenanceRenovate, "renew_id"),
        "device_change": _count_open(DeviceChange, "device_change_id"),
        "store_close": _count_open(StoreClose, "store_close_id"),
                "maintenance_t17": _count_open(Maintenance, "daily_maintenance_id"),
    }
    data["total"] = sum(data.values())
    return success_response(data=data)


@itsm_bp.get("/stats/completion")
@login_required
def itsm_completion_stats():  # type: ignore[no-untyped-def]
    """工单完成率统计。"""
    from sqlalchemy import func

    from app.extensions import db as _db
    from app.models.itsm import MaintenanceDaily
    total = _db.session.query(func.count(MaintenanceDaily.maintenance_id)).scalar() or 0
    closed = (
        _db.session.query(func.count(MaintenanceDaily.maintenance_id))
        .filter(MaintenanceDaily.current_status.in_(["3", "5"]))
        .scalar()
    ) or 0
    return success_response(data={
        "total": total,
        "closed": closed,
        "completion_rate": round(closed / total * 100, 1) if total > 0 else 0,
    })


@itsm_bp.get("/stats/customer-summary")
@login_required
def itsm_customer_summary():  # type: ignore[no-untyped-def]
    """客户工单汇总：按门店统计工单数量。"""
    from sqlalchemy import func

    from app.extensions import db as _db
    from app.models.itsm import MaintenanceDaily
    rows = (
        _db.session.query(
            MaintenanceDaily.store_id,
            func.count(MaintenanceDaily.maintenance_id).label("cnt"),
        )
        .group_by(MaintenanceDaily.store_id)
        .order_by(func.count(MaintenanceDaily.maintenance_id).desc())
        .limit(50)
        .all()
    )
    return success_response(data=[{"store_id": r[0], "count": r[1]} for r in rows])


@itsm_bp.get("/stats/archive")
@login_required
def itsm_archive_stats():  # type: ignore[no-untyped-def]
    """归档统计：按归档编码统计数量。"""
    from sqlalchemy import func

    from app.extensions import db as _db
    from app.models.itsm import MaintenanceArchive
    rows = (
        _db.session.query(
            MaintenanceArchive.fault_cd,
            func.count(MaintenanceArchive.id).label("cnt"),
        )
        .group_by(MaintenanceArchive.fault_cd)
        .order_by(func.count(MaintenanceArchive.id).desc())
        .limit(50)
        .all()
    )
    return success_response(data=[{"fault_cd": r[0] or "未分类", "count": r[1]} for r in rows])


@itsm_bp.get("/stats/engineer")
@login_required
def itsm_engineer_stats():  # type: ignore[no-untyped-def]
    """工程师工作量统计。"""
    from sqlalchemy import func

    from app.extensions import db as _db
    from app.models.itsm import MaintenanceD2D
    rows = (
        _db.session.query(
            MaintenanceD2D.d2d_engineer,
            func.count(MaintenanceD2D.id).label("cnt"),
        )
        .group_by(MaintenanceD2D.d2d_engineer)
        .order_by(func.count(MaintenanceD2D.id).desc())
        .limit(50)
        .all()
    )
    return success_response(data=[{"engineer": r[0] or "未分配", "count": r[1]} for r in rows])


# ---- 归档 (TIT12) ----


@itsm_bp.get("/archives/<maintenance_id>")
@login_required
def list_archives(maintenance_id: str):  # type: ignore[no-untyped-def]
    """获取指定维护单的归档记录列表（含维护单基本信息）。"""
    data = ArchiveService.list_by_maintenance(maintenance_id)
    if data is None:
        return error_response(message="维护单不存在", code=404)
    return success_response(data=data)


@itsm_bp.post("/archives")
@login_required
def create_archive():  # type: ignore[no-untyped-def]
    """创建归档记录。"""
    body = request.get_json(silent=True) or {}
    try:
        req = ArchiveCreate(**body)
    except Exception as e:
        return error_response(str(e), 400)
    return success_response(data=ArchiveService.create_archive(req.model_dump()), code=201)


@itsm_bp.put("/archives/<int:archive_id>")
@login_required
def update_archive(archive_id: int):  # type: ignore[no-untyped-def]
    """更新归档记录。"""
    body = request.get_json(silent=True) or {}
    try:
        req = ArchiveUpdate(**body)
    except Exception as e:
        return error_response(str(e), 400)
    data = ArchiveService.update_archive(archive_id, req.model_dump(exclude_none=True))
    if data is None:
        return error_response(message="归档记录不存在", code=404)
    return success_response(data=data)


@itsm_bp.delete("/archives/<int:archive_id>")
@login_required
def delete_archive(archive_id: int):  # type: ignore[no-untyped-def]
    """删除归档记录。"""
    if not ArchiveService.delete_archive(archive_id):
        return error_response(message="归档记录不存在", code=404)
    return success_response(message="已删除")


# ---- POS 状态字典 (TMM52) ----


@itsm_bp.get("/pos-status")
@login_required
def list_pos_status():  # type: ignore[no-untyped-def]
    """POS 状态字典列表。"""
    from app.extensions import db as _db
    from app.models.itsm import PosStatus
    items = _db.session.query(PosStatus).filter(PosStatus.useflg == "1").order_by(PosStatus.id).all()
    return success_response(data=[{
        "id": i.id, "codecd": i.codecd, "codecd1": i.codecd1,
        "memo": i.memo, "sysflg": i.sysflg
    } for i in items])


# ---- P1 附表 API ----


# -- 收费记录 (TIT26) --

@itsm_bp.get("/paylist/<maintenance_id>")
@login_required
def list_paylist(maintenance_id: str):  # type: ignore[no-untyped-def]
    data = PayListService.list_by_maintenance_id(maintenance_id)
    return success_response(data=data)


@itsm_bp.post("/paylist")
@login_required
def create_paylist():  # type: ignore[no-untyped-def]
    body = PayListCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    data = PayListService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


# -- 维护单责任豁免 (TIT10_LIABILITY) --

@itsm_bp.get("/liability/<maintenance_id>")
@login_required
def list_liability(maintenance_id: str):  # type: ignore[no-untyped-def]
    data = MaintenanceLiabilityService.list_by_maintenance_id(maintenance_id)
    return success_response(data=data)


@itsm_bp.post("/liability")
@login_required
def create_liability():  # type: ignore[no-untyped-def]
    body = MaintenanceLiabilityCreate.model_validate(request.get_json(silent=True) or {})
    data = MaintenanceLiabilityService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


@itsm_bp.put("/liability/<int:record_id>")
@login_required
def update_liability(record_id: int):  # type: ignore[no-untyped-def]
    body = MaintenanceLiabilityUpdate.model_validate(request.get_json(silent=True) or {})
    data = MaintenanceLiabilityService.update(record_id, body.model_dump(exclude_none=True))
    if data is None:
        return error_response(message="记录不存在", code=404)
    return success_response(data=data)


# -- 责任豁免字典 (TIT02) --

@itsm_bp.get("/liability-regs")
@login_required
def list_liability_regs():  # type: ignore[no-untyped-def]
    data = LiabilityRegService.list_all()
    return success_response(data=data)


@itsm_bp.get("/liability-regs/<liab_cd>")
@login_required
def get_liability_reg(liab_cd: str):  # type: ignore[no-untyped-def]
    data = LiabilityRegService.get(liab_cd)
    if data is None:
        return error_response(message="不存在", code=404)
    return success_response(data=data)


@itsm_bp.post("/liability-regs")
@login_required
def create_liability_reg():  # type: ignore[no-untyped-def]
    json_data = request.get_json(silent=True) or {}
    body = LiabilityRegCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    details = [LiabilityRegDetailCreate.model_validate(d).model_dump() for d in raw_details]
    data = LiabilityRegService.create(body.model_dump(exclude_none=True), details)
    return success_response(data=data, message="创建成功", code=201)


@itsm_bp.put("/liability-regs/<liab_cd>")
@login_required
def update_liability_reg(liab_cd: str):  # type: ignore[no-untyped-def]
    body = request.get_json(silent=True) or {}
    data = LiabilityRegService.update(liab_cd, body)
    if data is None:
        return error_response(message="不存在", code=404)
    return success_response(data=data)


# -- 附件 (TIT11) --

@itsm_bp.get("/attachments/<maintenance_id>")
@login_required
def list_attachments(maintenance_id: str):  # type: ignore[no-untyped-def]
    data = MaintenanceAttcService.list_by_maintenance_id(maintenance_id)
    return success_response(data=data)


@itsm_bp.post("/attachments")
@login_required
def create_attachment():  # type: ignore[no-untyped-def]
    body = MaintenanceAttcCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    data = MaintenanceAttcService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


# -- 换机配件明细 (TIT10_POS_DETAIL) --

@itsm_bp.get("/pos-details/<maintenance_id>")
@login_required
def list_pos_details(maintenance_id: str):  # type: ignore[no-untyped-def]
    data = PosDetailService.list_by_maintenance_id(maintenance_id)
    return success_response(data=data)


@itsm_bp.post("/pos-details")
@login_required
def create_pos_detail():  # type: ignore[no-untyped-def]
    body = PosDetailCreate.model_validate(request.get_json(silent=True) or {})
    data = PosDetailService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


# -- 未关单跟踪 (TIT29) --

@itsm_bp.get("/no-close-track/<maintenance_id>")
@login_required
def list_no_close_track(maintenance_id: str):  # type: ignore[no-untyped-def]
    data = NoCloseTrackService.list_by_maintenance_id(maintenance_id)
    return success_response(data=data)


@itsm_bp.get("/no-close-tracks")
@login_required
def list_all_no_close():  # type: ignore[no-untyped-def]
    page: int = request.args.get("page", 1, type=int)
    per_page: int = request.args.get("per_page", 20, type=int)
    data = NoCloseTrackService.list_all(page=page, per_page=per_page)
    return success_response(data=data)


@itsm_bp.post("/no-close-track")
@login_required
def create_no_close_track():  # type: ignore[no-untyped-def]
    body = NoCloseTrackCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    data = NoCloseTrackService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


# -- 报修信息 (TIT05) --

@itsm_bp.get("/repair-infos")
@login_required
def list_repair_infos():  # type: ignore[no-untyped-def]
    page: int = request.args.get("page", 1, type=int)
    per_page: int = request.args.get("per_page", 20, type=int)
    data = RepairInfoService.list_all(page=page, per_page=per_page)
    return success_response(data=data)


@itsm_bp.post("/repair-infos")
@login_required
def create_repair_info():  # type: ignore[no-untyped-def]
    body = RepairInfoCreate.model_validate(request.get_json(silent=True) or {})
    data = RepairInfoService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


@itsm_bp.delete("/repair-infos/<int:record_id>")
@login_required
def delete_repair_info(record_id: int):  # type: ignore[no-untyped-def]
    if not RepairInfoService.delete(record_id):
        return error_response(message="记录不存在", code=404)
    return success_response(message="已删除")


# -- 时间点级别 (TIT01) --

@itsm_bp.get("/timepoints")
@login_required
def list_timepoints():  # type: ignore[no-untyped-def]
    data = TimepointAreaService.list_all()
    return success_response(data=data)


@itsm_bp.get("/timepoints/<levels>")
@login_required
def get_timepoint(levels: str):  # type: ignore[no-untyped-def]
    data = TimepointAreaService.get(levels)
    if data is None:
        return error_response(message="不存在", code=404)
    return success_response(data=data)


@itsm_bp.post("/timepoints")
@login_required
def create_timepoint():  # type: ignore[no-untyped-def]
    body = TimepointAreaCreate.model_validate(request.get_json(silent=True) or {})
    data = TimepointAreaService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


@itsm_bp.put("/timepoints/<levels>")
@login_required
def update_timepoint(levels: str):  # type: ignore[no-untyped-def]
    body = TimepointAreaUpdate.model_validate(request.get_json(silent=True) or {})
    data = TimepointAreaService.update(levels, body.model_dump(exclude_none=True))
    if data is None:
        return error_response(message="不存在", code=404)
    return success_response(data=data)


# -- 状态变更轨迹 (TIT10_MAIN_TRACK) --

@itsm_bp.get("/tracks/<maintenance_id>")
@login_required
def list_tracks(maintenance_id: str):  # type: ignore[no-untyped-def]
    data = MaintenanceDailyTrackService.list_by_maintenance_id(maintenance_id)
    return success_response(data=data)


# -- 开通选择明细 (TIT19) --

@itsm_bp.get("/on-choose/<bill_id>")
@login_required
def list_on_choose(bill_id: str):  # type: ignore[no-untyped-def]
    data = OnChooseDtService.list_by_bill_id(bill_id)
    return success_response(data=data)


@itsm_bp.post("/on-choose")
@login_required
def create_on_choose():  # type: ignore[no-untyped-def]
    body = OnChooseDtCreate.model_validate(request.get_json(silent=True) or {})
    data = OnChooseDtService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


@itsm_bp.get("/should-charge")
@login_required
def should_charge():  # type: ignore[no-untyped-def]
    """判断门店是否应收费（基于客户资产）。"""
    store_id = request.args.get("store_id", "")
    if not store_id:
        return error_response(message="缺少 store_id", code=400)
    data = ChargeService.should_charge(store_id)
    return success_response(data=data)


# ---- 派单规则 (TIT30) ----


@itsm_bp.get("/dispatch-rules")
@login_required
def list_dispatch_rules():  # type: ignore[no-untyped-def]
    """派单规则列表（按 priority 升序）。"""
    from app.services.itsm_service import DispatchRuleService

    return success_response(data=DispatchRuleService.list_rules())


@itsm_bp.post("/dispatch-rules")
@login_required
def create_dispatch_rule():  # type: ignore[no-untyped-def]
    """新增派单规则。"""
    from app.services.itsm_service import DispatchRuleService

    body = request.get_json(silent=True) or {}
    if not body.get("rule_name"):
        return error_response(message="规则名称不能为空", code=400)
    user_cd: str = g.current_user
    data = DispatchRuleService.create_rule(body, user_cd)
    return success_response(data=data, message="创建成功", code=201)


@itsm_bp.put("/dispatch-rules/<int:rule_id>")
@login_required
def update_dispatch_rule(rule_id: int):  # type: ignore[no-untyped-def]
    """更新派单规则。"""
    from app.services.itsm_service import DispatchRuleService

    body = request.get_json(silent=True) or {}
    user_cd: str = g.current_user
    r = DispatchRuleService.update_rule(rule_id, body, user_cd)
    return success_response(data=r) if r else error_response(message="规则不存在", code=404)


@itsm_bp.delete("/dispatch-rules/<int:rule_id>")
@login_required
def delete_dispatch_rule(rule_id: int):  # type: ignore[no-untyped-def]
    """删除派单规则。"""
    from app.services.itsm_service import DispatchRuleService

    return (
        success_response(message="已删除")
        if DispatchRuleService.delete_rule(rule_id)
        else error_response(message="规则不存在", code=404)
    )


@itsm_bp.get("/dispatch-rules/resolve")
@login_required
def resolve_dispatch_rule():  # type: ignore[no-untyped-def]
    """按故障类型+门店解析派单目标（供手动派工表单默认值）。"""
    fault_type = request.args.get("fault_type", "")
    store_id = request.args.get("store_id", "")
    if not store_id:
        return error_response(message="缺少 store_id", code=400)
    from app.services.itsm_service import DispatchRuleService
    target = DispatchRuleService.resolve(fault_type or None, store_id)
    return success_response(data=target or {})
