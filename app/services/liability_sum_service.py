# -*- coding: utf-8 -*-
"""
免责汇总服务。
文件说明：编排免责汇总列表、明细与批量审核业务。
作者：Cascade
创建时间：2026-04-20

PB 对齐规则：
- 汇总检索默认使用 `TIT10_MAINTENANCEDAY + TIT10_MAINTENANCE_LIABILITY` 联查。
- 审核动作仅处理已勾选且未审核完成的数据，审核后 `IS_FINISH='3'`。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.repositories.liability_sum_repository import LiabilitySumRepository

logger = logging.getLogger(__name__)


class LiabilitySumService:
    """免责汇总服务类。"""

    def __init__(self) -> None:
        self.repo = LiabilitySumRepository()

    def list_liability_summaries(
        self,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        store_id: Optional[str] = None,
        maintenance_id: Optional[str] = None,
        deptnm: Optional[str] = None,
        exemptflg: Optional[str] = None,
        liability_type: Optional[str] = None,
        is_finish: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """查询免责汇总列表。"""
        try:
            return self.repo.list_liability_summaries(
                begin_date=begin_date,
                end_date=end_date,
                store_id=store_id,
                maintenance_id=maintenance_id,
                deptnm=deptnm,
                exemptflg=exemptflg,
                liability_type=liability_type,
                is_finish=is_finish,
                page=page,
                page_size=page_size,
            )
        except Exception as exc:
            logger.error("查询免责汇总列表失败: %s", exc)
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

    def list_liability_details(
        self, maintenance_id: str, liability_type: str
    ) -> Dict[str, Any]:
        """查询免责汇总明细。"""
        if not maintenance_id.strip() or not liability_type.strip():
            return {
                "success": False,
                "error": "maintenance_id 和 liability_type 不能为空",
            }

        try:
            items = self.repo.list_liability_details(
                maintenance_id=maintenance_id.strip(),
                liability_type=liability_type.strip(),
            )
            return {"success": True, "items": items}
        except Exception as exc:
            logger.error("查询免责汇总明细失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def batch_audit(
        self, records: List[Dict[str, str]], oper_cd: str
    ) -> Dict[str, Any]:
        """批量审核免责汇总。"""
        if not records:
            return {"success": False, "error": "records is required"}
        if not (oper_cd or "").strip():
            return {"success": False, "error": "oper_cd is required"}

        valid_records: List[Dict[str, str]] = []
        for record in records:
            maintenance_id = str(record.get("maintenance_id") or "").strip()
            liability_type = str(record.get("liability_type") or "").strip()
            if not maintenance_id or not liability_type:
                continue
            valid_records.append(
                {
                    "maintenance_id": maintenance_id,
                    "liability_type": liability_type,
                }
            )

        if not valid_records:
            return {"success": False, "error": "no valid records"}

        try:
            affected = self.repo.batch_audit(valid_records, oper_cd=oper_cd.strip())
            return {
                "success": True,
                "affected": affected,
                "requested": len(valid_records),
                "message": "免责汇总审核完成",
            }
        except Exception as exc:
            logger.error("批量审核免责汇总失败: %s", exc)
            return {"success": False, "error": str(exc)}
