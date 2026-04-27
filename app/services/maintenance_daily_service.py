# -*- coding: utf-8 -*-
"""
日常保养单服务
文件说明：实现日常保养单全生命周期管理，复用统一状态机
作者：Cascade
创建时间：2026-04-08

单据类型：BY（日常保养）
主表：TIT17_MAINTENANCE
"""

import logging
from typing import Dict, List, Optional, Any

from app.repositories.maintenance_daily_repository import MaintenanceDailyRepository
from app.services.state_machine import MaintenanceState, StateMachine

logger = logging.getLogger(__name__)


class MaintenanceDailyService:
    """日常保养单服务类"""

    def __init__(self):
        self.repo = MaintenanceDailyRepository()
        self.state_machine = StateMachine()

    def create_maintenance_daily(
        self,
        daily_maintenance_id: str,
        store_id: str,
        maintenance_plan_id: Optional[str] = None,
        has_video_device: str = "N",
        video_device_status: Optional[str] = None,
        maintenance_type: Optional[str] = None,
        oper_cd: Optional[str] = None,
        remark: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建日常保养单（初始状态：DRAFT）"""
        try:
            success = self.repo.create_maintenance_daily(
                daily_maintenance_id=daily_maintenance_id,
                store_id=store_id,
                maintenance_plan_id=maintenance_plan_id,
                has_video_device=has_video_device,
                video_device_status=video_device_status,
                maintenance_type=maintenance_type,
                current_status=MaintenanceState.DRAFT.value,
                oper_cd=oper_cd,
                remark=remark,
            )

            if not success:
                return {"success": False, "error": "Failed to create maintenance daily"}

            return {
                "success": True,
                "daily_maintenance_id": daily_maintenance_id,
                "status": MaintenanceState.DRAFT.value,
                "status_name": MaintenanceState.DRAFT.display_name,
            }

        except Exception as e:
            logger.error(f"创建日常保养单失败: {e}")
            return {"success": False, "error": str(e)}

    def get_maintenance_daily(self, daily_maintenance_id: str) -> Optional[Dict[str, Any]]:
        """获取日常保养单详情"""
        try:
            record = self.repo.get_by_id(daily_maintenance_id)
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
            logger.error(f"获取日常保养单详情失败: {e}")
            return None

    def list_maintenance_dailies(
        self,
        store_id: Optional[str] = None,
        status: Optional[str] = None,
        maintenance_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取日常保养单列表"""
        try:
            result = self.repo.list_maintenance_dailies(
                store_id=store_id,
                status=status,
                maintenance_type=maintenance_type,
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
            logger.error(f"获取日常保养单列表失败: {e}")
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

    def transition_state(
        self,
        daily_maintenance_id: str,
        to_status: str,
        oper_cd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """通用状态流转"""
        try:
            record = self.repo.get_by_id(daily_maintenance_id)
            if not record:
                return {"success": False, "error": "Maintenance daily not found"}

            from_status = record.get("current_status")

            validation = self.state_machine.validate_transition(from_status, to_status)
            if not validation["valid"]:
                return {"success": False, "error": validation["error"]}

            success = self.repo.update_status(
                daily_maintenance_id=daily_maintenance_id,
                old_status=from_status,
                new_status=to_status,
                oper_cd=oper_cd,
            )

            if not success:
                return {"success": False, "error": "Status update failed"}

            return {
                "success": True,
                "daily_maintenance_id": daily_maintenance_id,
                "from_status": from_status,
                "to_status": to_status,
                "from_status_name": MaintenanceState(from_status).display_name,
                "to_status_name": MaintenanceState(to_status).display_name,
            }

        except Exception as e:
            logger.error(f"状态流转失败: {e}")
            return {"success": False, "error": str(e)}

    def cancel_daily(self, daily_maintenance_id: str, oper_cd: Optional[str] = None) -> Dict[str, Any]:
        """取消保养单"""
        return self.transition_state(
            daily_maintenance_id=daily_maintenance_id,
            to_status=MaintenanceState.CANCELLED.value,
            oper_cd=oper_cd,
        )

    def get_allowed_transitions(self, daily_maintenance_id: str) -> Dict[str, Any]:
        """获取允许的状态流转"""
        try:
            record = self.repo.get_by_id(daily_maintenance_id)
            if not record:
                return {"success": False, "error": "Maintenance daily not found"}

            current_status = record.get("current_status")
            transitions = self.state_machine.get_allowed_transitions(current_status)

            return {
                "success": True,
                "daily_maintenance_id": daily_maintenance_id,
                "current_status": current_status,
                "current_status_name": MaintenanceState(current_status).display_name,
                "allowed_transitions": transitions,
            }

        except Exception as e:
            logger.error(f"获取允许流转失败: {e}")
            return {"success": False, "error": str(e)}

    def list_cust_pos_daily(self, daily_maintenance_id: str) -> Dict[str, Any]:
        """
        获取保养设备明细（TIT17_CUST_POS_DAILY）。

        Args:
            daily_maintenance_id: 日常保养单ID

        Returns:
            统一结果
        """
        try:
            record = self.repo.get_by_id(daily_maintenance_id)
            if not record:
                return {"success": False, "error": "Maintenance daily not found"}

            items = self.repo.list_cust_pos_daily(daily_maintenance_id)
            return {
                "success": True,
                "daily_maintenance_id": daily_maintenance_id,
                "items": items,
            }
        except Exception as e:
            logger.error(f"获取保养设备明细失败: {e}")
            return {"success": False, "error": str(e)}

    def create_cust_pos_daily(
        self,
        daily_maintenance_id: str,
        business_operation_id: int,
        cust_cd: str,
        eid: str,
        item_cd: str,
        typflg: str,
        creator: str,
        status: str = "1",
        start_date: Optional[str] = None,
        sys_info: Optional[str] = None,
        soft_info: Optional[str] = None,
        pos_upd_date: Optional[str] = None,
        pos_info: Optional[str] = None,
        area: Optional[str] = None,
        maintenance_date: Optional[str] = None,
        maintenance_typ: Optional[str] = None,
        request_enginner_id: Optional[str] = None,
        request_time: Optional[str] = None,
        short_description: Optional[str] = None,
        detail_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        新增保养设备明细（TIT17_CUST_POS_DAILY）。

        Returns:
            统一结果
        """
        try:
            record = self.repo.get_by_id(daily_maintenance_id)
            if not record:
                return {"success": False, "error": "Maintenance daily not found"}

            success = self.repo.create_cust_pos_daily(
                daily_maintenance_id=daily_maintenance_id,
                business_operation_id=business_operation_id,
                cust_cd=cust_cd,
                eid=eid,
                item_cd=item_cd,
                typflg=typflg,
                creator=creator,
                status=status,
                start_date=start_date,
                sys_info=sys_info,
                soft_info=soft_info,
                pos_upd_date=pos_upd_date,
                pos_info=pos_info,
                area=area,
                maintenance_date=maintenance_date,
                maintenance_typ=maintenance_typ,
                request_enginner_id=request_enginner_id,
                request_time=request_time,
                short_description=short_description,
                detail_description=detail_description,
            )
            if not success:
                return {"success": False, "error": "Failed to create cust pos daily"}

            return {
                "success": True,
                "daily_maintenance_id": daily_maintenance_id,
                "business_operation_id": business_operation_id,
                "cust_cd": cust_cd,
                "eid": eid,
                "item_cd": item_cd,
                "typflg": typflg,
            }
        except Exception as e:
            logger.error(f"新增保养设备明细失败: {e}")
            return {"success": False, "error": str(e)}
