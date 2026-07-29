"""Entitlement 权益判定数据访问层。"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.extensions import db
from app.models.entitlement import ServiceContract, SpecialAgreement

# 需要转换为 date 类型的字段
_DATE_FIELDS = {"effective_date", "expire_date"}


def _coerce_dates(data: dict[str, Any]) -> dict[str, Any]:
    """将日期字符串字段转换为 date 对象，兼容 SQLite Date 列。"""
    result = dict(data)
    for key in _DATE_FIELDS:
        val = result.get(key)
        if isinstance(val, str) and val:
            result[key] = date.fromisoformat(val)
    return result


class SpecialAgreementRepository:
    """特殊客户协议数据访问。"""

    @staticmethod
    def list_all(filters: dict[str, Any] | None = None) -> list[SpecialAgreement]:
        """查询列表。"""
        query = db.session.query(SpecialAgreement)
        if filters:
            if filters.get("cust_cd"):
                query = query.filter(SpecialAgreement.cust_cd == filters["cust_cd"])
            if filters.get("useflg"):
                query = query.filter(SpecialAgreement.useflg == filters["useflg"])
        return query.order_by(SpecialAgreement.effective_date.desc()).all()

    @staticmethod
    def get_by_id(agreement_id: str) -> SpecialAgreement | None:
        return db.session.get(SpecialAgreement, agreement_id)

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> SpecialAgreement:
        record = SpecialAgreement(**_coerce_dates(data), creator=creator)
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def update(record: SpecialAgreement, data: dict[str, Any]) -> None:
        for k, v in _coerce_dates(data).items():
            setattr(record, k, v)
        db.session.commit()


class ServiceContractRepository:
    """维保合同数据访问。"""

    @staticmethod
    def list_all(filters: dict[str, Any] | None = None) -> list[ServiceContract]:
        """查询列表。"""
        query = db.session.query(ServiceContract)
        if filters:
            if filters.get("cust_cd"):
                query = query.filter(ServiceContract.cust_cd == filters["cust_cd"])
            if filters.get("eid"):
                query = query.filter(ServiceContract.eid == filters["eid"])
            if filters.get("useflg"):
                query = query.filter(ServiceContract.useflg == filters["useflg"])
        return query.order_by(ServiceContract.effective_date.desc()).all()

    @staticmethod
    def get_by_id(contract_id: str) -> ServiceContract | None:
        return db.session.get(ServiceContract, contract_id)

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> ServiceContract:
        record = ServiceContract(**_coerce_dates(data), creator=creator)
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def update(record: ServiceContract, data: dict[str, Any]) -> None:
        for k, v in _coerce_dates(data).items():
            setattr(record, k, v)
        db.session.commit()
