"""ITSM 业务数据访问层。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc

from app.extensions import db
from app.models.itsm import (
    AccessoriesUpdate,
    CloseBills,
    DeviceChange,
    MaintenanceD2D,
    MaintenanceDaily,
    MaintenanceDailyTrack,
    MaintenanceDispatch,
    MaintenanceOpen,
    MaintenanceRenovate,
    MaintenanceRV,
    RecycleTask,
    RecycleTaskDtl,
    StoreClose,
)
from app.models.master import CustomerHistory


def _gen_id(prefix: str = "") -> str:
    """生成8位唯一ID。"""
    return (prefix + uuid.uuid4().hex[:8].upper())[:8]


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
    ) -> tuple[list[MaintenanceDaily], int]:
        """分页查询日常维护单。"""
        query = db.session.query(MaintenanceDaily)
        if status:
            query = query.filter(MaintenanceDaily.current_status == status)
        if store_id:
            query = query.filter(MaintenanceDaily.store_id == store_id)
        query = query.order_by(desc(MaintenanceDaily.create_time))
        total: int = query.count()
        items: list[MaintenanceDaily] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> MaintenanceDaily:
        now = datetime.now(UTC)
        record = MaintenanceDaily(
            maintenance_id=_gen_id(),
            current_status="00",
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
            new_opening_id=_gen_id(),
            current_status="00",
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
            renew_id=_gen_id(),
            current_status="00",
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
        record: MaintenanceRenovate,
        new_status: str,
        updator: str,
    ) -> MaintenanceRenovate:
        record.current_status = new_status
        record.update_time = datetime.now(UTC)
        record.updator = updator
        return record


class DeviceChangeRepository:
    """设备变更单数据访问。"""

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
            device_change_id=_gen_id(),
            current_status="00",
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
            store_close_id=_gen_id(),
            current_status="00",
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


class RVRepository:
    """客户回访数据访问（公用附表 TIT24）。"""

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


class AccessoriesUpdateRepository:
    """配件更新数据访问（TIT25）。"""

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


class CloseBillRepository:
    """关单数据访问（TIT27）。"""

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


class DispatchRepository:
    """维护单分派数据访问（TIT21）。"""

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
            recycle_id=_gen_id("R"),
            task_status="00",
            create_time=now,
            creator=creator,
            update_time=now,
            updator=creator,
            **data,
        )
        db.session.add(record)
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
    def list_details(recycle_id: str) -> list[RecycleTaskDtl]:
        return (
            db.session.query(RecycleTaskDtl).filter(RecycleTaskDtl.recycle_id == recycle_id).all()
        )
