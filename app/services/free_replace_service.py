# -*- coding: utf-8 -*-
"""
免费更换单服务。
文件说明：实现 TIT28_FREE_REPLACE/TIT28_FREE_REPLACE_DT 业务编排与 PB 约束校验。
作者：Cascade
创建时间：2026-04-20

PB 关键约束：
- 作废前：TIT28_FREE_REPLACE_DT 存在 is_finish='1' 时禁止作废。
- 关单前：必须存在 TIT24_MAINTENANCE_RV 回访记录。
- 关单前：存在 is_finish='0' 明细时禁止关单。
- 关单时：写入 TIT27_CLOSE_BILLS。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.repositories.free_replace_repository import FreeReplaceRepository

logger = logging.getLogger(__name__)


class FreeReplaceService:
    """免费更换单服务类。"""

    def __init__(self) -> None:
        self.repo = FreeReplaceRepository()

    def list_free_replaces(
        self,
        store_id: Optional[str] = None,
        current_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询免费更换单。"""
        try:
            return self.repo.list_free_replaces(
                store_id=store_id,
                current_status=current_status,
                page=page,
                page_size=page_size,
            )
        except Exception as exc:
            logger.error("查询免费更换单列表失败: %s", exc)
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

    def get_free_replace(self, renew_id: str) -> Optional[Dict[str, Any]]:
        """查询免费更换单详情。"""
        try:
            return self.repo.get_by_id(renew_id)
        except Exception as exc:
            logger.error("查询免费更换单详情失败: %s", exc)
            return None

    def create_free_replace(
        self,
        renew_id: str,
        store_id: str,
        creator: str,
        company_id: Optional[str] = None,
        request_time: Optional[str] = None,
        request_paper_id: Optional[str] = None,
        old_device_id: Optional[str] = None,
        new_device_id: Optional[str] = None,
        deliver_no: Optional[str] = None,
        count: Optional[int] = None,
        expected_completion_time: Optional[str] = None,
        short_description: Optional[str] = None,
        detail_description: Optional[str] = None,
        current_status: str = "1",
        is_success: Optional[str] = None,
        is_old: str = "0",
        is_back: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建免费更换单主表记录。"""
        if not renew_id or not renew_id.strip():
            return {"success": False, "error": "renew_id is required"}
        if not store_id or not store_id.strip():
            return {"success": False, "error": "store_id is required"}
        if not creator or not creator.strip():
            return {"success": False, "error": "creator is required"}

        try:
            success = self.repo.create_free_replace(
                renew_id=renew_id.strip(),
                store_id=store_id.strip(),
                creator=creator.strip(),
                company_id=company_id,
                request_time=request_time,
                request_paper_id=request_paper_id,
                old_device_id=old_device_id,
                new_device_id=new_device_id,
                deliver_no=deliver_no,
                count=count,
                expected_completion_time=expected_completion_time,
                short_description=short_description,
                detail_description=detail_description,
                current_status=current_status,
                is_success=is_success,
                is_old=is_old,
                is_back=is_back,
            )
            if not success:
                return {"success": False, "error": "Failed to create free replace"}

            return {
                "success": True,
                "renew_id": renew_id.strip(),
                "message": "免费更换单新增成功",
            }
        except Exception as exc:
            logger.error("新增免费更换单失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def list_free_replace_details(self, renew_id: str) -> Dict[str, Any]:
        """查询免费更换设备明细。"""
        try:
            record = self.repo.get_by_id(renew_id)
            if not record:
                return {"success": False, "error": "Free replace not found"}

            items = self.repo.list_free_replace_details(renew_id)
            return {"success": True, "renew_id": renew_id, "items": items}
        except Exception as exc:
            logger.error("查询免费更换设备明细失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def create_free_replace_detail(
        self,
        renew_id: str,
        business_operation_id: int,
        creator: str,
        device_id: Optional[str] = None,
        new_device_id: Optional[str] = None,
        delivery_id: Optional[str] = None,
        is_finish: str = "0",
    ) -> Dict[str, Any]:
        """新增免费更换设备明细。"""
        try:
            record = self.repo.get_by_id(renew_id)
            if not record:
                return {"success": False, "error": "Free replace not found"}

            if is_finish not in {"0", "1"}:
                return {"success": False, "error": "is_finish must be '0' or '1'"}

            success = self.repo.create_free_replace_detail(
                renew_id=renew_id,
                business_operation_id=business_operation_id,
                creator=creator,
                device_id=device_id,
                new_device_id=new_device_id,
                delivery_id=delivery_id,
                is_finish=is_finish,
            )
            if not success:
                return {
                    "success": False,
                    "error": "Failed to create free replace detail",
                }

            return {
                "success": True,
                "renew_id": renew_id,
                "business_operation_id": business_operation_id,
                "is_finish": is_finish,
            }
        except Exception as exc:
            logger.error("新增免费更换设备明细失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def cancel_free_replace(self, renew_id: str, oper_cd: str) -> Dict[str, Any]:
        """作废免费更换单（对应 PB 作废约束）。"""
        try:
            record = self.repo.get_by_id(renew_id)
            if not record:
                return {"success": False, "error": "Free replace not found"}

            current_status = str(record.get("current_status") or "")
            if current_status == "9":
                return {"success": False, "error": "当前单据已作废"}
            if current_status == "3":
                return {"success": False, "error": "当前单据已关闭，不能作废"}

            submitted_count = self.repo.count_details_by_finish(renew_id, "1")
            if submitted_count > 0:
                return {
                    "success": False,
                    "error": "当前维护单存在已提交的设备更换信息,不能作废！",
                }

            updated = self.repo.update_status(
                renew_id=renew_id,
                old_status=current_status,
                new_status="9",
                updator=oper_cd,
            )
            if not updated:
                return {"success": False, "error": "状态更新失败，请刷新后重试"}

            return {
                "success": True,
                "renew_id": renew_id,
                "from_status": current_status,
                "to_status": "9",
                "message": "免费更换单作废成功",
            }
        except Exception as exc:
            logger.error("作废免费更换单失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def close_free_replace(self, renew_id: str, oper_cd: str) -> Dict[str, Any]:
        """关闭免费更换单（对应 PB 关单约束并写关单记录）。"""
        try:
            record = self.repo.get_by_id(renew_id)
            if not record:
                return {"success": False, "error": "Free replace not found"}

            current_status = str(record.get("current_status") or "")
            if current_status == "3":
                return {"success": False, "error": "当前单据已关闭"}
            if current_status == "9":
                return {"success": False, "error": "当前单据已作废，不能关闭"}

            rv_count = self.repo.count_revisit_records(renew_id)
            if rv_count < 1:
                return {"success": False, "error": "当前维护单无回访信息,不能关闭！"}

            unsubmitted_count = self.repo.count_details_by_finish(renew_id, "0")
            if unsubmitted_count > 0:
                return {
                    "success": False,
                    "error": "当前维护单有未提交的开通设备信息,不能关闭！",
                }

            close_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            business_operation_id = self.repo.next_close_business_operation_id(renew_id)

            updated = self.repo.update_status(
                renew_id=renew_id,
                old_status=current_status,
                new_status="3",
                updator=oper_cd,
                close_time=close_time,
            )
            if not updated:
                return {"success": False, "error": "状态更新失败，请刷新后重试"}

            self.repo.insert_close_bill(
                renew_id=renew_id,
                business_operation_id=business_operation_id,
                close_time=close_time,
                close_type="免费更换关闭",
                is_old=record.get("is_old"),
                creator=oper_cd,
            )

            return {
                "success": True,
                "renew_id": renew_id,
                "from_status": current_status,
                "to_status": "3",
                "business_operation_id": business_operation_id,
                "message": "免费更换单关闭成功",
            }
        except Exception as exc:
            logger.error("关闭免费更换单失败: %s", exc)
            return {"success": False, "error": str(exc)}
