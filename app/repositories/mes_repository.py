"""生产制造MES数据访问层（Tier-3 G7）。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.extensions import db
from app.models.mes import MaterialConsume, ProcessDef, WorkOrder, WorkProcess


class WorkOrderRepository:
    """生产工单数据访问。"""

    @staticmethod
    def get_by_id(wo_id: str) -> WorkOrder | None:
        return db.session.get(WorkOrder, wo_id)

    @staticmethod
    def list_all(
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[WorkOrder], int]:
        query = db.session.query(WorkOrder)
        if status is not None:
            query = query.filter(WorkOrder.status == status)
        total: int = query.count()
        items: list[WorkOrder] = (
            query.order_by(WorkOrder.wo_id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> WorkOrder:
        now = datetime.now(UTC)
        record = WorkOrder(opercd=creator, upddate=now, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: WorkOrder,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> WorkOrder:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record


class ProcessDefRepository:
    """工序定义数据访问。"""

    @staticmethod
    def get_by_id(process_cd: str) -> ProcessDef | None:
        return db.session.get(ProcessDef, process_cd)

    @staticmethod
    def list_all(useflg: str | None = "1") -> list[ProcessDef]:
        query = db.session.query(ProcessDef)
        if useflg is not None:
            query = query.filter(ProcessDef.useflg == useflg)
        return query.order_by(ProcessDef.sort_no).all()

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> ProcessDef:
        now = datetime.now(UTC)
        record = ProcessDef(opercd=creator, upddate=now, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: ProcessDef,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> ProcessDef:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record


class WorkProcessRepository:
    """工单工序数据访问。"""

    @staticmethod
    def list_by_wo(wo_id: str) -> list[WorkProcess]:
        return (
            db.session.query(WorkProcess)
            .filter(WorkProcess.wo_id == wo_id)
            .order_by(WorkProcess.seq_no)
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> WorkProcess:
        now = datetime.now(UTC)
        record = WorkProcess(opercd=creator, upddate=now, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: WorkProcess,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> WorkProcess:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record

    @staticmethod
    def get_by_id(wp_id: int) -> WorkProcess | None:
        return db.session.get(WorkProcess, wp_id)


class MaterialConsumeRepository:
    """物料消耗数据访问。"""

    @staticmethod
    def list_by_wo(wo_id: str) -> list[MaterialConsume]:
        return (
            db.session.query(MaterialConsume)
            .filter(MaterialConsume.wo_id == wo_id)
            .order_by(MaterialConsume.id)
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> MaterialConsume:
        now = datetime.now(UTC)
        record = MaterialConsume(opercd=creator, upddate=now, **data)
        db.session.add(record)
        return record
