"""维护单归档业务逻辑层。"""

from __future__ import annotations

from typing import Any

from app.repositories.archive_repository import ArchiveRepository
from app.repositories.itsm_repository import MaintenanceDailyRepository


class ArchiveService:
    """TIT12_MAINTENANCE_ARCHIVE 归档业务逻辑。"""

    @staticmethod
    def list_by_maintenance(maintenance_id: str) -> dict[str, Any] | None:
        """获取指定维护单的归档记录列表。"""
        record = MaintenanceDailyRepository.get_by_id(maintenance_id)
        if record is None:
            return None
        archives = ArchiveRepository.list_by_maintenance(maintenance_id)
        data = record.to_dict()
        data["archives"] = [a.to_dict() for a in archives]
        return data

    @staticmethod
    def create_archive(data: dict[str, Any]) -> dict[str, Any]:
        return ArchiveRepository.create(data).to_dict()

    @staticmethod
    def update_archive(archive_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        archive = ArchiveRepository.get_by_id(archive_id)
        if archive is None:
            return None
        return ArchiveRepository.update(archive, data).to_dict()

    @staticmethod
    def delete_archive(archive_id: int) -> bool:
        archive = ArchiveRepository.get_by_id(archive_id)
        if archive is None:
            return False
        ArchiveRepository.delete(archive)
        return True
