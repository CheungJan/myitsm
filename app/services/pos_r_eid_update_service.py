# -*- coding: utf-8 -*-
"""
免费更换配置更新服务。
文件说明：编排配置更新列表查询、旧新配件查看与确认业务。
作者：Cascade
创建时间：2026-04-20

PB 对齐规则：
- 列表来源于 `d_itsm_free_replace_dt_list`，仅处理 `is_finish <> '0'` 记录。
- 确认时以旧配件中 `chooseflg='1'` 的行驱动更新 `TMM44_POS_R_EID.posid`。
- 确认成功后回写 `TIT28_FREE_REPLACE_DT.is_finish='2'`。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.repositories.pos_r_eid_update_repository import PosREidUpdateRepository

logger = logging.getLogger(__name__)


class PosREidUpdateService:
    """免费更换配置更新服务类。"""

    def __init__(self) -> None:
        self.repo = PosREidUpdateRepository()

    def list_updates(
        self,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        custcard: Optional[str] = None,
        renew_id: Optional[str] = None,
        is_finish: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询配置更新待确认列表。"""
        try:
            return self.repo.list_updates(
                begin_date=begin_date,
                end_date=end_date,
                custcard=custcard,
                renew_id=renew_id,
                is_finish=is_finish,
                page=page,
                page_size=page_size,
            )
        except Exception as exc:
            logger.error("查询配置更新列表失败: %s", exc)
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

    def get_update(
        self, renew_id: str, business_operation_id: int
    ) -> Optional[Dict[str, Any]]:
        """查询单条配置更新记录。"""
        try:
            return self.repo.get_update(renew_id, business_operation_id)
        except Exception as exc:
            logger.error("查询配置更新记录失败: %s", exc)
            return None

    def get_choices(
        self,
        renew_id: str,
        business_operation_id: int,
        old_eid: str,
        new_eid: str,
    ) -> Dict[str, Any]:
        """查询旧新配件选择明细。"""
        if not renew_id.strip():
            return {"success": False, "error": "renew_id 不能为空"}
        if business_operation_id <= 0:
            return {"success": False, "error": "business_operation_id 必须大于0"}
        if not old_eid.strip() or not new_eid.strip():
            return {"success": False, "error": "old_eid/new_eid 不能为空"}

        try:
            old_items = self.repo.list_old_choices(
                bill_id=renew_id.strip(),
                business_id=business_operation_id,
                device_id=old_eid.strip(),
            )
            new_items = self.repo.list_new_choices(
                bill_id=renew_id.strip(),
                business_id=business_operation_id,
                device_id=new_eid.strip(),
            )
            return {
                "success": True,
                "renew_id": renew_id.strip(),
                "business_operation_id": business_operation_id,
                "old_eid": old_eid.strip(),
                "new_eid": new_eid.strip(),
                "old_items": old_items,
                "new_items": new_items,
            }
        except Exception as exc:
            logger.error("查询旧新配件明细失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def confirm_update(
        self,
        renew_id: str,
        business_operation_id: int,
        old_eid: str,
        new_eid: str,
        oper_cd: str,
    ) -> Dict[str, Any]:
        """确认配置更新。"""
        if not renew_id.strip():
            return {"success": False, "error": "renew_id 不能为空"}
        if business_operation_id <= 0:
            return {"success": False, "error": "business_operation_id 必须大于0"}
        if not old_eid.strip() or not new_eid.strip():
            return {"success": False, "error": "old_eid/new_eid 不能为空"}
        if not oper_cd.strip():
            return {"success": False, "error": "oper_cd 不能为空"}

        try:
            update_record = self.repo.get_update(
                renew_id.strip(), business_operation_id
            )
            if not update_record:
                return {"success": False, "error": "配置更新记录不存在"}

            is_finish = str(update_record.get("is_finish") or "")
            if is_finish == "2":
                return {"success": False, "error": "当前记录已确认，无需重复提交"}

            result = self.repo.confirm_update(
                renew_id=renew_id.strip(),
                business_operation_id=business_operation_id,
                old_eid=old_eid.strip(),
                new_eid=new_eid.strip(),
                oper_cd=oper_cd.strip(),
            )
            return {
                "success": True,
                "renew_id": renew_id.strip(),
                "business_operation_id": business_operation_id,
                "old_eid": old_eid.strip(),
                "new_eid": new_eid.strip(),
                **result,
            }
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            logger.error("确认配置更新失败: %s", exc)
            return {"success": False, "error": str(exc)}
