# -*- coding: utf-8 -*-
"""
免责处理服务。
文件说明：编排免责处理业务逻辑，并对齐 PB 保存校验与状态规则。
作者：Cascade
创建时间：2026-04-20

PB 对齐规则：
- exemptflg='Y' 时必须填写 exceptionscd。
- 保存时按场景写入 is_finish：分配=1，处理=2。
"""

import logging
from typing import Any, Dict, List, Optional

from app.repositories.liability_repository import LiabilityRepository

logger = logging.getLogger(__name__)


class LiabilityService:
    """免责处理服务类。"""

    def __init__(self) -> None:
        self.repo = LiabilityRepository()

    def list_liabilities(
        self,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        maintenance_id: Optional[str] = None,
        exemptflg: Optional[str] = None,
        liability_type: Optional[str] = None,
        is_finish: Optional[str] = None,
        include_finished: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询免责处理列表。"""
        try:
            return self.repo.list_liabilities(
                begin_date=begin_date,
                end_date=end_date,
                maintenance_id=maintenance_id,
                exemptflg=exemptflg,
                liability_type=liability_type,
                is_finish=is_finish,
                include_finished=include_finished,
                page=page,
                page_size=page_size,
            )
        except Exception as exc:
            logger.error("查询免责处理列表失败: %s", exc)
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

    def get_liability(
        self, maintenance_id: str, liability_type: str
    ) -> Optional[Dict[str, Any]]:
        """查询免责处理详情。"""
        try:
            return self.repo.get_liability(
                maintenance_id=maintenance_id, liability_type=liability_type
            )
        except Exception as exc:
            logger.error("查询免责处理详情失败: %s", exc)
            return None

    def save_liability(
        self,
        maintenance_id: str,
        liability_type: str,
        oper_cd: str,
        scene: str,
        exceptionscd: Optional[str] = None,
        exceptionsnm: Optional[str] = None,
        deptnm: Optional[str] = None,
        assessflg: str = "N",
        exemptflg: str = "N",
        useflg: str = "1",
        setfrom: Optional[str] = None,
    ) -> Dict[str, Any]:
        """保存免责处理（分配/处理）。"""
        scene_map = {"assign": "1", "process": "2"}
        if scene not in scene_map:
            return {"success": False, "error": "scene must be 'assign' or 'process'"}

        if exemptflg == "Y" and not (exceptionscd or "").strip():
            return {"success": False, "error": "请填写免责科目后保存"}

        try:
            success = self.repo.save_liability(
                maintenance_id=maintenance_id,
                liability_type=liability_type,
                oper_cd=oper_cd,
                is_finish=scene_map[scene],
                exceptionscd=(exceptionscd or "").strip() or None,
                exceptionsnm=(exceptionsnm or "").strip() or None,
                deptnm=(deptnm or "").strip() or None,
                assessflg=assessflg,
                exemptflg=exemptflg,
                useflg=useflg,
                setfrom=(setfrom or "").strip() or None,
            )
            if not success:
                return {"success": False, "error": "保存免责处理失败"}

            return {
                "success": True,
                "maintenance_id": maintenance_id,
                "type": liability_type,
                "is_finish": scene_map[scene],
                "message": "免责处理保存成功",
            }
        except Exception as exc:
            logger.error("保存免责处理失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def audit_liabilities(
        self, maintenance_ids: List[str], oper_cd: str
    ) -> Dict[str, Any]:
        """批量审核免责处理（2->3）。"""
        if not maintenance_ids:
            return {"success": False, "error": "maintenance_ids is required"}

        try:
            affected = self.repo.batch_update_is_finish(
                maintenance_ids=maintenance_ids,
                from_is_finish="2",
                to_is_finish="3",
                oper_cd=oper_cd,
            )
            return {
                "success": True,
                "affected": affected,
                "from_is_finish": "2",
                "to_is_finish": "3",
            }
        except Exception as exc:
            logger.error("批量审核免责处理失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def list_liability_dictionary(
        self, class_code_like: Optional[str] = None
    ) -> Dict[str, Any]:
        """查询免责科目字典。"""
        try:
            items = self.repo.list_liability_dictionary(class_code_like=class_code_like)
            return {"success": True, "items": items}
        except Exception as exc:
            logger.error("查询免责科目字典失败: %s", exc)
            return {"success": False, "error": str(exc)}
