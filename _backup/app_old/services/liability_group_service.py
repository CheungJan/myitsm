# -*- coding: utf-8 -*-
"""
免责分部门处理服务。
文件说明：编排分部门免责处理列表、明细与保存业务。
作者：Cascade
创建时间：2026-04-20

PB 对齐规则：
- 主列表按当前登录用户部门过滤（通过部门映射免责编码）。
- 主列表处理标志限制在 `IS_FINISH in ('1','2')`。
- 明细仅允许未审核（`IS_FINISH != '3'`）记录修改。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.repositories.liability_group_repository import LiabilityGroupRepository

logger = logging.getLogger(__name__)


class LiabilityGroupService:
    """免责分部门处理服务类。"""

    def __init__(self) -> None:
        self.repo = LiabilityGroupRepository()

    def list_liability_groups(
        self,
        user_cd: str,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        store_id: Optional[str] = None,
        maintenance_id: Optional[str] = None,
        exemptflg: str = "%",
        liability_type: str = "%",
        is_finish: str = "1",
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """查询分部门免责处理列表。"""
        if not user_cd.strip():
            return {
                "success": False,
                "error": "user_cd 不能为空",
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }

        try:
            dept_liabcd = self.repo.get_dept_liabcd_by_user(user_cd.strip())
            if not dept_liabcd:
                return {
                    "success": False,
                    "error": "当前用户未配置部门免责编码",
                    "items": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                }

            result = self.repo.list_liability_groups(
                dept_liabcd=dept_liabcd,
                begin_date=begin_date,
                end_date=end_date,
                store_id=store_id,
                maintenance_id=maintenance_id,
                exemptflg=exemptflg,
                liability_type=liability_type,
                is_finish=is_finish,
                page=page,
                page_size=page_size,
            )
            return {"success": True, "dept_liabcd": dept_liabcd, **result}
        except Exception as exc:
            logger.error("查询分部门免责列表失败: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }

    def list_details(self, maintenance_id: str, liability_type: str) -> Dict[str, Any]:
        """查询免责明细。"""
        if not maintenance_id.strip() or not liability_type.strip():
            return {
                "success": False,
                "error": "maintenance_id 和 liability_type 不能为空",
            }

        try:
            items = self.repo.list_details(
                maintenance_id.strip(), liability_type.strip()
            )
            return {"success": True, "items": items}
        except Exception as exc:
            logger.error("查询免责明细失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def save_detail(
        self,
        maintenance_id: str,
        liability_type: str,
        oper_cd: str,
        exceptionscd: Optional[str],
        exceptionsnm: Optional[str],
        deptnm: Optional[str],
        assessflg: str = "N",
        exemptflg: str = "N",
    ) -> Dict[str, Any]:
        """保存免责明细。"""
        if not maintenance_id.strip() or not liability_type.strip():
            return {
                "success": False,
                "error": "maintenance_id 和 liability_type 不能为空",
            }
        if not oper_cd.strip():
            return {"success": False, "error": "oper_cd 不能为空"}
        if exemptflg == "Y" and not (exceptionscd or "").strip():
            return {"success": False, "error": "豁免时 exceptionscd 不能为空"}

        try:
            is_finish = self.repo.get_is_finish(
                maintenance_id.strip(), liability_type.strip()
            )
            if is_finish == "3":
                return {"success": False, "error": "当前记录已审核，不能修改"}

            saved = self.repo.save_detail(
                maintenance_id=maintenance_id.strip(),
                liability_type=liability_type.strip(),
                oper_cd=oper_cd.strip(),
                exceptionscd=(exceptionscd or "").strip() or None,
                exceptionsnm=(exceptionsnm or "").strip() or None,
                deptnm=(deptnm or "").strip() or None,
                assessflg=assessflg,
                exemptflg=exemptflg,
            )
            if not saved:
                return {"success": False, "error": "保存失败"}

            return {
                "success": True,
                "maintenance_id": maintenance_id.strip(),
                "liability_type": liability_type.strip(),
                "message": "免责明细保存成功",
            }
        except Exception as exc:
            logger.error("保存免责明细失败: %s", exc)
            return {"success": False, "error": str(exc)}
