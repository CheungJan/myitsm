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
        """从预计划创建/更新客户。

        新客户（客户表无记录）→ TEMP。
        已有正式客户（ACTIVE）→ 仅更新信息，保持 ACTIVE。
        已有临时/待确认客户 → 保持原状态。
        """
        custcd = data.get("custcd") or ""
        existing = db.session.get(Customer, custcd) if custcd else None
        is_new = existing is None
        customer = existing or Customer(cust_cd=custcd)

        # 基本信息
        customer.cust_nm = data.get("custnm") or customer.cust_nm or ""
        customer.cust_card = data.get("custcard") or customer.cust_card
        customer.busi_typ = data.get("busityp") or customer.busi_typ
        customer.address = data.get("address") or customer.address
        customer.contactor = data.get("contactor") or customer.contactor
        customer.phone_no = data.get("phoneno") or customer.phone_no

        # 生命周期字段：新客户=TEMP，已有正式客户=保持ACTIVE
        if is_new:
            customer.customer_status = CustomerStatus.TEMP.value
            customer.source_type = CustomerSourceType.PREPLAN.value
            customer.preplan_id = preplan_id
            customer.useflg = "1"
        elif customer.customer_status in (
            None, "", CustomerStatus.TEMP.value, CustomerStatus.PENDING.value
        ):
            customer.customer_status = CustomerStatus.TEMP.value
            customer.source_type = CustomerSourceType.PREPLAN.value
            customer.preplan_id = preplan_id
        # else: ACTIVE or INVALID → keep as is (existing formal customer)

        if is_new:
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

    # ------------------------------------------------------------------
    # 门店经营状态 / 数据有效性（对齐 PB usp_plan_confrim）
    # ------------------------------------------------------------------

    # 门店关闭名称前缀（与 s_status 对应，用于幂等判断）
    _CLOSE_PREFIX: dict[str, str] = {
        "3": "(永久关闭)",
        "2": "(临时关闭)",
    }

    @staticmethod
    def set_store_close_status(
        custcd: str, close_type: str | None, operator: str | None = None
    ) -> Customer | None:
        """门店关闭时设置经营状态（对齐 usp_plan_confrim 门店关闭分支）。

        close_type='YJ'（永久）→ s_status='3' + 名称前缀 '(永久关闭)'；
        其他（临时）→ s_status='2' + 名称前缀 '(临时关闭)'。
        名称前缀幂等：已加过则不重复添加。
        """
        customer = db.session.get(Customer, custcd)
        if customer is None:
            return None

        new_status = "3" if (close_type or "").strip().upper() == "YJ" else "2"
        prefix = CustomerService._CLOSE_PREFIX[new_status]

        customer.s_status = new_status
        cust_nm = customer.cust_nm or ""
        # 幂等：避免重复叠加关闭前缀（永久/临时前缀均不重复添加）
        already_prefixed = cust_nm.startswith("(永久关闭)") or cust_nm.startswith("(临时关闭)")
        if not already_prefixed:
            customer.cust_nm = f"{prefix}{cust_nm}"
        return customer

    @staticmethod
    def invalidate_store_customer(
        custcd: str, operator: str | None = None
    ) -> Customer | None:
        """客户无效化：移机/取机后空门店逻辑删除（对齐 usp_plan_confrim cust_useflg='1' 分支）。

        置 useflg='0'、pos_n=0、posstatus='03'、posstatus1='31'。
        仅对当前有效（useflg='1'）的客户生效，避免重复处理。
        """
        customer = db.session.get(Customer, custcd)
        if customer is None:
            return None
        if (customer.useflg or "") == "0":
            return customer
        customer.useflg = "0"
        customer.pos_n = 0
        customer.posstatus = "03"
        customer.posstatus1 = "31"
        return customer
