# -*- coding: utf-8 -*-
"""
资产作废审核服务。
文件说明：封装待审核作废单列表、明细、审批与作废业务。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.repositories.asset_audit_repository import AssetAuditRepository

logger = logging.getLogger(__name__)


class AssetAuditService:
    """资产作废审核服务类。"""

    def __init__(self) -> None:
        self.repo = AssetAuditRepository()

    def list_pending_audits(
        self,
        opbillid: Optional[str] = None,
        custcd: Optional[str] = None,
        custcard: Optional[str] = None,
        sltyp: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """查询待审核列表。"""
        try:
            result = self.repo.list_pending_audits(
                opbillid=(opbillid or "").strip() or None,
                custcd=(custcd or "").strip() or None,
                custcard=(custcard or "").strip() or None,
                sltyp=(sltyp or "").strip() or None,
                page=page,
                page_size=page_size,
            )
            return {"success": True, **result}
        except Exception as exc:
            logger.error("查询资产作废待审核列表失败: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }

    def list_audit_details(
        self, opbillid: str, custcd_like: str = "%"
    ) -> Dict[str, Any]:
        """查询作废单明细。"""
        if not opbillid.strip():
            return {"success": False, "error": "opbillid 不能为空"}

        try:
            items = self.repo.list_audit_details(
                opbillid=opbillid.strip(),
                custcd_like=(custcd_like or "%").strip() or "%",
            )
            return {
                "success": True,
                "items": items,
                "total": len(items),
            }
        except Exception as exc:
            logger.error("查询资产作废单明细失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def approve_audit(self, opbillid: str, custcd: str, opercd: str) -> Dict[str, Any]:
        """审批作废单。"""
        if not opbillid.strip() or not custcd.strip():
            return {"success": False, "error": "opbillid/custcd 不能为空"}
        if not opercd.strip():
            return {"success": False, "error": "opercd 不能为空"}

        try:
            ok = self.repo.approve_audit(
                opbillid=opbillid.strip(),
                custcd=custcd.strip(),
                opercd=opercd.strip(),
            )
            if not ok:
                return {"success": False, "error": "单据不存在或状态已变更"}
            return {
                "success": True,
                "opbillid": opbillid.strip(),
                "message": "审批成功",
            }
        except Exception as exc:
            logger.error("审批资产作废单失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def invalidate_audit(self, opbillid: str, opercd: str) -> Dict[str, Any]:
        """作废作废单。"""
        if not opbillid.strip():
            return {"success": False, "error": "opbillid 不能为空"}
        if not opercd.strip():
            return {"success": False, "error": "opercd 不能为空"}

        try:
            ok = self.repo.invalidate_audit(
                opbillid=opbillid.strip(), opercd=opercd.strip()
            )
            if not ok:
                return {"success": False, "error": "单据不存在或已作废"}
            return {
                "success": True,
                "opbillid": opbillid.strip(),
                "message": "作废成功",
            }
        except Exception as exc:
            logger.error("作废资产作废单失败: %s", exc)
            return {"success": False, "error": str(exc)}
