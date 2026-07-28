"""押金管理业务服务层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models.master import Customer, SysCode
from app.repositories.deposit_repository import (
    DepositDetailRepository,
    DepositIORepository,
    DepositPosModelRepository,
    DepositRepository,
)


def _enrich_c_type(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """为押金明细补充 c_type_nm（从 PL 字典查询）。"""
    codes = {r.get("c_type", "") for r in items if r.get("c_type")}
    if not codes:
        return items
    names = dict(
        db.session.query(SysCode.code_cd, SysCode.code_nm)
        .filter(SysCode.code_typ == "PL", SysCode.code_cd.in_(codes))
        .all()
    )
    for r in items:
        ct = r.get("c_type", "")
        if ct and ct in names:
            r["c_type_nm"] = names[ct]
    return items


def _enrich_cust_card(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """为押金记录补充 cust_card（从 tmm22_customers 关联查询）。"""
    custcds = {r.get("custcd") for r in items if r.get("custcd")}
    if not custcds:
        return items
    cards = dict(
        db.session.query(Customer.cust_cd, Customer.cust_card)
        .filter(Customer.cust_cd.in_(custcds))
        .all()
    )
    for r in items:
        cd = r.get("custcd")
        if cd and cd in cards:
            r["cust_card"] = cards[cd]
    return items


class DepositService:
    """押金主记录服务。"""

    @staticmethod
    def get(custcd: str) -> dict[str, Any] | None:
        record = DepositRepository.get_by_id(custcd)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = DepositRepository.list_all(page, per_page)
        enriched = _enrich_cust_card([r.to_dict() for r in items])
        return {
            "items": enriched,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = DepositRepository.create(data)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(custcd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = DepositRepository.get_by_id(custcd)
        if record is None:
            return None
        DepositRepository.update(record, data)
        db.session.commit()
        return record.to_dict()


class DepositDetailService:
    """押金变更明细服务。"""

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = DepositDetailRepository.list_all(page=page, per_page=per_page)
        enriched = _enrich_c_type(_enrich_cust_card([r.to_dict() for r in items]))
        return {"items": enriched, "total": total, "page": page, "per_page": per_page}

    @staticmethod
    def list_by_customer(custcd: str, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = DepositDetailRepository.list_by_customer(custcd, page, per_page)
        enriched = _enrich_c_type(_enrich_cust_card([r.to_dict() for r in items]))
        return {
            "items": enriched,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = DepositDetailRepository.create(data)
        db.session.commit()
        return record.to_dict()


class DepositPosModelService:
    """设备型号押金标准服务。"""

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        records = DepositPosModelRepository.list_all()
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = DepositPosModelRepository.create(data)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(model_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = DepositPosModelRepository.get_by_id(model_cd)
        if record is None:
            return None
        DepositPosModelRepository.update(record, data)
        db.session.commit()
        return record.to_dict()


class DepositIOService:
    """押金出入流水服务。"""

    @staticmethod
    def list_records(
        custcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = DepositIORepository.list_by_filters(
            custcd=custcd, page=page, per_page=per_page
        )
        enriched = _enrich_cust_card([item.to_dict() for item in items])
        return {
            "items": enriched,
            "total": total,
            "page": page,
            "per_page": per_page,
        }
