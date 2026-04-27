# -*- coding: utf-8 -*-
"""
新机开通单服务
文件说明：实现新机开通单全生命周期管理，复用统一状态机
作者：Cascade
创建时间：2026-04-08

单据类型：MO（新机开通）
主表：TIT13_MAINTENANCE_OPEN
"""

import logging
from typing import Dict, List, Optional, Any

from app.repositories.maintenance_open_repository import MaintenanceOpenRepository
from app.services.state_machine import MaintenanceState, StateMachine

logger = logging.getLogger(__name__)


class MaintenanceOpenService:
    """新机开通单服务类"""

    def __init__(self):
        self.repo = MaintenanceOpenRepository()
        self.state_machine = StateMachine()

    def create_maintenance_open(
        self,
        new_opening_id: str,
        store_id: str,
        device_id: Optional[str] = None,
        open_type: Optional[str] = None,
        oper_cd: Optional[str] = None,
        remark: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建新机开通单（初始状态：DRAFT）"""
        try:
            success = self.repo.create_maintenance_open(
                new_opening_id=new_opening_id,
                store_id=store_id,
                device_id=device_id,
                open_type=open_type,
                current_status=MaintenanceState.DRAFT.value,
                oper_cd=oper_cd,
                remark=remark,
            )

            if not success:
                return {"success": False, "error": "Failed to create maintenance open"}

            return {
                "success": True,
                "new_opening_id": new_opening_id,
                "status": MaintenanceState.DRAFT.value,
                "status_name": MaintenanceState.DRAFT.display_name,
            }

        except Exception as e:
            logger.error(f"创建新机开通单失败: {e}")
            return {"success": False, "error": str(e)}

    def get_maintenance_open(self, new_opening_id: str) -> Optional[Dict[str, Any]]:
        """获取新机开通单详情"""
        try:
            record = self.repo.get_by_id(new_opening_id)
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
            logger.error(f"获取新机开通单详情失败: {e}")
            return None

    def list_maintenance_opens(
        self,
        store_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取新机开通单列表"""
        try:
            result = self.repo.list_maintenance_opens(
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
            logger.error(f"获取新机开通单列表失败: {e}")
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

    def transition_state(
        self,
        new_opening_id: str,
        to_status: str,
        oper_cd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """通用状态流转"""
        try:
            record = self.repo.get_by_id(new_opening_id)
            if not record:
                return {"success": False, "error": "Maintenance open not found"}

            from_status = record.get("current_status")

            # PB流程约束对齐：
            # 1) 作废前若存在已提交设备记录（IS_FINISH=1），不允许作废
            # 2) 完成前若存在未提交设备记录（IS_FINISH=0），不允许完成
            if to_status == MaintenanceState.CANCELLED.value:
                finished_count = self.repo.count_equipment_opens_by_finish(new_opening_id, "1")
                if finished_count > 0:
                    return {
                        "success": False,
                        "error": "当前开通单存在已提交的开通设备信息，不能作废",
                    }

            if to_status == MaintenanceState.COMPLETED.value:
                unfinished_count = self.repo.count_equipment_opens_by_finish(new_opening_id, "0")
                if unfinished_count > 0:
                    return {
                        "success": False,
                        "error": "当前开通单存在未提交的开通设备信息，不能完成",
                    }

            validation = self.state_machine.validate_transition(from_status, to_status)
            if not validation["valid"]:
                return {"success": False, "error": validation["error"]}

            success = self.repo.update_status(
                new_opening_id=new_opening_id,
                old_status=from_status,
                new_status=to_status,
                oper_cd=oper_cd,
            )

            if not success:
                return {"success": False, "error": "Status update failed"}

            return {
                "success": True,
                "new_opening_id": new_opening_id,
                "from_status": from_status,
                "to_status": to_status,
                "from_status_name": MaintenanceState(from_status).display_name,
                "to_status_name": MaintenanceState(to_status).display_name,
            }

        except Exception as e:
            logger.error(f"状态流转失败: {e}")
            return {"success": False, "error": str(e)}

    def cancel_open(self, new_opening_id: str, oper_cd: Optional[str] = None) -> Dict[str, Any]:
        """取消开通单"""
        return self.transition_state(
            new_opening_id=new_opening_id,
            to_status=MaintenanceState.CANCELLED.value,
            oper_cd=oper_cd,
        )

    def get_allowed_transitions(self, new_opening_id: str) -> Dict[str, Any]:
        """获取允许的状态流转"""
        try:
            record = self.repo.get_by_id(new_opening_id)
            if not record:
                return {"success": False, "error": "Maintenance open not found"}

            current_status = record.get("current_status")
            transitions = self.state_machine.get_allowed_transitions(current_status)

            return {
                "success": True,
                "new_opening_id": new_opening_id,
                "current_status": current_status,
                "current_status_name": MaintenanceState(current_status).display_name,
                "allowed_transitions": transitions,
            }

        except Exception as e:
            logger.error(f"获取允许流转失败: {e}")
            return {"success": False, "error": str(e)}

    def list_equipment_opens(self, new_opening_id: str) -> Dict[str, Any]:
        """
        获取开通设备明细（TIT14_EQUIPMENT_OPEN）。

        Args:
            new_opening_id: 新机开通单ID

        Returns:
            统一结果
        """
        try:
            record = self.repo.get_by_id(new_opening_id)
            if not record:
                return {"success": False, "error": "Maintenance open not found"}

            items = self.repo.list_equipment_opens(new_opening_id)
            return {
                "success": True,
                "new_opening_id": new_opening_id,
                "items": items,
            }
        except Exception as e:
            logger.error(f"获取开通设备明细失败: {e}")
            return {"success": False, "error": str(e)}

    def create_equipment_open(
        self,
        new_opening_id: str,
        business_operation_id: int,
        device_id: str,
        creator: str,
        price: float | None = None,
        delivery_id: str | None = None,
        is_finish: str = "0",
        is_change: str | None = None,
        change_eid: str | None = None,
        from_custcard: str | None = None,
        to_custcard: str | None = None,
        mobile_no: str | None = None,
        oper_memo: str | None = None,
        card_type: str | None = None,
        cust_id: str | None = None,
    ) -> Dict[str, Any]:
        """
        新增开通设备明细（TIT14_EQUIPMENT_OPEN）。

        PB流程对齐与优化点：
            - 子表新增前必须存在主单
            - 当 is_finish='1'（提交）时，要求 device_id 非空

        Args:
            new_opening_id: 新机开通单ID
            business_operation_id: 业务流水操作ID
            device_id: 整机ID
            creator: 创建人
            price: 价格
            delivery_id: 送货单号
            is_finish: 是否提交（0未提交，1已提交）
            is_change: 是否变更
            change_eid: 变更设备ID
            from_custcard: 迁出磁卡号
            to_custcard: 迁入磁卡号
            mobile_no: 联系电话
            oper_memo: 操作备注
            card_type: 卡类型
            cust_id: 客户ID

        Returns:
            统一结果
        """
        try:
            record = self.repo.get_by_id(new_opening_id)
            if not record:
                return {"success": False, "error": "Maintenance open not found"}

            if is_finish == "1" and (not device_id or not device_id.strip()):
                return {
                    "success": False,
                    "error": "device_id is required when is_finish=1",
                }

            success = self.repo.create_equipment_open(
                new_opening_id=new_opening_id,
                business_operation_id=business_operation_id,
                device_id=device_id,
                creator=creator,
                price=price,
                delivery_id=delivery_id,
                is_finish=is_finish,
                is_change=is_change,
                change_eid=change_eid,
                from_custcard=from_custcard,
                to_custcard=to_custcard,
                mobile_no=mobile_no,
                oper_memo=oper_memo,
                card_type=card_type,
                cust_id=cust_id,
            )
            if not success:
                return {"success": False, "error": "Failed to create equipment open"}

            return {
                "success": True,
                "new_opening_id": new_opening_id,
                "business_operation_id": business_operation_id,
                "device_id": device_id,
                "is_finish": is_finish,
            }
        except Exception as e:
            logger.error(f"新增开通设备明细失败: {e}")
            return {"success": False, "error": str(e)}
