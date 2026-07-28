"""报表查询业务服务层。

提供库存快照/预警/流水、EID 生命周期追踪、销售状态汇总、BOM 结构树等查询。
"""

from __future__ import annotations

from typing import Any

from app.repositories.report_repository import (
    BOMReportRepository,
    EidReportRepository,
    FaultAnalysisRepository,
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


class FaultAnalysisService:
    """D2 故障分析报表服务（基于 v_fault_analysis 视图）。"""

    @staticmethod
    def model_fault_rate(
        start_date: str | None = None,
        end_date: str | None = None,
        bill_type: str | None = None,
        fault_type_cd: str | None = None,
    ) -> list[dict[str, Any]]:
        """型号故障率：按设备物料编码统计故障次数。"""
        return FaultAnalysisRepository.model_fault_rate(
            {
                "start_date": start_date,
                "end_date": end_date,
                "bill_type": bill_type,
                "fault_type_cd": fault_type_cd,
            }
        )

    @staticmethod
    def accessory_frequency(
        start_date: str | None = None,
        end_date: str | None = None,
        fault_type_cd: str | None = None,
    ) -> list[dict[str, Any]]:
        """配件更换频次：按 TIT25 itemcd 统计更换次数。"""
        return FaultAnalysisRepository.accessory_frequency(
            {"start_date": start_date, "end_date": end_date, "fault_type_cd": fault_type_cd}
        )

    @staticmethod
    def repair_duration(
        start_date: str | None = None,
        end_date: str | None = None,
        bill_type: str | None = None,
        fault_type_cd: str | None = None,
    ) -> list[dict[str, Any]]:
        """修复时长分析：按单据类型统计平均/中位/最大修复时长。"""
        return FaultAnalysisRepository.repair_duration(
            {
                "start_date": start_date,
                "end_date": end_date,
                "bill_type": bill_type,
                "fault_type_cd": fault_type_cd,
            }
        )
