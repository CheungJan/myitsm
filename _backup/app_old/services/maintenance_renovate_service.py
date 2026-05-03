# -*- coding: utf-8 -*-
"""
旧机翻新单服务
文件说明：实现旧机翻新单全生命周期管理，复用统一状态机
作者：Cascade
创建时间：2026-04-08

单据类型：MR（旧机翻新）
主表：TIT15_MAINTENANCE_RENOVATE
"""

import logging
from typing import Dict, List, Optional, Any

from app.repositories.maintenance_renovate_repository import MaintenanceRenovateRepository
from app.services.state_machine import MaintenanceState, StateMachine

logger = logging.getLogger(__name__)


class MaintenanceRenovateService:
    """旧机翻新单服务类"""

    def __init__(self):
        self.repo = MaintenanceRenovateRepository()
        self.state_machine = StateMachine()

    def create_maintenance_renovate(
        self,
        renovate_id: str,
        store_id: str,
        old_device_id: Optional[str] = None,
        new_device_id: Optional[str] = None,
        renovate_type: Optional[str] = None,
        oper_cd: Optional[str] = None,
        remark: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建旧机翻新单（初始状态：DRAFT）"""
        try:
            success = self.repo.create_maintenance_renovate(
                renovate_id=renovate_id,
                store_id=store_id,
                old_device_id=old_device_id,
                new_device_id=new_device_id,
                renovate_type=renovate_type,
                current_status=MaintenanceState.DRAFT.value,
                oper_cd=oper_cd,
                remark=remark,
            )

            if not success:
                return {"success": False, "error": "Failed to create maintenance renovate"}

            return {
                "success": True,
                "renovate_id": renovate_id,
                "status": MaintenanceState.DRAFT.value,
                "status_name": MaintenanceState.DRAFT.display_name,
            }

        except Exception as e:
            logger.error(f"创建旧机翻新单失败: {e}")
            return {"success": False, "error": str(e)}

    def get_maintenance_renovate(self, renovate_id: str) -> Optional[Dict[str, Any]]:
        """获取旧机翻新单详情"""
        try:
            record = self.repo.get_by_id(renovate_id)
            if not record:
                return None

            status_value = record.get("current_status")
            try:
                status = MaintenanceState(status_value)
                record["status_name"] = status.display_name
                record["status_description"] = status.description
            except ValueError:
                record["status_name"] = status_value

            return record

        except Exception as e:
            logger.error(f"获取旧机翻新单详情失败: {e}")
            return None

    def list_maintenance_renovates(
        self,
        store_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取旧机翻新单列表"""
        try:
            result = self.repo.list_maintenance_renovates(
                store_id=store_id,
                status=status,
                page=page,
                page_size=page_size,
            )

            for item in result["items"]:
                status_value = item.get("current_status")
                try:
                    item["status_name"] = MaintenanceState(status_value).display_name
                except ValueError:
                    item["status_name"] = status_value

            return result

        except Exception as e:
            logger.error(f"获取旧机翻新单列表失败: {e}")
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

    def transition_state(
        self,
        renovate_id: str,
        to_status: str,
        oper_cd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """通用状态流转"""
        try:
            record = self.repo.get_by_id(renovate_id)
            if not record:
                return {"success": False, "error": "Maintenance renovate not found"}

            from_status = record.get("current_status")

            validation = self.state_machine.validate_transition(from_status, to_status)
            if not validation["valid"]:
                return {"success": False, "error": validation["error"]}

            success = self.repo.update_status(
                renovate_id=renovate_id,
                old_status=from_status,
                new_status=to_status,
                oper_cd=oper_cd,
            )

            if not success:
                return {"success": False, "error": "Status update failed"}

            return {
                "success": True,
                "renovate_id": renovate_id,
                "from_status": from_status,
                "to_status": to_status,
                "from_status_name": MaintenanceState(from_status).display_name,
                "to_status_name": MaintenanceState(to_status).display_name,
            }

        except Exception as e:
            logger.error(f"状态流转失败: {e}")
            return {"success": False, "error": str(e)}

    def cancel_renovate(self, renovate_id: str, oper_cd: Optional[str] = None) -> Dict[str, Any]:
        """取消翻新单"""
        return self.transition_state(
            renovate_id=renovate_id,
            to_status=MaintenanceState.CANCELLED.value,
            oper_cd=oper_cd,
        )

    def get_allowed_transitions(self, renovate_id: str) -> Dict[str, Any]:
        """获取允许的状态流转"""
        try:
            record = self.repo.get_by_id(renovate_id)
            if not record:
                return {"success": False, "error": "Maintenance renovate not found"}

            current_status = record.get("current_status")
            transitions = self.state_machine.get_allowed_transitions(current_status)

            return {
                "success": True,
                "renovate_id": renovate_id,
                "current_status": current_status,
                "current_status_name": MaintenanceState(current_status).display_name,
                "allowed_transitions": transitions,
            }

        except Exception as e:
            logger.error(f"获取允许流转失败: {e}")
            return {"success": False, "error": str(e)}

    def list_equipment_renovates(self, renovate_id: str) -> Dict[str, Any]:
        """
        获取翻新设备明细（TIT15_EQUIPMENT_RENOVATE）。

        Args:
            renovate_id: 旧机翻新单ID

        Returns:
            统一结果
        """
        try:
            record = self.repo.get_by_id(renovate_id)
            if not record:
                return {"success": False, "error": "Maintenance renovate not found"}

            items = self.repo.list_equipment_renovates(renovate_id)
            return {
                "success": True,
                "renovate_id": renovate_id,
                "items": items,
            }
        except Exception as e:
            logger.error(f"获取翻新设备明细失败: {e}")
            return {"success": False, "error": str(e)}

    def create_equipment_renovate(
        self,
        renovate_id: str,
        business_operation_id: int,
        device_id: str,
        creator: str,
        new_device_id: Optional[str] = None,
        price: Optional[float] = None,
        delivery_id: Optional[str] = None,
        is_finish: str = "0",
        is_change: Optional[str] = None,
        change_eid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        新增翻新设备明细（TIT15_EQUIPMENT_RENOVATE）。

        Args:
            renovate_id: 旧机翻新单ID
            business_operation_id: 业务流水操作ID
            device_id: 旧整机ID
            creator: 创建人
            new_device_id: 新整机ID
            price: 价格
            delivery_id: 送货单号
            is_finish: 是否提交（0未提交，1已提交）
            is_change: 是否变更
            change_eid: 变更设备ID

        Returns:
            统一结果
        """
        try:
            record = self.repo.get_by_id(renovate_id)
            if not record:
                return {"success": False, "error": "Maintenance renovate not found"}

            if is_finish == "1" and (not device_id or not device_id.strip()):
                return {
                    "success": False,
                    "error": "device_id is required when is_finish=1",
                }

            success = self.repo.create_equipment_renovate(
                renovate_id=renovate_id,
                business_operation_id=business_operation_id,
                device_id=device_id,
                creator=creator,
                new_device_id=new_device_id,
                price=price,
                delivery_id=delivery_id,
                is_finish=is_finish,
                is_change=is_change,
                change_eid=change_eid,
            )
            if not success:
                return {"success": False, "error": "Failed to create equipment renovate"}

            return {
                "success": True,
                "renovate_id": renovate_id,
                "business_operation_id": business_operation_id,
                "device_id": device_id,
                "new_device_id": new_device_id,
                "is_finish": is_finish,
            }
        except Exception as e:
            logger.error(f"新增翻新设备明细失败: {e}")
            return {"success": False, "error": str(e)}
