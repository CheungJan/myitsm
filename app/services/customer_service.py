"""
客户生命周期管理服务。

优化方案1（P0）：预计划创建/作废时管理客户状态（TEMP→ACTIVE→INVALID），
解决 PB 原系统中"幽灵客户"问题。
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.extensions import db
from app.models.master import Customer


class CustomerStatus(str, Enum):
    """客户生命周期状态。"""

    TEMP = "TEMP"  # 临时（预计划新建）
    PENDING = "PENDING"  # 待确认（预计划提交）
    ACTIVE = "ACTIVE"  # 正式客户（预计划完成）
    INVALID = "INVALID"  # 已作废（预计划取消）


class CustomerSourceType(str, Enum):
    """客户来源类型。"""

    PREPLAN = "PREPLAN"  # 预计划创建
    MANUAL = "MANUAL"  # 手工创建
    IMPORT = "IMPORT"  # 批量导入
    API = "API"  # API 对接


class CustomerService:
    """客户生命周期管理服务（静态方法，对齐项目风格）。"""

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    @staticmethod
    def check_card_exists(custcard: str) -> Customer | None:
        """检查磁卡号是否已被占用（返回已有客户或 None）。"""
        if not custcard:
            return None
        return (
            db.session.query(Customer)
            .filter(
                Customer.cust_card == custcard,
                Customer.useflg != "0",
            )
            .first()
        )

    @staticmethod
    def get_by_custcd(custcd: str) -> Customer | None:
        """按客户编码查询。"""
        return db.session.get(Customer, custcd)

    # ------------------------------------------------------------------
    # 生命周期流转
    # ------------------------------------------------------------------

    @staticmethod
    def create_temp_customer(
        data: dict[str, Any],
        preplan_id: str,
        creator: str,
    ) -> Customer:
        """从预计划创建临时客户（customer_status=TEMP）。

        返回创建的 Customer 实例（未 commit，由调用方统一提交）。
        """
        custcd = data.get("custcd") or ""
        # 检查是否已存在同编码客户
        existing = db.session.get(Customer, custcd) if custcd else None
        customer = existing or Customer(cust_cd=custcd)

        # 基本信息
        customer.cust_nm = data.get("custnm") or customer.cust_nm or ""
        customer.cust_card = data.get("custcard") or customer.cust_card
        customer.busi_typ = data.get("busityp") or customer.busi_typ
        customer.address = data.get("address") or customer.address
        customer.contactor = data.get("contactor") or customer.contactor
        customer.phone_no = data.get("phoneno") or customer.phone_no

        # 生命周期字段
        customer.customer_status = CustomerStatus.TEMP.value
        customer.source_type = CustomerSourceType.PREPLAN.value
        customer.preplan_id = preplan_id
        customer.useflg = "1"

        if not existing:
            db.session.add(customer)
        return customer

    @staticmethod
    def promote_to_pending(custcd: str) -> Customer | None:
        """预计划提交时：TEMP → PENDING。"""
        customer = db.session.get(Customer, custcd)
        if customer is None:
            return None
        if customer.customer_status in (
            CustomerStatus.TEMP.value,
            CustomerStatus.PENDING.value,
        ):
            customer.customer_status = CustomerStatus.PENDING.value
        return customer

    @staticmethod
    def promote_to_active(custcd: str, operator: str) -> Customer | None:
        """预计划完成时：PENDING/TEMP → ACTIVE，记录转正时间。"""
        customer = db.session.get(Customer, custcd)
        if customer is None:
            return None
        if customer.customer_status in (
            CustomerStatus.TEMP.value,
            CustomerStatus.PENDING.value,
        ):
            customer.customer_status = CustomerStatus.ACTIVE.value
            customer.verified_at = datetime.now(UTC)
        return customer

    @staticmethod
    def invalidate_customer(custcd: str, operator: str | None = None) -> Customer | None:
        """预计划作废时：TEMP/PENDING → INVALID，标记失效。"""
        customer = db.session.get(Customer, custcd)
        if customer is None:
            return None
        if customer.customer_status in (
            CustomerStatus.TEMP.value,
            CustomerStatus.PENDING.value,
        ):
            customer.customer_status = CustomerStatus.INVALID.value
            customer.useflg = "0"
        return customer

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------

    @staticmethod
    def update_customer_card(custcd: str, new_card: str) -> Customer | None:
        """同步更新客户磁卡号。"""
        customer = db.session.get(Customer, custcd)
        if customer is None:
            return None
        customer.cust_card = new_card
        return customer
