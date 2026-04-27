# -*- coding: utf-8 -*-
"""
旧机翻新计划（ex_gh）服务。
文件说明：编排 TSL01_EXTEND / TSL02_EXTENDDT 业务流程，并对齐 PB 送审与作废约束。
作者：Cascade
创建时间：2026-04-20

PB 对齐规则：
- 列表默认只取 sltyp='GH'。
- 送审仅允许 auditflg='0' 且 useflg='1' 的记录。
- 作废限制：仅当日单据可作废，且 auditflg!='2'。
- 作废后：主表 useflg='9'，并从 TSL10_SLBILL 回退 planqty。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.repositories.ex_gh_repository import ExGhRepository

logger = logging.getLogger(__name__)


class ExGhService:
    """旧机翻新计划服务类。"""

    def __init__(self) -> None:
        self.repo = ExGhRepository()

    def list_ex_ghs(
        self,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        custcd: Optional[str] = None,
        auditflg: Optional[str] = None,
        useflg: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询旧机翻新计划列表。"""
        try:
            return self.repo.list_ex_ghs(
                begin_date=begin_date,
                end_date=end_date,
                custcd=custcd,
                auditflg=auditflg,
                useflg=useflg,
                page=page,
                page_size=page_size,
            )
        except Exception as exc:
            logger.error("查询旧机翻新计划列表失败: %s", exc)
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

    def get_ex_gh(self, opbillid: str) -> Optional[Dict[str, Any]]:
        """查询旧机翻新计划详情。"""
        try:
            master = self.repo.get_ex_gh(opbillid)
            if not master:
                return None
            details = self.repo.list_ex_gh_details(opbillid)
            return {"master": master, "details": details}
        except Exception as exc:
            logger.error("查询旧机翻新计划详情失败: %s", exc)
            return None

    def create_ex_gh(
        self,
        opbillid: str,
        slbillid: str,
        custcd: str,
        opercd: str,
        busityp: Optional[str] = None,
        itemcd: Optional[str] = None,
        impdate: Optional[str] = None,
        traindate: Optional[str] = None,
        backup: Optional[str] = None,
    ) -> Dict[str, Any]:
        """新增旧机翻新计划主表。"""
        if not opbillid.strip():
            return {"success": False, "error": "opbillid is required"}
        if not slbillid.strip():
            return {"success": False, "error": "slbillid is required"}
        if not custcd.strip():
            return {"success": False, "error": "custcd is required"}
        if not opercd.strip():
            return {"success": False, "error": "opercd is required"}

        try:
            success = self.repo.create_ex_gh(
                opbillid=opbillid.strip(),
                slbillid=slbillid.strip(),
                custcd=custcd.strip(),
                opercd=opercd.strip(),
                busityp=(busityp or "").strip() or None,
                itemcd=(itemcd or "").strip() or None,
                impdate=(impdate or "").strip() or None,
                traindate=(traindate or "").strip() or None,
                backup=(backup or "").strip() or None,
            )
            if not success:
                return {"success": False, "error": "新增旧机翻新计划失败"}
            return {
                "success": True,
                "opbillid": opbillid.strip(),
                "message": "新增成功",
            }
        except Exception as exc:
            logger.error("新增旧机翻新计划失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def create_ex_gh_detail(
        self,
        opbillid: str,
        custcd: str,
        planqty: int,
        opercd: str,
        opqty: int = 0,
        clqty: int = 0,
        useflg: str = "0",
        impdate: Optional[str] = None,
        traindate: Optional[str] = None,
        newaddress: Optional[str] = None,
        newcustcd: Optional[str] = None,
        eid: Optional[str] = None,
        address: Optional[str] = None,
        newcustcard: Optional[str] = None,
        custcard: Optional[str] = None,
    ) -> Dict[str, Any]:
        """新增旧机翻新计划明细。"""
        if planqty <= 0:
            return {"success": False, "error": "planqty must > 0"}

        master = self.repo.get_ex_gh(opbillid)
        if not master:
            return {"success": False, "error": "ex_gh master not found"}

        try:
            success = self.repo.create_ex_gh_detail(
                opbillid=opbillid,
                custcd=custcd,
                planqty=planqty,
                opercd=opercd,
                opqty=opqty,
                clqty=clqty,
                useflg=useflg,
                impdate=(impdate or "").strip() or None,
                traindate=(traindate or "").strip() or None,
                newaddress=(newaddress or "").strip() or None,
                newcustcd=(newcustcd or "").strip() or None,
                eid=(eid or "").strip() or None,
                address=(address or "").strip() or None,
                newcustcard=(newcustcard or "").strip() or None,
                custcard=(custcard or "").strip() or None,
            )
            if not success:
                return {"success": False, "error": "新增明细失败"}
            return {"success": True, "opbillid": opbillid, "message": "新增明细成功"}
        except Exception as exc:
            logger.error("新增旧机翻新计划明细失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def submit_audit(self, opbillids: List[str], opercd: str) -> Dict[str, Any]:
        """批量送审。"""
        cleaned = [item.strip() for item in opbillids if item and item.strip()]
        if not cleaned:
            return {"success": False, "error": "opbillids is required"}
        if not opercd.strip():
            return {"success": False, "error": "opercd is required"}

        try:
            affected = self.repo.submit_audit(cleaned, opercd.strip())
            return {"success": True, "affected": affected}
        except Exception as exc:
            logger.error("批量送审旧机翻新计划失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def invalidate_ex_gh(self, opbillid: str, opercd: str) -> Dict[str, Any]:
        """作废旧机翻新计划。"""
        if not opbillid.strip():
            return {"success": False, "error": "opbillid is required"}
        if not opercd.strip():
            return {"success": False, "error": "opercd is required"}

        try:
            record = self.repo.get_ex_gh(opbillid.strip())
            if not record:
                return {"success": False, "error": "旧机翻新计划不存在"}

            if str(record.get("useflg") or "") == "9":
                return {
                    "success": False,
                    "error": "该旧机翻新订单已作废，不允许再次作废",
                }
            if str(record.get("auditflg") or "") == "2":
                return {"success": False, "error": "该单据已通过审核，您不能作废"}

            gendate = record.get("gendate")
            if gendate is None:
                return {"success": False, "error": "单据生成时间缺失，不能作废"}

            today = datetime.now().date()
            if getattr(gendate, "date", lambda: gendate)() != today:
                return {"success": False, "error": "该单据不是当日单据，您不能作废"}

            success = self.repo.invalidate_ex_gh(
                opbillid=opbillid.strip(),
                slbillid=str(record.get("slbillid") or "").strip(),
            )
            if not success:
                return {"success": False, "error": "作废失败或记录已变化，请刷新重试"}

            return {
                "success": True,
                "opbillid": opbillid.strip(),
                "message": "作废成功",
            }
        except Exception as exc:
            logger.error("作废旧机翻新计划失败: %s", exc)
            return {"success": False, "error": str(exc)}
