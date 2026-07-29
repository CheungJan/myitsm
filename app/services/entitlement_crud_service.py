"""Entitlement 权益判定业务服务层。"""

from __future__ import annotations

from typing import Any

from app.repositories.entitlement_repository import (
    ServiceContractRepository,
    SpecialAgreementRepository,
)


class SpecialAgreementService:
    """特殊客户协议服务。"""

    @staticmethod
    def get(agreement_id: str) -> dict[str, Any] | None:
        record = SpecialAgreementRepository.get_by_id(agreement_id)
        return record.to_dict() if record else None

    @staticmethod
    def list(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        records = SpecialAgreementRepository.list_all(filters)
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = SpecialAgreementRepository.create(data, creator)
        return record.to_dict()

    @staticmethod
    def update(agreement_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = SpecialAgreementRepository.get_by_id(agreement_id)
        if record is None:
            return None
        SpecialAgreementRepository.update(record, data)
        return record.to_dict()


class ServiceContractService:
    """维保合同服务。"""

    @staticmethod
    def get(contract_id: str) -> dict[str, Any] | None:
        record = ServiceContractRepository.get_by_id(contract_id)
        return record.to_dict() if record else None

    @staticmethod
    def list(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        records = ServiceContractRepository.list_all(filters)
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = ServiceContractRepository.create(data, creator)
        return record.to_dict()

    @staticmethod
    def update(contract_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = ServiceContractRepository.get_by_id(contract_id)
        if record is None:
            return None
        ServiceContractRepository.update(record, data)
        return record.to_dict()
