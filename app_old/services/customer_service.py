"""
客户主数据服务。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 客户生命周期管理（优化1：预计划客户生命周期）
    - 对应 base_cust.pbl 的客户管理功能
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from app.repositories.customer_repository import CustomerRepository

logger = logging.getLogger(__name__)

__all__ = ["CustomerService", "CustomerStatus"]


class CustomerStatus(Enum):
    """
    客户生命周期状态。

    状态流转：
        TEMP → PENDING → ACTIVE
        TEMP → INVALID（预计划取消）
        PENDING → INVALID
    """

    TEMP = "TEMP"  # 临时（预计划新建）
    PENDING = "PENDING"  # 待确认（预计划提交）
    ACTIVE = "ACTIVE"  # 正式客户
    INVALID = "INVALID"  # 已作废（预计划取消）
    BLACKLIST = "BLACKLIST"  # 黑名单


class CustomerSourceType(Enum):
    """客户来源类型。"""

    PREPLAN = "PREPLAN"  # 预计划
    MANUAL = "MANUAL"  # 手工录入
    IMPORT = "IMPORT"  # 批量导入
    API = "API"  # 接口同步


class CustomerService:
    """
    客户主数据业务服务。

    功能概述：
        - 客户生命周期管理（结合优化1）
        - 预计划关联客户处理
        - 客户信息维护
    """

    def __init__(self, customer_repository: CustomerRepository | None = None) -> None:
        """
        初始化服务。

        参数：
            customer_repository: 客户仓储实例，默认自动创建
        """
        self._repo = customer_repository or CustomerRepository()

    def list_customers(
        self,
        status: str | None = None,
        use_flg: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        获取客户列表。

        参数：
            status: 生命周期状态过滤
            use_flg: 有效标志过滤

        返回值：
            list[dict[str, Any]]: 客户列表
        """
        return self._repo.list_customers(status=status, use_flg=use_flg)

    def get_customer_detail(self, cust_cd: str) -> dict[str, Any] | None:
        """
        获取客户详情。

        参数：
            cust_cd: 客户代码

        返回值：
            dict[str, Any] | None: 客户详情或空
        """
        return self._repo.get_by_code(cust_cd)

    def check_card_exists(self, cust_card: str) -> dict[str, Any] | None:
        """
        检查磁卡号是否已存在。

        参数：
            cust_card: 磁卡号

        返回值：
            dict[str, Any] | None: 已存在的客户信息或空
        """
        return self._repo.get_by_card(cust_card)

    def create_temp_from_preplan(
        self,
        preplan_id: str,
        cust_info: dict[str, Any],
        oper_cd: str,
    ) -> dict[str, Any] | None:
        """
        从预计划创建临时客户（优化1核心功能）。

        流程：
            1. 生成新客户代码（8位数字）
            2. 创建客户记录，状态为 TEMP
            3. 记录来源为 PREPLAN，关联预计划号

        参数：
            preplan_id: 预计划单号
            cust_info: 客户信息
            oper_cd: 操作员代码

        返回值：
            dict[str, Any] | None: 新建客户信息或空
        """
        # 检查磁卡号是否已存在
        existing = self.check_card_exists(cust_info.get("cust_card", ""))
        if existing:
            logger.warning("磁卡号 %s 已存在，客户代码 %s", 
                         cust_info.get("cust_card"), existing.get("cust_cd"))
            return None

        cust_cd = self._repo.create_temp_from_plan(preplan_id, cust_info, oper_cd)
        if cust_cd is None:
            return None

        return self.get_customer_detail(cust_cd)

    def promote_to_active(self, cust_cd: str, oper_cd: str) -> bool:
        """
        临时客户转正（预计划执行完成时调用）。

        参数：
            cust_cd: 客户代码
            oper_cd: 操作员代码

        返回值：
            bool: 是否成功
        """
        return self._transition_status(
            cust_cd,
            CustomerStatus.TEMP.value,
            CustomerStatus.ACTIVE.value,
            oper_cd,
        )

    def mark_invalid(self, cust_cd: str, oper_cd: str) -> bool:
        """
        标记客户为无效（预计划取消时调用）。

        参数：
            cust_cd: 客户代码
            oper_cd: 操作员代码

        返回值：
            bool: 是否成功
        """
        # 获取当前客户状态
        customer = self.get_customer_detail(cust_cd)
        if customer is None:
            return False

        current_status = customer.get("customer_status", "ACTIVE")
        return self._transition_status(
            cust_cd,
            current_status,
            CustomerStatus.INVALID.value,
            oper_cd,
        )

    def update_customer_info(
        self,
        cust_cd: str,
        cust_info: dict[str, Any],
        oper_cd: str,
    ) -> bool:
        """
        更新客户信息。

        参数：
            cust_cd: 客户代码
            cust_info: 客户信息（cust_nm, address, phone_no, contactor）
            oper_cd: 操作员代码

        返回值：
            bool: 是否成功
        """
        return self._repo.update_customer(cust_cd, cust_info, oper_cd)

    def _transition_status(
        self,
        cust_cd: str,
        old_status: str,
        new_status: str,
        oper_cd: str,
    ) -> bool:
        """
        内部方法：执行状态流转。

        参数：
            cust_cd: 客户代码
            old_status: 原状态
            new_status: 新状态
            oper_cd: 操作员代码

        返回值：
            bool: 是否成功
        """
        return self._repo.transition_status(cust_cd, old_status, new_status, oper_cd)
