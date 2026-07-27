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

    # PB 磁卡号录入规则常量（对齐 d_plan_cust_edit.srd / w_plan_cust_befor.srw）
    CUSTCARD_MAX_LENGTH = 20  # PB DataWindow char(20) + Oracle VARCHAR2(20)
    CUSTCD_LENGTH = 8  # PB CHAR(8) 固定 8 位

    @staticmethod
    def validate_custcard(custcard: str, exclude_custcd: str | None = None) -> str | None:
        """校验磁卡号录入规则，对齐 PB w_plan_cust_befor.srw of_insert_cust。

        校验规则：
        1. 长度 ≤ 20 字符（PB DataWindow char(20)）
        2. 磁卡号在 tmm22_customers 中唯一（useflg='1'），对齐 PB 重复检查
        3. 大小写不限（PB edit.case=any）

        Args:
            custcard: 待校验磁卡号
            exclude_custcd: 排除的客户编码（更新场景排除自身）

        Returns:
            None 表示校验通过，否则返回错误信息字符串
        """
        if not custcard or not custcard.strip():
            return "磁卡号不能为空"
        if len(custcard) > CustomerService.CUSTCARD_MAX_LENGTH:
            return f"磁卡号长度不能超过 {CustomerService.CUSTCARD_MAX_LENGTH} 字符"
        # 磁卡号重复检查（对齐 PB: SELECT count(1) WHERE CUSTCARD=:ls AND USEFLG='1'）
        from sqlalchemy import func

        query = db.session.query(func.count(Customer.cust_cd)).filter(
            Customer.cust_card == custcard,
            Customer.useflg == "1",
        )
        if exclude_custcd:
            query = query.filter(Customer.cust_cd != exclude_custcd)
        if query.scalar() > 0:
            return f"磁卡号 {custcard} 已存在，请重新输入"
        return None

    @staticmethod
    def validate_custnm_unique(custnm: str, exclude_custcd: str | None = None) -> str | None:
        """校验客户名称唯一性，对齐 PB w_plan_cust_befor.srw of_insert_cust。

        PB 逻辑：SELECT count(*), max(custcd) WHERE custnm=:ls → 同名客户不允许新建。

        Args:
            custnm: 待校验客户名称
            exclude_custcd: 排除的客户编码（更新场景排除自身）

        Returns:
            None 表示校验通过，否则返回错误信息字符串（含已有 custcd）
        """
        if not custnm or not custnm.strip():
            return "客户名称不能为空"
        from sqlalchemy import func

        query = db.session.query(
            func.count(Customer.cust_cd), func.max(Customer.cust_cd)
        ).filter(Customer.cust_nm == custnm)
        if exclude_custcd:
            query = query.filter(Customer.cust_cd != exclude_custcd)
        count, existing_cd = query.one()
        if count > 0 and existing_cd:
            return f"已有此客户，请使用编码 {existing_cd}"
        return None

    @staticmethod
    def generate_custcd() -> str:
        """生成下一个客户编码（custcd）。

        对齐 PB w_plan_cust_befor_new.srw 逻辑：
            SELECT max(custcd) INTO :ls_Custcd FROM tmm22_customers;
            ls_fill = 8 - len(string(integer(ls_Custcd)+1))
            ls_Custcd = fill('0', ls_fill) + string(integer(ls_Custcd)+1)

        规则：取 tmm22_customers.cust_cd 最大值 +1，左侧补零到 8 位。
        例如 '00008397' → '00008398'。
        """
        from sqlalchemy import func

        max_custcd = (
            db.session.query(func.max(Customer.cust_cd)).scalar() or "0"
        )
        try:
            next_val = int(max_custcd) + 1
        except (ValueError, TypeError):
            next_val = 1
        return str(next_val).zfill(8)

    @staticmethod
    def create_temp_customer(
        data: dict[str, Any],
        preplan_id: str,
        creator: str,
        plantyp: str = "",
    ) -> Customer:
        """从预计划创建/更新客户。

        新客户（客户表无记录）→ TEMP。
        已有正式客户（ACTIVE）→ 仅更新信息，保持 ACTIVE。
        已有临时/待确认客户 → 保持原状态。

        custcd 为空时按 PB 规则自动生成（MAX(custcd)+1，左侧补零到 8 位），
        对齐 PB w_plan_cust_befor_new.srw 全新开通场景。

        PB 校验（仅 plantyp=00 全新开通，对齐 of_insert_cust）：
        - 磁卡号重复检查 + 长度限制（≤20 字符）
        - 客户名称重复检查

        注：plantyp=10 磁卡号变更的新磁卡号（new_custcard）校验在
        sales_service.create 中执行，因为 new_custcard 是预计划字段
        而非客户表字段。
        """
        custcd = data.get("custcd") or ""
        custcard = (data.get("custcard") or "").strip()
        custnm = (data.get("custnm") or "").strip()
        # custcd 为空时自动生成（全新开通手动输入磁卡号但未填 custcd 的场景）
        if not custcd:
            custcd = CustomerService.generate_custcd()
            data = {**data, "custcd": custcd}
        existing = db.session.get(Customer, custcd) if custcd else None
        is_new = existing is None
        customer = existing or Customer(cust_cd=custcd)

        # PB 校验仅对 plantyp=00 全新开通新客户执行（对齐 of_insert_cust:
        # if ls_plantyp <> '00' then return 1）
        if is_new and plantyp == "00":
            err = CustomerService.validate_custcard(custcard)
            if err:
                raise ValueError(err)
            err = CustomerService.validate_custnm_unique(custnm)
            if err:
                raise ValueError(err)

        # 基本信息
        customer.cust_nm = custnm or customer.cust_nm or ""
        customer.cust_card = custcard or customer.cust_card
        customer.busi_typ = data.get("busityp") or customer.busi_typ
        customer.address = data.get("address") or customer.address
        customer.contactor = data.get("contactor") or customer.contactor
        customer.phone_no = data.get("phoneno") or customer.phone_no
        customer.yun_type = data.get("yun_type") or customer.yun_type
        # PB同步字段：从plan_cust同步到tmm22_customers
        customer.class_cd = data.get("classcd") or customer.class_cd
        customer.ppt_code = data.get("pptcode") or customer.ppt_code
        customer.comm_mode = data.get("commmode") or customer.comm_mode
        customer.is_contract = data.get("is_contract") or customer.is_contract
        customer.jl_contactor = data.get("jl_contactor") or customer.jl_contactor
        customer.jl_phoneno = data.get("jl_phoneno") or customer.jl_phoneno
        customer.custrnm = data.get("custrnm") or customer.custrnm
        # 地理/负责区域/环线信息（从预计划同步到客户表）
        customer.geo_prvn_cd = data.get("geo_prvn_cd") or customer.geo_prvn_cd
        customer.geo_city_cd = data.get("geo_city_cd") or customer.geo_city_cd
        customer.geo_area_cd = data.get("geo_area_cd") or customer.geo_area_cd
        customer.geo_street_cd = data.get("geo_street_cd") or customer.geo_street_cd
        customer.area_cd = data.get("area_cd") or customer.area_cd
        customer.location = data.get("location") or customer.location

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
        """预计划作废时：TEMP/PENDING → INVALID，标记失效（保留记录以复用custcd）。"""
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

    @staticmethod
    def update_customer_fields(cust_cd: str, data: dict[str, Any]) -> None:
        """批量更新客户字段（用于预计划同步）。"""
        customer = db.session.get(Customer, cust_cd)
        if customer:
            for field, value in data.items():
                if hasattr(customer, field) and value is not None:
                    setattr(customer, field, value)

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
