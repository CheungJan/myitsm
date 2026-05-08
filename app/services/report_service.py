"""报表查询业务服务层。

提供库存快照/预警/流水、EID 生命周期追踪、销售状态汇总、BOM 结构树等查询。
"""

from __future__ import annotations

from typing import Any

from app.repositories.report_repository import (
    BOMReportRepository,
    EidReportRepository,
    InventoryReportRepository,
    SalesReportRepository,
)


class InventoryReportService:
    """库存报表服务。"""

    @staticmethod
    def snapshot(
        whcd: str | None,
        itemtyp: str | None,
        itemcd: str | None,
        page: int,
        per_page: int,
    ) -> dict[str, Any]:
        items, total = InventoryReportRepository.get_snapshot(
            whcd=whcd, itemtyp=itemtyp, itemcd=itemcd, page=page, per_page=per_page
        )
        return {"items": items, "total": total, "page": page, "per_page": per_page}

    @staticmethod
    def alert_items() -> list[dict[str, Any]]:
        return InventoryReportRepository.get_alert_items()

    @staticmethod
    def movement_log(
        whcd: str | None,
        itemcd: str | None,
        start_date: str | None,
        end_date: str | None,
        page: int,
        per_page: int,
    ) -> dict[str, Any]:
        items, total = InventoryReportRepository.get_movement_log(
            whcd=whcd, itemcd=itemcd, start_date=start_date,
            end_date=end_date, page=page, per_page=per_page,
        )
        return {"items": items, "total": total, "page": page, "per_page": per_page}


class EidReportService:
    """EID 追踪报表服务。"""

    @staticmethod
    def lifecycle(
        eid_val: str | None,
        itemcd_val: str | None,
        custcd: str | None,
        page: int,
        per_page: int,
    ) -> dict[str, Any]:
        items, total = EidReportRepository.get_lifecycle(
            eid_val=eid_val, itemcd_val=itemcd_val, custcd=custcd, page=page, per_page=per_page
        )
        return {"items": items, "total": total, "page": page, "per_page": per_page}

    @staticmethod
    def tracks(eid_val: str, page: int, per_page: int) -> dict[str, Any]:
        items, total = EidReportRepository.get_tracks(eid_val, page=page, per_page=per_page)
        return {"items": items, "total": total, "page": page, "per_page": per_page}


class SalesReportService:
    """销售报表服务。"""

    @staticmethod
    def status_summary(
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        return SalesReportRepository.get_status_summary(start_date=start_date, end_date=end_date)

    @staticmethod
    def open_bills(page: int, per_page: int) -> dict[str, Any]:
        items, total = SalesReportRepository.get_open_bills(page=page, per_page=per_page)
        return {"items": items, "total": total, "page": page, "per_page": per_page}


class BOMReportService:
    """BOM 报表服务。"""

    @staticmethod
    def bom_tree(
        itemcd_val: str | None,
        page: int,
        per_page: int,
    ) -> dict[str, Any]:
        items, total = BOMReportRepository.get_bom_tree(
            itemcd_val=itemcd_val, page=page, per_page=per_page
        )
        return {"items": items, "total": total, "page": page, "per_page": per_page}
