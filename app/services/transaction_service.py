"""全模块事务查询与错账更正业务服务层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.transaction_repository import (
    ErrorCorrectionRepository,
    StockSummaryRepository,
    TransactionRepository,
)


class TransactionService:
    """全模块单据统一查询服务。"""

    @staticmethod
    def list_all_bills(
        bill_type: str | None = None,
        store_id: str | None = None,
        status: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        keyword: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = TransactionRepository.list_all_bills(
            bill_type=bill_type,
            store_id=store_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            keyword=keyword,
            page=page,
            per_page=per_page,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def get_bill_types() -> list[dict[str, str]]:
        return TransactionRepository.get_bill_types()


class ErrorCorrectionService:
    """错账更正服务。

    实现"红蓝单"更正模式：
    1. 验证原单存在且可冲销
    2. 标记原单为已冲销（redflg='1'）
    3. 通过各模块的 create 接口生成更正蓝单
    """

    @staticmethod
    def reverse(
        table_name: str,
        record_id: str,
        operator: str,
    ) -> dict[str, object]:
        """执行红字冲销。"""
        # 校验表名
        if table_name not in ErrorCorrectionRepository.CORRECTABLE_TABLES:
            return {"success": False, "error": f"不支持冲销的表类型: {table_name}"}

        record = ErrorCorrectionRepository.get_record(table_name, record_id)
        if record is None:
            return {"success": False, "error": "单据不存在"}

        # 检查是否已冲销
        redflg = getattr(record, "redflg", "0")
        if redflg == "1":
            return {"success": False, "error": "该单据已被冲销"}

        # 执行冲销
        result = ErrorCorrectionRepository.mark_reversed(table_name, record_id, operator)
        if result is None:
            return {"success": False, "error": "冲销失败"}

        db.session.commit()
        return {"success": True, "data": result}


class StockSummaryService:
    """进销存汇总服务。"""

    @staticmethod
    def get_summary(
        whcd: str | None = None,
        itemtyp: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = StockSummaryRepository.get_stock_summary(
            whcd=whcd,
            itemtyp=itemtyp,
            start_date=start_date,
            end_date=end_date,
            page=page,
            per_page=per_page,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
        }
