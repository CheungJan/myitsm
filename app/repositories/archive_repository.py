"""维护单归档数据访问层。"""

from __future__ import annotations

from app.extensions import db
from app.models.itsm import MaintenanceArchive


class ArchiveRepository:
    """TIT12_MAINTENANCE_ARCHIVE 归档记录数据访问。"""

    @staticmethod
    def list_by_maintenance(
        maintenance_id: str,
    ) -> list[MaintenanceArchive]:
        return list(
            db.session.query(MaintenanceArchive)
            .filter(MaintenanceArchive.maintenance_id == maintenance_id)
            .order_by(MaintenanceArchive.create_time.desc())
            .all()
        )

    @staticmethod
    def get_by_id(archive_id: int) -> MaintenanceArchive | None:
        return db.session.get(MaintenanceArchive, archive_id)

    @staticmethod
    def create(data: dict[str, object]) -> MaintenanceArchive:
        archive = MaintenanceArchive(**data)
        db.session.add(archive)
        db.session.commit()
        return archive

    @staticmethod
    def update(archive: MaintenanceArchive, data: dict[str, object]) -> MaintenanceArchive:
        for k, v in data.items():
            setattr(archive, k, v)
        db.session.commit()
        return archive

    @staticmethod
    def delete(archive: MaintenanceArchive) -> None:
        db.session.delete(archive)
        db.session.commit()
