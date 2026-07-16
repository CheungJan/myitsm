"""ITSM 业务数据访问层。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc

from app.extensions import db
from app.repositories.procurement_repository import _gen_master_id
from app.models.itsm import (
    AccessoriesUpdate,
    CloseBills,
    DeviceChange,
    FreeReplace,
    FreeReplaceDt,
    LiabilityReg,
    LiabilityRegDt,
    Maintenance,
    MaintenanceAttc,
    MaintenanceD2D,
    MaintenanceDaily,
    MaintenanceDailyTrack,
    MaintenanceDispatch,
    MaintenanceLiability,
    MaintenanceOpen,
    MaintenancePlan,
    MaintenanceRenovate,
    MaintenanceRV,
    EquipmentRenovate,
    NoCloseTrack,
    OnChooseDt,
    PayList,
    PosDetail,
    RecycleTask,
    RecycleTaskDtl,
    RepairInfo,
    StoreClose,
    TimepointArea,
)
from app.models.master import CustomerHistory, IdMaster


def _gen_id(prefix: str = "") -> str:
    """生成8位唯一ID。"""
    return (prefix + uuid.uuid4().hex[:8].upper())[:8]


def _gen_itsm_id(id_type: str, id_type_name: str, model_cls: Any, pk_field: str) -> str:
    """ITSM 单据自增编号：首次取号时从对应业务表 MAX(主键) 初始化 IdMaster。

    避免从 000001 开始与已有历史数据冲突。
    """
    from sqlalchemy import func

    id_master = db.session.get(IdMaster, id_type)
    if id_master is None:
        # 从业务表 MAX(主键) 提取当前最大序号
        max_pk = db.session.query(func.max(getattr(model_cls, pk_field))).scalar()
        init_no = 0
        if max_pk:
            # 去掉前缀，取数字部分
            num_part = "".join(ch for ch in str(max_pk) if ch.isdigit())
            if num_part:
                try:
                    init_no = int(num_part)
                except ValueError:
                    init_no = 0
        return _gen_master_id(id_type, id_type_name, init_current_no=init_no)
    return _gen_master_id(id_type, id_type_name)


class MaintenanceDailyRepository:
    """日常维护单数据访问。"""

    @staticmethod
    def get_by_id(maintenance_id: str) -> MaintenanceDaily | None:
        return db.session.get(MaintenanceDaily, maintenance_id)

    @staticmethod
    def list_by_filters(
        status: str | None = None,
        store_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
        *,
        maintenance_id: str | None = None,
        company_id: str | None = None,
        area_cd: str | None = None,
        firstor: str | None = None,
        cust_card: str | None = None,
        cust_nm: str | None = None,
        address: str | None = None,
        fault_type: str | None = None,
        short_description: str | None = None,
        request_begin: str | None = None,
        request_end: str | None = None,
        first_begin: str | None = None,
        first_end: str | None = None,
        dispatch_to: str | None = None,
        area_user: str | None = None,
    ) -> tuple[list[MaintenanceDaily], int]:
        """分页查询日常维护单（对齐 PB u_itsm_rep_maintenanceday 报表查询条件）。

        status 支持单值或逗号分隔多值（如 "1,2,5"）。
        dispatch_to: 派给我——按派工人 accpectder 过滤（关联 TIT21）。
        area_user: 本区域——按用户编码查 TIT06 所属区域，过滤门店 area_cd。
        """
        from app.models.itsm import MaintenanceDispatch, UserArea
        from app.models.master import Customer

        query = db.session.query(MaintenanceDaily)
        # 状态过滤（支持多值）
        if status:
            statuses = [s.strip() for s in status.split(",") if s.strip()]
            if len(statuses) == 1:
                query = query.filter(MaintenanceDaily.current_status == statuses[0])
            elif statuses:
                query = query.filter(MaintenanceDaily.current_status.in_(statuses))
        if store_id:
            query = query.filter(MaintenanceDaily.store_id == store_id)
        if maintenance_id:
            query = query.filter(MaintenanceDaily.maintenance_id.ilike(f"%{maintenance_id}%"))
        if company_id:
            query = query.filter(MaintenanceDaily.company_id == company_id)
        if firstor:
            query = query.filter(MaintenanceDaily.firstor == firstor)
        if fault_type:
            query = query.filter(MaintenanceDaily.fault_type == fault_type)
        if short_description:
            query = query.filter(MaintenanceDaily.short_description.ilike(f"%{short_description}%"))
        # 请求时间范围
        if request_begin:
            query = query.filter(MaintenanceDaily.request_time >= request_begin)
        if request_end:
            query = query.filter(MaintenanceDaily.request_time <= f"{request_end} 23:59:59")
        # 上门时间范围
        if first_begin:
            query = query.filter(MaintenanceDaily.first_time >= first_begin)
        if first_end:
            query = query.filter(MaintenanceDaily.first_time <= f"{first_end} 23:59:59")
        # 关联 tmm22_customers 查询磁卡号/店名/地址/区域
        if cust_card or cust_nm or address or area_cd or area_user:
            query = query.join(Customer, Customer.cust_cd == MaintenanceDaily.store_id)
            if cust_card:
                query = query.filter(Customer.cust_card.ilike(f"%{cust_card}%"))
            if cust_nm:
                query = query.filter(Customer.cust_nm.ilike(f"%{cust_nm}%"))
            if address:
                query = query.filter(Customer.address.ilike(f"%{address}%"))
            if area_cd:
                query = query.filter(Customer.area_cd == area_cd)
            # 本区域：按用户编码查 TIT06 所属区域集合
            if area_user:
                area_subq = (
                    db.session.query(UserArea.area_cd)
                    .filter(UserArea.user_cd == area_user)
                    .subquery()
                )
                query = query.filter(Customer.area_cd.in_(db.select(area_subq)))
        # 派给我：按派工人 accpectder 过滤（关联 TIT21）
        if dispatch_to:
            md_subq = (
                db.session.query(MaintenanceDispatch.maintenance_id)
                .filter(MaintenanceDispatch.accpectder == dispatch_to)
                .subquery()
            )
            query = query.filter(
                MaintenanceDaily.maintenance_id.in_(db.select(md_subq))
            )
        query = query.order_by(desc(MaintenanceDaily.create_time))
        total: int = query.count()
        items: list[MaintenanceDaily] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> MaintenanceDaily:
        now = datetime.now(UTC)
        record = MaintenanceDaily(
            maintenance_id=_gen_itsm_id("MD", "日常维护单号", MaintenanceDaily, "maintenance_id"),
            current_status="1",
            create_time=now,
            creator=creator,
            update_time=now,
            updator=creator,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: MaintenanceDaily, data: dict[str, Any], updator: str) -> MaintenanceDaily:
        for key, value in data.items():
            setattr(record, key, value)
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record

    @staticmethod
    def update_status(
        record: MaintenanceDaily,
        new_status: str,
        updator: str,
    ) -> MaintenanceDaily:
        record.current_status = new_status
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record

    @staticmethod
    def add_track(
        maintenance_id: str,
        from_status: str,
        to_status: str,
        oper_cd: str,
        remark: str | None = None,
    ) -> MaintenanceDailyTrack:
        track = MaintenanceDailyTrack(
            maintenance_id=maintenance_id,
            from_status=from_status,
            to_status=to_status,
            oper_cd=oper_cd,
            memo=remark,
            updatetime=datetime.now(UTC),
        )
        db.session.add(track)
        return track


class MaintenanceOpenRepository:
    """新机开通单数据访问。"""

    @staticmethod
    def get_by_id(opening_id: str) -> MaintenanceOpen | None:
        return db.session.get(MaintenanceOpen, opening_id)

    @staticmethod
    def list_by_filters(
        status: str | None = None,
        store_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[MaintenanceOpen], int]:
        query = db.session.query(MaintenanceOpen)
        if status:
            query = query.filter(MaintenanceOpen.current_status == status)
        if store_id:
            query = query.filter(MaintenanceOpen.store_id == store_id)
        query = query.order_by(desc(MaintenanceOpen.create_time))
        total: int = query.count()
        items: list[MaintenanceOpen] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> MaintenanceOpen:
        now = datetime.now(UTC)
        record = MaintenanceOpen(
            new_opening_id=_gen_itsm_id("MO", "新机开通单号", MaintenanceOpen, "new_opening_id"),
            current_status="1",
            create_time=now,
            creator=creator,
            update_time=now,
            updator=creator,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: MaintenanceOpen, data: dict[str, Any], updator: str) -> MaintenanceOpen:
        for key, value in data.items():
            setattr(record, key, value)
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record

    # ---- TIT14 设备明细 ----
    @staticmethod
    def add_equipment(opening_id: str, data: dict[str, Any]) -> EquipmentOpen:
        now = datetime.now(UTC)
        eq = EquipmentOpen(
            new_opening_id=opening_id,
            create_time=now, creator=data.get("creator", ""),
            update_time=now, updator=data.get("creator", ""),
            **{k: v for k, v in data.items() if k != "creator"},
        )
        db.session.add(eq)
        return eq

    @staticmethod
    def delete_equipment(opening_id: str, eq_id: int) -> bool:
        eq = db.session.get(EquipmentOpen, eq_id)
        if eq is None or eq.new_opening_id != opening_id:
            return False
        db.session.delete(eq)
        return True

    @staticmethod
    def update_status(
        record: MaintenanceOpen,
        new_status: str,
        updator: str,
    ) -> MaintenanceOpen:
        record.current_status = new_status
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record


class MaintenanceRenovateRepository:
    """旧机翻新单数据访问。"""

    @staticmethod
    def get_by_id(renew_id: str) -> MaintenanceRenovate | None:
        return db.session.get(MaintenanceRenovate, renew_id)

    @staticmethod
    def list_by_filters(
        status: str | None = None,
        store_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[MaintenanceRenovate], int]:
        query = db.session.query(MaintenanceRenovate)
        if status:
            query = query.filter(MaintenanceRenovate.current_status == status)
        if store_id:
            query = query.filter(MaintenanceRenovate.store_id == store_id)
        query = query.order_by(desc(MaintenanceRenovate.create_time))
        total: int = query.count()
        items: list[MaintenanceRenovate] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> MaintenanceRenovate:
        now = datetime.now(UTC)
        record = MaintenanceRenovate(
            renew_id=_gen_itsm_id("MR", "旧机翻新单号", MaintenanceRenovate, "renew_id"),
            current_status="1",
            create_time=now,
            creator=creator,
            update_time=now,
            updator=creator,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: MaintenanceRenovate, data: dict[str, Any], updator: str) -> MaintenanceRenovate:
        for key, value in data.items():
            setattr(record, key, value)
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record

    # ---- TIT15 设备明细 ----
    @staticmethod
    def list_equipments(renew_id: str) -> list[EquipmentRenovate]:
        return db.session.query(EquipmentRenovate).filter(
            EquipmentRenovate.renovate_id == renew_id
        ).order_by(EquipmentRenovate.id).all()

    @staticmethod
    def add_equipment(renew_id: str, data: dict[str, Any]) -> EquipmentRenovate:
        now = datetime.now(UTC)
        eq = EquipmentRenovate(
            renovate_id=renew_id,
            create_time=now, creator=data.get("creator", ""),
            update_time=now, updator=data.get("creator", ""),
            **{k: v for k, v in data.items() if k != "creator"},
        )
        db.session.add(eq)
        return eq

    @staticmethod
    def delete_equipment(renew_id: str, eq_id: int) -> bool:
        eq = db.session.get(EquipmentRenovate, eq_id)
        if eq is None or eq.renovate_id != renew_id:
            return False
        db.session.delete(eq)
        return True

    @staticmethod
    def update_status(
        record: MaintenanceRenovate,
        new_status: str,
        updator: str,
    ) -> MaintenanceRenovate:
        record.current_status = new_status
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record


class DeviceChangeRepository:
    """磁卡号变更单数据访问。"""

    @staticmethod
    def get_by_id(change_id: str) -> DeviceChange | None:
        return db.session.get(DeviceChange, change_id)

    @staticmethod
    def list_by_filters(
        status: str | None = None,
        store_id: str | None = None,
        change_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[DeviceChange], int]:
        query = db.session.query(DeviceChange)
        if status:
            query = query.filter(DeviceChange.current_status == status)
        if store_id:
            query = query.filter(DeviceChange.store_id == store_id)
        if change_type:
            query = query.filter(DeviceChange.change_type == change_type)
        query = query.order_by(desc(DeviceChange.create_time))
        total: int = query.count()
        items: list[DeviceChange] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> DeviceChange:
        now = datetime.now(UTC)
        record = DeviceChange(
            device_change_id=_gen_itsm_id("BG", "磁卡号变更单号", DeviceChange, "device_change_id"),
            current_status="1",
            create_time=now,
            creator=creator,
            update_time=now,
            updator=creator,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: DeviceChange, data: dict[str, Any], updator: str) -> DeviceChange:
        for key, value in data.items():
            setattr(record, key, value)
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record

    @staticmethod
    def update_status(
        record: DeviceChange,
        new_status: str,
        updator: str,
    ) -> DeviceChange:
        record.current_status = new_status
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record

    @staticmethod
    def save_customer_history(data: dict[str, Any]) -> CustomerHistory:
        """CK变更时保存磁卡号变更历史（P0-4优化）。"""
        history = CustomerHistory(**data)
        db.session.add(history)
        return history


class StoreCloseRepository:
    """门店关闭数据访问。"""

    @staticmethod
    def get_by_id(close_id: str) -> StoreClose | None:
        return db.session.get(StoreClose, close_id)

    @staticmethod
    def list_by_filters(
        status: str | None = None,
        store_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[StoreClose], int]:
        query = db.session.query(StoreClose)
        if status:
            query = query.filter(StoreClose.current_status == status)
        if store_id:
            query = query.filter(StoreClose.store_id == store_id)
        query = query.order_by(desc(StoreClose.create_time))
        total: int = query.count()
        items: list[StoreClose] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> StoreClose:
        now = datetime.now(UTC)
        record = StoreClose(
            store_close_id=_gen_itsm_id("GB", "门店关闭单号", StoreClose, "store_close_id"),
            current_status="1",
            create_time=now,
            creator=creator,
            update_time=now,
            updator=creator,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: StoreClose, data: dict[str, Any], updator: str) -> StoreClose:
        for key, value in data.items():
            setattr(record, key, value)
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record

    @staticmethod
    def update_status(
        record: StoreClose,
        new_status: str,
        updator: str,
    ) -> StoreClose:
        record.current_status = new_status
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record


# ---------------------------------------------------------------------------
# 公用附表 Repository
# ---------------------------------------------------------------------------


class D2DRepository:
    """上门服务记录数据访问（公用附表 TIT23）。"""

    @staticmethod
    def get_by_id(record_id: int) -> MaintenanceD2D | None:
        return db.session.get(MaintenanceD2D, record_id)

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[MaintenanceD2D]:
        return (
            db.session.query(MaintenanceD2D)
            .filter(MaintenanceD2D.maintenance_id == maintenance_id)
            .order_by(desc(MaintenanceD2D.create_time))
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> MaintenanceD2D:
        now = datetime.now(UTC)
        record = MaintenanceD2D(
            create_time=now,
            creator=creator,
            update_time=now,
            updator=creator,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: MaintenanceD2D, data: dict[str, Any], updator: str) -> MaintenanceD2D:
        for key, value in data.items():
            setattr(record, key, value)
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record


class RVRepository:
    """客户回访数据访问（公用附表 TIT24）。"""

    @staticmethod
    def get_by_id(record_id: int) -> MaintenanceRV | None:
        return db.session.get(MaintenanceRV, record_id)

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[MaintenanceRV]:
        return (
            db.session.query(MaintenanceRV)
            .filter(MaintenanceRV.maintenance_id == maintenance_id)
            .order_by(desc(MaintenanceRV.create_time))
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> MaintenanceRV:
        now = datetime.now(UTC)
        record = MaintenanceRV(
            create_time=now,
            creator=creator,
            update_time=now,
            updator=creator,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: MaintenanceRV, data: dict[str, Any], updator: str) -> MaintenanceRV:
        for key, value in data.items():
            setattr(record, key, value)
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record


class AccessoriesUpdateRepository:
    """配件更新数据访问（TIT25）。"""

    @staticmethod
    def get_by_id(record_id: int) -> AccessoriesUpdate | None:
        return db.session.get(AccessoriesUpdate, record_id)

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[AccessoriesUpdate]:
        return (
            db.session.query(AccessoriesUpdate)
            .filter(AccessoriesUpdate.maintenance_id == maintenance_id)
            .order_by(desc(AccessoriesUpdate.create_time))
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> AccessoriesUpdate:
        now = datetime.now(UTC)
        record = AccessoriesUpdate(
            create_time=now,
            creator=creator,
            update_time=now,
            updator=creator,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: AccessoriesUpdate, data: dict[str, Any], updator: str) -> AccessoriesUpdate:
        for key, value in data.items():
            setattr(record, key, value)
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record


class CloseBillRepository:
    """关单数据访问（TIT27）。"""

    @staticmethod
    def get_by_id(record_id: int) -> CloseBills | None:
        return db.session.get(CloseBills, record_id)

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[CloseBills]:
        return (
            db.session.query(CloseBills)
            .filter(CloseBills.maintenance_id == maintenance_id)
            .order_by(desc(CloseBills.create_time))
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> CloseBills:
        now = datetime.now(UTC)
        record = CloseBills(
            create_time=now,
            creator=creator,
            update_time=now,
            updator=creator,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: CloseBills, data: dict[str, Any], updator: str) -> CloseBills:
        for key, value in data.items():
            setattr(record, key, value)
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record


class DispatchRepository:
    """维护单分派数据访问（TIT21）。"""

    @staticmethod
    def get_by_id(record_id: int) -> MaintenanceDispatch | None:
        return db.session.get(MaintenanceDispatch, record_id)

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[MaintenanceDispatch]:
        return (
            db.session.query(MaintenanceDispatch)
            .filter(MaintenanceDispatch.maintenance_id == maintenance_id)
            .order_by(desc(MaintenanceDispatch.create_time))
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> MaintenanceDispatch:
        now = datetime.now(UTC)
        record = MaintenanceDispatch(
            create_time=now,
            creator=creator,
            update_time=now,
            updator=creator,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: MaintenanceDispatch, data: dict[str, Any], updator: str) -> MaintenanceDispatch:
        for key, value in data.items():
            setattr(record, key, value)
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record


class RecycleTaskRepository:
    """回收任务数据访问（TIT20，P0-1/优化4.2）。"""

    @staticmethod
    def get_by_id(recycle_id: str) -> RecycleTask | None:
        return db.session.get(RecycleTask, recycle_id)

    @staticmethod
    def list_by_filters(
        task_status: str | None = None,
        cust_cd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[RecycleTask], int]:
        query = db.session.query(RecycleTask)
        if task_status:
            query = query.filter(RecycleTask.task_status == task_status)
        if cust_cd:
            query = query.filter(RecycleTask.cust_cd == cust_cd)
        query = query.order_by(desc(RecycleTask.create_time))
        total: int = query.count()
        items: list[RecycleTask] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> RecycleTask:
        now = datetime.now(UTC)
        record = RecycleTask(
            recycle_id=_gen_itsm_id("RC", "取机回收任务单号", RecycleTask, "recycle_id"),
            task_status="1",
            create_time=now,
            creator=creator,
            update_time=now,
            updator=creator,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: RecycleTask, data: dict[str, Any], updator: str) -> RecycleTask:
        for key, value in data.items():
            if key == "task_status":
                continue  # 状态通过 transition() 流转，不直接修改
            setattr(record, key, value)
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record

    @staticmethod
    def update_status(record: RecycleTask, new_status: str, updator: str) -> RecycleTask:
        record.task_status = new_status
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record

    @staticmethod
    def add_detail(recycle_id: str, data: dict[str, Any]) -> RecycleTaskDtl:
        dtl = RecycleTaskDtl(recycle_id=recycle_id, **data)
        db.session.add(dtl)
        return dtl

    @staticmethod
    def delete_detail(recycle_id: str, asset_id: str) -> bool:
        dtl = db.session.get(RecycleTaskDtl, (recycle_id, asset_id))
        if dtl is None:
            return False
        db.session.delete(dtl)
        return True

    @staticmethod
    def list_details(recycle_id: str) -> list[RecycleTaskDtl]:
        return (
            db.session.query(RecycleTaskDtl).filter(RecycleTaskDtl.recycle_id == recycle_id).all()
        )


class MaintenancePlanRepository:
    """保养计划数据访问（TIT17_PLAN）。"""

    @staticmethod
    def get_by_id(plan_id: int) -> MaintenancePlan | None:
        return db.session.get(MaintenancePlan, plan_id)

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> tuple[list[MaintenancePlan], int]:
        query = db.session.query(MaintenancePlan).order_by(desc(MaintenancePlan.plan_yymm))
        total: int = query.count()
        items: list[MaintenancePlan] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> MaintenancePlan:
        now = datetime.now(UTC)
        record = MaintenancePlan(
            create_time=now,
            creator=creator,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: MaintenancePlan, data: dict[str, Any]) -> MaintenancePlan:
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)
        return record


class MaintenanceT17Repository:
    """日常保养工单数据访问（TIT17_MAINTENANCE）。"""

    @staticmethod
    def get_by_id(maintenance_id: str) -> Maintenance | None:
        return db.session.get(Maintenance, maintenance_id)

    @staticmethod
    def list_by_filters(
        status: str | None = None,
        store_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Maintenance], int]:
        query = db.session.query(Maintenance)
        if status:
            query = query.filter(Maintenance.current_status == status)
        if store_id:
            query = query.filter(Maintenance.store_id == store_id)
        query = query.order_by(desc(Maintenance.create_time))
        total: int = query.count()
        items: list[Maintenance] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total


# TODO(cleanup): 免费更换（TIT28）在重构版本中已废弃，以下 FreeReplaceRepository 仅保留
# 供历史数据查询。FR/GH 均为 PB 老版本遗留号段，当前业务不再创建新免费更换单。
# 后续版本统一清理：Repository / Service / Model / Schema / API 端点。
class FreeReplaceRepository:
    """免费更换工单数据访问（TIT28_FREE_REPLACE）—— 已废弃，仅保留历史数据查询。"""

    @staticmethod
    def get_by_id(renew_id: str) -> FreeReplace | None:
        return db.session.get(FreeReplace, renew_id)

    @staticmethod
    def list_by_filters(
        status: str | None = None,
        store_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[FreeReplace], int]:
        query = db.session.query(FreeReplace)
        if status:
            query = query.filter(FreeReplace.current_status == status)
        if store_id:
            query = query.filter(FreeReplace.store_id == store_id)
        query = query.order_by(desc(FreeReplace.create_time))
        total: int = query.count()
        items: list[FreeReplace] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> FreeReplace:
        now = datetime.now(UTC)
        record = FreeReplace(
            renew_id=_gen_itsm_id("FR", "免费更换单号", FreeReplace, "renew_id"),
            current_status="1",
            create_time=now,
            creator=creator,
            update_time=now,
            updator=creator,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update_status(
        record: FreeReplace,
        new_status: str,
        updator: str,
    ) -> FreeReplace:
        record.current_status = new_status
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record

    @staticmethod
    def add_detail(renew_id: str, data: dict[str, Any]) -> FreeReplaceDt:
        record = FreeReplaceDt(
            renovate_id=renew_id,
            **data,
        )
        db.session.add(record)
        return record


# ============================================================================
# ITSM 附表 Repository（P1 补全）
# ============================================================================


class PayListRepository:
    """收费记录数据访问（TIT26_PAYLIST）。"""

    @staticmethod
    def get_by_id(record_id: int) -> PayList | None:
        return db.session.get(PayList, record_id)

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[PayList]:
        return (
            db.session.query(PayList)
            .filter(PayList.maintenance_id == maintenance_id)
            .order_by(PayList.create_time)
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> PayList:
        now = datetime.now(UTC)
        record = PayList(create_time=now, creator=creator, update_time=now, updator=creator, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(record: PayList, data: dict[str, Any], updator: str) -> PayList:
        for key, value in data.items():
            setattr(record, key, value)
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record


class MaintenanceLiabilityRepository:
    """维护单责任豁免数据访问（TIT10_MAINTENANCE_LIABILITY）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[MaintenanceLiability]:
        return (
            db.session.query(MaintenanceLiability)
            .filter(MaintenanceLiability.maintenance_id == maintenance_id)
            .order_by(MaintenanceLiability.id)
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any]) -> MaintenanceLiability:
        record = MaintenanceLiability(**data)
        db.session.add(record)
        return record

    @staticmethod
    def update(record: MaintenanceLiability, data: dict[str, Any]) -> MaintenanceLiability:
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)
        return record


class LiabilityRegRepository:
    """责任豁免字典数据访问（TIT02_LIABILITYREG）。"""

    @staticmethod
    def get_by_id(liab_cd: str) -> LiabilityReg | None:
        return db.session.get(LiabilityReg, liab_cd)

    @staticmethod
    def list_all() -> list[LiabilityReg]:
        return (
            db.session.query(LiabilityReg)
            .filter(LiabilityReg.useflg == "1")
            .order_by(LiabilityReg.liab_cd)
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any]) -> LiabilityReg:
        record = LiabilityReg(**data)
        db.session.add(record)
        return record

    @staticmethod
    def update(record: LiabilityReg, data: dict[str, Any]) -> LiabilityReg:
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)
        return record

    @staticmethod
    def add_detail(liab_cd: str, data: dict[str, Any]) -> LiabilityRegDt:
        record = LiabilityRegDt(liab_cd=liab_cd, **data)
        db.session.add(record)
        return record


class MaintenanceAttcRepository:
    """附件数据访问（TIT11_MAINTENANCE_ATTC）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[MaintenanceAttc]:
        return (
            db.session.query(MaintenanceAttc)
            .filter(MaintenanceAttc.maintenance_id == maintenance_id)
            .order_by(MaintenanceAttc.create_time)
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> MaintenanceAttc:
        now = datetime.now(UTC)
        record = MaintenanceAttc(create_time=now, creator=creator, update_time=now, updator=creator, **data)
        db.session.add(record)
        return record


class PosDetailRepository:
    """换机配件明细数据访问（TIT10_POS_DETAIL）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[PosDetail]:
        return (
            db.session.query(PosDetail)
            .filter(PosDetail.bill_id == maintenance_id)
            .order_by(PosDetail.id)
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any]) -> PosDetail:
        record = PosDetail(**data)
        db.session.add(record)
        return record


class NoCloseTrackRepository:
    """未关单跟踪数据访问（TIT29_NOCLOSE_TRACK）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[NoCloseTrack]:
        return (
            db.session.query(NoCloseTrack)
            .filter(NoCloseTrack.maintenance_id == maintenance_id)
            .order_by(NoCloseTrack.create_time)
            .all()
        )

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> tuple[list[NoCloseTrack], int]:
        query = db.session.query(NoCloseTrack).order_by(desc(NoCloseTrack.create_time))
        total: int = query.count()
        items: list[NoCloseTrack] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> NoCloseTrack:
        now = datetime.now(UTC)
        record = NoCloseTrack(create_time=now, creator=creator, update_time=now, updator=creator, **data)
        db.session.add(record)
        return record


class RepairInfoRepository:
    """报修信息数据访问（TIT05_REPAIRINFO）。"""

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> tuple[list[RepairInfo], int]:
        query = db.session.query(RepairInfo).order_by(RepairInfo.id)
        total: int = query.count()
        items: list[RepairInfo] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any]) -> RepairInfo:
        record = RepairInfo(**data)
        db.session.add(record)
        return record

    @staticmethod
    def delete(record: RepairInfo) -> None:
        db.session.delete(record)


class TimepointAreaRepository:
    """时间点级别数据访问（TIT01_TIMEPOINT_AREA）。"""

    @staticmethod
    def get_by_id(levels: str) -> TimepointArea | None:
        return db.session.get(TimepointArea, levels)

    @staticmethod
    def list_all() -> list[TimepointArea]:
        return (
            db.session.query(TimepointArea)
            .filter(TimepointArea.useflg == "1")
            .order_by(TimepointArea.levels)
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any]) -> TimepointArea:
        record = TimepointArea(**data)
        db.session.add(record)
        return record

    @staticmethod
    def update(record: TimepointArea, data: dict[str, Any]) -> TimepointArea:
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)
        return record


class MaintenanceDailyTrackRepository:
    """状态变更轨迹数据访问（TIT10_MAIN_TRACK）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[MaintenanceDailyTrack]:
        return (
            db.session.query(MaintenanceDailyTrack)
            .filter(MaintenanceDailyTrack.maintenance_id == maintenance_id)
            .order_by(desc(MaintenanceDailyTrack.updatetime))
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any]) -> MaintenanceDailyTrack:
        record = MaintenanceDailyTrack(**data)
        db.session.add(record)
        return record


class OnChooseDtRepository:
    """开通选择明细数据访问（TIT19_ON_CHOOSEDT）。"""

    @staticmethod
    def list_by_bill_id(bill_id: str) -> list[OnChooseDt]:
        return (
            db.session.query(OnChooseDt)
            .filter(OnChooseDt.bill_id == bill_id)
            .order_by(OnChooseDt.id)
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any]) -> OnChooseDt:
        record = OnChooseDt(**data)
        db.session.add(record)
        return record
