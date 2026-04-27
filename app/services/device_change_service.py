# -*- coding: utf-8 -*-
"""
设备变更单服务
文件说明：实现设备变更单全生命周期管理，包含磁卡号变更历史记录优化
作者：Cascade
创建时间：2026-04-08

优化点：
- 磁卡号变更（CK类型）时，先保存旧磁卡号到历史表，再更新主表
- 解决老系统直接删除旧记录导致的历史追溯问题

变更类型：
- CK：改磁卡号（同门店，仅磁卡号变更）
- BQ：信息变更（联系人/电话/地址变更）
- BG：设备变更（跨门店设备迁移）
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.repositories.device_change_repository import DeviceChangeRepository
from app.services.state_machine import MaintenanceState, StateMachine

logger = logging.getLogger(__name__)


class DeviceChangeService:
    """设备变更单服务类"""

    def __init__(self):
        self.repo = DeviceChangeRepository()
        self.state_machine = StateMachine()

    def create_device_change(
        self,
        device_change_id: str,
        store_id: str,
        change_type: str,
        device_id: Optional[str] = None,
        new_contactor: Optional[str] = None,
        new_tel: Optional[str] = None,
        new_address: Optional[str] = None,
        new_store_card: Optional[str] = None,
        new_store_id: Optional[str] = None,
        is_store_inside_change: str = "N",
        oper_cd: Optional[str] = None,
        remark: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        创建设备变更单
        
        初始状态为DRAFT（草稿），后续通过状态流转推进
        
        Args:
            device_change_id: 变更单ID
            store_id: 原门店ID
            change_type: 变更类型（CK/BQ/BG）
            device_id: 整机ID
            new_contactor: 变更后联系人（BQ类型用）
            new_tel: 变更后电话（BQ类型用）
            new_address: 变更后地址（BQ类型用）
            new_store_card: 变更后磁卡号（CK类型用）
            new_store_id: 变更后门店ID（BG类型用）
            is_store_inside_change: 是否店内移机
            oper_cd: 操作人
            remark: 备注
            
        Returns:
            创建结果字典
        """
        try:
            # 验证变更类型
            if change_type not in ["CK", "BQ", "BG"]:
                return {"success": False, "error": f"Invalid change_type: {change_type}. Must be CK/BQ/BG"}

            # 校验必填字段
            if change_type == "CK" and not new_store_card:
                return {"success": False, "error": "new_store_card is required for CK type"}

            # 创建变更单（状态：DRAFT）
            success = self.repo.create_device_change(
                device_change_id=device_change_id,
                store_id=store_id,
                change_type=change_type,
                device_id=device_id,
                new_contactor=new_contactor,
                new_tel=new_tel,
                new_address=new_address,
                new_store_card=new_store_card,
                new_store_id=new_store_id,
                is_store_inside_change=is_store_inside_change,
                current_status=MaintenanceState.DRAFT.value,
                oper_cd=oper_cd,
                remark=remark,
            )

            if not success:
                return {"success": False, "error": "Failed to create device change"}

            logger.info(f"设备变更单创建成功: {device_change_id}, type={change_type}")
            return {
                "success": True,
                "device_change_id": device_change_id,
                "change_type": change_type,
                "status": MaintenanceState.DRAFT.value,
                "status_name": MaintenanceState.DRAFT.display_name,
            }

        except Exception as e:
            logger.error(f"创建设备变更单失败: {e}")
            return {"success": False, "error": str(e)}

    def get_device_change(self, device_change_id: str) -> Optional[Dict[str, Any]]:
        """
        获取设备变更单详情
        
        Args:
            device_change_id: 变更单ID
            
        Returns:
            变更单详情字典
        """
        try:
            record = self.repo.get_by_id(device_change_id)
            if not record:
                return None

            # 添加状态显示名称
            status_value = record.get("current_status")
            try:
                status = MaintenanceState(status_value)
                record["status_name"] = status.display_name
                record["status_description"] = status.description
            except ValueError:
                record["status_name"] = status_value
                record["status_description"] = ""

            # 添加变更类型显示名称
            change_type = record.get("change_type")
            type_names = {"CK": "改磁卡号", "BQ": "信息变更", "BG": "设备变更"}
            record["change_type_name"] = type_names.get(change_type, change_type)

            return record

        except Exception as e:
            logger.error(f"获取设备变更单详情失败: {e}")
            return None

    def list_device_changes(
        self,
        store_id: Optional[str] = None,
        custcard: Optional[str] = None,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        device_change_id: Optional[str] = None,
        new_store_card: Optional[str] = None,
        new_tel: Optional[str] = None,
        change_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        获取设备变更单列表
        
        Args:
            store_id: 门店ID过滤
            change_type: 变更类型过滤
            status: 状态过滤
            page: 页码
            page_size: 每页数量
            
        Returns:
            分页结果字典
        """
        try:
            result = self.repo.list_device_changes(
                store_id=store_id,
                custcard=custcard,
                begin_date=begin_date,
                end_date=end_date,
                device_change_id=device_change_id,
                new_store_card=new_store_card,
                new_tel=new_tel,
                change_type=change_type,
                status=status,
                page=page,
                page_size=page_size,
            )

            # 添加状态显示名称
            for item in result["items"]:
                status_value = item.get("current_status")
                try:
                    item["status_name"] = MaintenanceState(status_value).display_name
                except ValueError:
                    item["status_name"] = status_value

            return result

        except Exception as e:
            logger.error(f"获取设备变更单列表失败: {e}")
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

    def _execute_card_change(
        self,
        device_change_id: str,
        store_id: str,
        old_card: str,
        new_card: str,
        oper_cd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        执行磁卡号变更（核心优化逻辑）
        
        流程：
        1. 保存旧磁卡号信息到历史表
        2. 更新主表磁卡号
        3. 变更单流转到完成状态
        
        Args:
            device_change_id: 变更单ID
            store_id: 门店ID
            old_card: 原磁卡号
            new_card: 新磁卡号
            oper_cd: 操作人
            
        Returns:
            执行结果
        """
        try:
            change_time = datetime.now()

            # 步骤1：创建历史记录（保存旧磁卡号）
            history_success = self.repo.create_history_record(
                store_id=store_id,
                change_type="CK",
                change_time=change_time,
                device_change_id=device_change_id,
                oper_cd=oper_cd,
                old_custcard=old_card,
                new_custcard=new_card,
                change_reason=f"设备变更单{device_change_id}磁卡号变更: {old_card} -> {new_card}",
            )

            if not history_success:
                return {"success": False, "error": "Failed to create history record"}

            # 步骤2：更新门店磁卡号
            update_success = self.repo.update_customer_card(
                store_id=store_id,
                new_card=new_card,
                oper_cd=oper_cd,
            )

            if not update_success:
                return {"success": False, "error": "Failed to update customer card"}

            logger.info(f"磁卡号变更执行成功: {old_card} -> {new_card}, store={store_id}")
            return {"success": True}

        except Exception as e:
            logger.error(f"磁卡号变更执行失败: {e}")
            return {"success": False, "error": str(e)}

    def complete_change(
        self,
        device_change_id: str,
        oper_cd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        完成设备变更单
        
        根据变更类型执行不同的完成逻辑：
        - CK（改磁卡号）：执行磁卡号变更优化流程
        - BQ（信息变更）：更新门店联系人/电话/地址
        - BG（设备变更）：跨门店设备迁移
        
        Args:
            device_change_id: 变更单ID
            oper_cd: 操作人
            
        Returns:
            执行结果
        """
        try:
            # 获取变更单信息
            change = self.repo.get_by_id(device_change_id)
            if not change:
                return {"success": False, "error": "Device change not found"}

            current_status = change.get("current_status")
            change_type = change.get("change_type")
            store_id = change.get("store_id")

            # 状态流转验证
            if current_status != MaintenanceState.IN_PROGRESS.value:
                return {
                    "success": False,
                    "error": f"Invalid status transition from {current_status} to COMPLETED",
                }

            # 执行变更逻辑
            if change_type == "CK":  # 改磁卡号
                old_card = self.repo.get_customer_info(store_id).get("custcard")
                new_card = change.get("new_store_card")

                result = self._execute_card_change(
                    device_change_id=device_change_id,
                    store_id=store_id,
                    old_card=old_card,
                    new_card=new_card,
                    oper_cd=oper_cd,
                )

                if not result["success"]:
                    return result

            elif change_type == "BQ":  # 信息变更
                # TODO: 实现信息变更逻辑
                logger.info(f"信息变更执行: store_id={store_id}")

            elif change_type == "BG":  # 设备变更
                # TODO: 实现跨门店设备迁移逻辑
                logger.info(f"设备变更执行: store_id={store_id}")

            # 更新变更单状态为已完成
            success = self.repo.update_status(
                device_change_id=device_change_id,
                old_status=MaintenanceState.IN_PROGRESS.value,
                new_status=MaintenanceState.COMPLETED.value,
                oper_cd=oper_cd,
            )

            if not success:
                return {"success": False, "error": "Status update failed, record may be modified"}

            return {
                "success": True,
                "device_change_id": device_change_id,
                "change_type": change_type,
                "from_status": MaintenanceState.IN_PROGRESS.value,
                "to_status": MaintenanceState.COMPLETED.value,
                "action_executed": change_type == "CK",  # 磁卡号变更已执行
            }

        except Exception as e:
            logger.error(f"完成设备变更单失败: {e}")
            return {"success": False, "error": str(e)}

    def transition_state(
        self,
        device_change_id: str,
        to_status: str,
        oper_cd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        通用状态流转
        
        支持的流转：
        - DRAFT -> PLANNED -> DISPATCHED -> IN_PROGRESS -> COMPLETED
        - 任意状态 -> CANCELLED
        
        Args:
            device_change_id: 变更单ID
            to_status: 目标状态
            oper_cd: 操作人
            
        Returns:
            流转结果
        """
        try:
            # 获取当前状态
            change = self.repo.get_by_id(device_change_id)
            if not change:
                return {"success": False, "error": "Device change not found"}

            from_status = change.get("current_status")

            # 状态机验证
            validation = self.state_machine.validate_transition(from_status, to_status)
            if not validation["valid"]:
                return {"success": False, "error": validation["error"]}

            # 特殊处理：流转到COMPLETED时，需要执行变更逻辑
            if to_status == MaintenanceState.COMPLETED.value:
                return self.complete_change(device_change_id, oper_cd)

            # 普通状态流转
            success = self.repo.update_status(
                device_change_id=device_change_id,
                old_status=from_status,
                new_status=to_status,
                oper_cd=oper_cd,
            )

            if not success:
                return {"success": False, "error": "Status update failed, record may be modified"}

            return {
                "success": True,
                "device_change_id": device_change_id,
                "from_status": from_status,
                "to_status": to_status,
                "from_status_name": MaintenanceState(from_status).display_name,
                "to_status_name": MaintenanceState(to_status).display_name,
            }

        except Exception as e:
            logger.error(f"状态流转失败: {e}")
            return {"success": False, "error": str(e)}

    def cancel_change(
        self,
        device_change_id: str,
        oper_cd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        取消设备变更单
        
        Args:
            device_change_id: 变更单ID
            oper_cd: 操作人
            
        Returns:
            取消结果
        """
        return self.transition_state(
            device_change_id=device_change_id,
            to_status=MaintenanceState.CANCELLED.value,
            oper_cd=oper_cd,
        )

    def get_allowed_transitions(self, device_change_id: str) -> Dict[str, Any]:
        """
        获取允许的状态流转
        
        Args:
            device_change_id: 变更单ID
            
        Returns:
            允许的流转列表
        """
        try:
            change = self.repo.get_by_id(device_change_id)
            if not change:
                return {"success": False, "error": "Device change not found"}

            current_status = change.get("current_status")
            transitions = self.state_machine.get_allowed_transitions(current_status)

            return {
                "success": True,
                "device_change_id": device_change_id,
                "current_status": current_status,
                "current_status_name": MaintenanceState(current_status).display_name,
                "allowed_transitions": transitions,
            }

        except Exception as e:
            logger.error(f"获取允许流转失败: {e}")
            return {"success": False, "error": str(e)}

    def get_store_change_history(
        self,
        store_id: str,
        change_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        获取门店变更历史
        
        Args:
            store_id: 门店ID
            change_type: 变更类型过滤
            page: 页码
            page_size: 每页数量
            
        Returns:
            历史记录列表
        """
        try:
            result = self.repo.get_history_by_store(
                store_id=store_id,
                change_type=change_type,
                page=page,
                page_size=page_size,
            )

            # 添加变更类型显示名称
            type_names = {"CK": "改磁卡号", "BQ": "信息变更", "BG": "设备变更", "INIT": "系统初始化"}
            for item in result["items"]:
                item["change_type_name"] = type_names.get(
                    item.get("change_type"), item.get("change_type")
                )

            return {"success": True, **result}

        except Exception as e:
            logger.error(f"获取门店变更历史失败: {e}")
            return {"success": False, "error": str(e)}

    def get_card_change_history(
        self,
        custcard: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        根据磁卡号查询变更历史（核心优化功能）
        
        解决老系统无法查询磁卡号历史的问题
        
        Args:
            custcard: 磁卡号（支持旧磁卡号或新磁卡号查询）
            page: 页码
            page_size: 每页数量
            
        Returns:
            历史记录列表
        """
        try:
            result = self.repo.get_history_by_card(
                custcard=custcard,
                page=page,
                page_size=page_size,
            )

            # 添加变更类型显示名称
            type_names = {"CK": "改磁卡号", "BQ": "信息变更", "BG": "设备变更", "INIT": "系统初始化"}
            for item in result["items"]:
                item["change_type_name"] = type_names.get(
                    item.get("change_type"), item.get("change_type")
                )

            return {"success": True, **result}

        except Exception as e:
            logger.error(f"获取磁卡号变更历史失败: {e}")
            return {"success": False, "error": str(e)}
