"""IoT数据监控数据访问层（Tier-3 G8）。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.extensions import db
from app.models.iot import AlertLog, AlertRule, DeviceConn, DeviceData


class DeviceConnRepository:
    """设备接入数据访问。"""

    @staticmethod
    def get_by_id(conn_id: str) -> DeviceConn | None:
        return db.session.get(DeviceConn, conn_id)

    @staticmethod
    def get_by_eid(eid: str) -> DeviceConn | None:
        return db.session.query(DeviceConn).filter(DeviceConn.eid == eid).first()

    @staticmethod
    def list_all(
        online_status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[DeviceConn], int]:
        query = db.session.query(DeviceConn).filter(DeviceConn.useflg == "1")
        if online_status is not None:
            query = query.filter(DeviceConn.online_status == online_status)
        total: int = query.count()
        items: list[DeviceConn] = (
            query.order_by(DeviceConn.conn_id).offset((page - 1) * per_page).limit(per_page).all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> DeviceConn:
        now = datetime.now(UTC)
        record = DeviceConn(opercd=creator, upddate=now, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: DeviceConn,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> DeviceConn:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record


class DeviceDataRepository:
    """设备数据访问。"""

    @staticmethod
    def list_by_eid(
        eid: str,
        data_type: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[DeviceData], int]:
        query = db.session.query(DeviceData).filter(DeviceData.eid == eid)
        if data_type is not None:
            query = query.filter(DeviceData.data_type == data_type)
        total: int = query.count()
        items: list[DeviceData] = (
            query.order_by(DeviceData.report_time.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> DeviceData:
        now = datetime.now(UTC)
        record = DeviceData(opercd=creator, upddate=now, **data)
        db.session.add(record)
        return record


class AlertRuleRepository:
    """报警规则数据访问。"""

    @staticmethod
    def get_by_id(rule_id: str) -> AlertRule | None:
        return db.session.get(AlertRule, rule_id)

    @staticmethod
    def list_all(useflg: str | None = "1") -> list[AlertRule]:
        query = db.session.query(AlertRule)
        if useflg is not None:
            query = query.filter(AlertRule.useflg == useflg)
        return query.order_by(AlertRule.rule_id).all()

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> AlertRule:
        now = datetime.now(UTC)
        record = AlertRule(opercd=creator, upddate=now, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: AlertRule,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> AlertRule:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record


class AlertLogRepository:
    """报警记录数据访问。"""

    @staticmethod
    def list_all(
        eid: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[AlertLog], int]:
        query = db.session.query(AlertLog)
        if eid is not None:
            query = query.filter(AlertLog.eid == eid)
        if status is not None:
            query = query.filter(AlertLog.status == status)
        total: int = query.count()
        items: list[AlertLog] = (
            query.order_by(AlertLog.alert_time.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> AlertLog:
        now = datetime.now(UTC)
        record = AlertLog(opercd=creator, upddate=now, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(record: AlertLog, data: dict[str, Any]) -> AlertLog:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        return record

    @staticmethod
    def get_by_id(log_id: int) -> AlertLog | None:
        return db.session.get(AlertLog, log_id)
