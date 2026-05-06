"""押金管理数据访问层。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc

from app.extensions import db
from app.models.deposit import Deposit, DepositDetail, DepositPosModel


class DepositRepository:
    """押金主记录数据访问。"""

    @staticmethod
    def get_by_id(custcd: str) -> Deposit | None:
        return db.session.get(Deposit, custcd)

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> tuple[list[Deposit], int]:
        query = db.session.query(Deposit)
        total: int = query.count()
        items: list[Deposit] = (
            query.order_by(Deposit.custcd).offset((page - 1) * per_page).limit(per_page).all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any]) -> Deposit:
        now = datetime.now(UTC)
        record = Deposit(updatetime=now, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(record: Deposit, data: dict[str, Any]) -> Deposit:
        for key, value in data.items():
            setattr(record, key, value)
        record.updatetime = datetime.now(UTC)
        return record


class DepositDetailRepository:
    """押金变更明细数据访问。"""

    @staticmethod
    def list_by_customer(
        custcd: str, page: int = 1, per_page: int = 20
    ) -> tuple[list[DepositDetail], int]:
        query = db.session.query(DepositDetail).filter(
            DepositDetail.custcd == custcd, DepositDetail.useflg == "1"
        )
        total: int = query.count()
        items: list[DepositDetail] = (
            query.order_by(desc(DepositDetail.gendate))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any]) -> DepositDetail:
        now = datetime.now(UTC)
        record = DepositDetail(updatetime=now, gendate=now, **data)
        db.session.add(record)
        return record


class DepositPosModelRepository:
    """设备型号押金标准数据访问。"""

    @staticmethod
    def get_by_id(model_cd: str) -> DepositPosModel | None:
        return db.session.get(DepositPosModel, model_cd)

    @staticmethod
    def list_all(useflg: str | None = "1") -> list[DepositPosModel]:
        query = db.session.query(DepositPosModel)
        if useflg is not None:
            query = query.filter(DepositPosModel.useflg == useflg)
        return query.order_by(DepositPosModel.model_cd).all()

    @staticmethod
    def create(data: dict[str, Any]) -> DepositPosModel:
        record = DepositPosModel(**data)
        db.session.add(record)
        return record

    @staticmethod
    def update(record: DepositPosModel, data: dict[str, Any]) -> DepositPosModel:
        for key, value in data.items():
            setattr(record, key, value)
        return record
