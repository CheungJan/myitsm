"""V1 测试：resolve_entitlement() + resolve_service_responsibility() 单元测试。

验证 1a 阶段服务权益判定 6 级优先级 + SR 默认推导。
对齐文档 §3.5.4 和 1a阶段实施计划.md V1。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

from flask import Flask

from app.services.entitlement_service import (
    Entitlement,
    OW_COMMERCIAL,
    OW_CUSTOMER,
    OW_HAISHENG,
    OW_TONGFANG_INFO,
    SR_CONTRACTOR,
    SR_INTERNAL,
    SR_MANUFACTURER,
    resolve_entitlement,
    resolve_old_part_disposal,
    resolve_service_responsibility,
)


def _make_eid(
    asset_owner: str | None = None,
    warranty_expire: datetime | None = None,
    eid: str = "EIDTEST001",
) -> SimpleNamespace:
    """构造内存 Eid 对象（不查数据库）。"""
    return SimpleNamespace(
        eid=eid,
        asset_owner=asset_owner,
        warranty_expire=warranty_expire,
    )


def _make_rl(business_mode: str | None = None, cust_cd: str = "CUST001") -> SimpleNamespace:
    """构造内存 CustPosRl 对象。"""
    return SimpleNamespace(business_mode=business_mode, cust_cd=cust_cd)


class TestResolveEntitlementLevel1:
    """1级：特殊客户协议（1a 写死返回 None）。"""

    def test_level1_stub_returns_none(self, app: Flask) -> None:
        """1a 阶段 get_special_agreement 写死返回 None，不触发免费。"""
        eid = _make_eid(asset_owner=OW_CUSTOMER)
        rl = _make_rl(business_mode="01")
        result = resolve_entitlement(eid, rl)
        # 1级 None → 走 4级 销售模式判定
        assert result.reason in ("保内", "过保")


class TestResolveEntitlementLevel2:
    """2级：维保合同（1a 写死返回 None）。"""

    def test_level2_stub_returns_none(self, app: Flask) -> None:
        """1a 阶段 get_service_contract 写死返回 None。"""
        eid = _make_eid(asset_owner=OW_CUSTOMER)
        rl = _make_rl(business_mode="01")
        result = resolve_entitlement(eid, rl)
        # 2级 None → 走 4级
        assert result.reason in ("保内", "过保")


class TestResolveEntitlementLevel3:
    """3级：租赁/借用/免费投放/合作运营免费。"""

    def test_level3_rental_free(self, app: Flask) -> None:
        """租赁 business_mode='02' → 免费。"""
        eid = _make_eid(asset_owner=OW_CUSTOMER)
        rl = _make_rl(business_mode="02")
        result = resolve_entitlement(eid, rl)
        assert result.free is True
        assert "租赁" in result.reason

    def test_level3_loan_free(self, app: Flask) -> None:
        """借用 business_mode='03' → 免费。"""
        eid = _make_eid(asset_owner=OW_CUSTOMER)
        rl = _make_rl(business_mode="03")
        result = resolve_entitlement(eid, rl)
        assert result.free is True
        assert "借用" in result.reason

    def test_level3_free_placement_free(self, app: Flask) -> None:
        """免费投放 business_mode='07' → 免费。"""
        eid = _make_eid(asset_owner=OW_CUSTOMER)
        rl = _make_rl(business_mode="07")
        result = resolve_entitlement(eid, rl)
        assert result.free is True
        assert "免费投放" in result.reason

    def test_level3_cooperation_free(self, app: Flask) -> None:
        """合作运营 business_mode='08' → 免费。"""
        eid = _make_eid(asset_owner=OW_CUSTOMER)
        rl = _make_rl(business_mode="08")
        result = resolve_entitlement(eid, rl)
        assert result.free is True
        assert "合作运营" in result.reason


class TestResolveEntitlementLevel4:
    """4级：厂家保修（销售/寄售/试用模式按保修期判定）。"""

    def test_level4_warranty_in_warranty(self, app: Flask) -> None:
        """销售保内 → 免费。"""
        eid = _make_eid(
            asset_owner=OW_CUSTOMER,
            warranty_expire=datetime.now() + timedelta(days=30),
        )
        rl = _make_rl(business_mode="01")
        result = resolve_entitlement(eid, rl)
        assert result.free is True
        assert result.reason == "保内"

    def test_level4_warranty_out_of_warranty(self, app: Flask) -> None:
        """销售过保 → 收费。"""
        eid = _make_eid(
            asset_owner=OW_CUSTOMER,
            warranty_expire=datetime.now() - timedelta(days=1),
        )
        rl = _make_rl(business_mode="01")
        result = resolve_entitlement(eid, rl)
        assert result.free is False
        assert result.reason == "过保"

    def test_level4_consignation_in_warranty(self, app: Flask) -> None:
        """寄售 business_mode='05' 保内 → 免费。"""
        eid = _make_eid(
            asset_owner=OW_CUSTOMER,
            warranty_expire=datetime.now() + timedelta(days=10),
        )
        rl = _make_rl(business_mode="05")
        result = resolve_entitlement(eid, rl)
        assert result.free is True

    def test_level4_trial_out_of_warranty(self, app: Flask) -> None:
        """试用 business_mode='06' 过保 → 收费。"""
        eid = _make_eid(
            asset_owner=OW_CUSTOMER,
            warranty_expire=datetime.now() - timedelta(days=1),
        )
        rl = _make_rl(business_mode="06")
        result = resolve_entitlement(eid, rl)
        assert result.free is False


class TestResolveEntitlementLevel5:
    """5级：Owner 默认规则（无 business_mode 时兜底）。"""

    def test_level5_owner_commercial_free(self, app: Flask) -> None:
        """商用电子 asset_owner='01' → 默认免费。"""
        eid = _make_eid(asset_owner=OW_COMMERCIAL)
        rl = _make_rl(business_mode=None)
        result = resolve_entitlement(eid, rl)
        assert result.free is True
        assert "商用电子" in result.reason

    def test_level5_owner_haisheng_charge(self, app: Flask) -> None:
        """海晟 asset_owner='04' → 默认收费。"""
        eid = _make_eid(asset_owner=OW_HAISHENG)
        rl = _make_rl(business_mode=None)
        result = resolve_entitlement(eid, rl)
        assert result.free is False
        assert "海晟" in result.reason


class TestResolveEntitlementLevel6:
    """6级：异常兜底。"""

    def test_level6_fallback_charge(self, app: Flask) -> None:
        """无 business_mode + 门店资产 → 兜底收费。"""
        eid = _make_eid(asset_owner=OW_CUSTOMER)
        rl = _make_rl(business_mode=None)
        result = resolve_entitlement(eid, rl)
        assert result.free is False
        assert "门店资产" in result.reason

    def test_level6_no_rl_charge(self, app: Flask) -> None:
        """无 cust_pos_rl + 门店资产 → 兜底收费。"""
        eid = _make_eid(asset_owner=OW_CUSTOMER)
        result = resolve_entitlement(eid, None)
        assert result.free is False


class TestResolveServiceResponsibility:
    """SR 默认推导测试。"""

    def test_in_warranty_returns_manufacturer(self, app: Flask) -> None:
        """保内设备 → '02' 厂商。"""
        eid = _make_eid(
            asset_owner=OW_CUSTOMER,
            warranty_expire=datetime.now() + timedelta(days=30),
        )
        assert resolve_service_responsibility(eid) == SR_MANUFACTURER

    def test_haisheng_returns_contract(self, app: Flask) -> None:
        """海晟设备 → '03' 代维。"""
        eid = _make_eid(asset_owner=OW_HAISHENG)
        assert resolve_service_responsibility(eid) == SR_CONTRACTOR

    def test_normal_returns_internal(self, app: Flask) -> None:
        """其他 → '01' 内部。"""
        eid = _make_eid(asset_owner=OW_CUSTOMER)
        assert resolve_service_responsibility(eid) == SR_INTERNAL

    def test_no_warranty_expire_returns_internal(self, app: Flask) -> None:
        """无 warranty_expire → '01' 内部。"""
        eid = _make_eid(asset_owner=OW_COMMERCIAL, warranty_expire=None)
        assert resolve_service_responsibility(eid) == SR_INTERNAL

    def test_haisheng_in_warranty_still_manufacturer(self, app: Flask) -> None:
        """海晟保内 → 仍走厂商（保内优先于海晟）。"""
        eid = _make_eid(
            asset_owner=OW_HAISHENG,
            warranty_expire=datetime.now() + timedelta(days=30),
        )
        assert resolve_service_responsibility(eid) == SR_MANUFACTURER


class TestResolveOldPartDisposal:
    """C6 旧件处理策略测试。"""

    def test_in_warranty_recycle(self, app: Flask) -> None:
        """保内旧件 → 入库回收。"""
        eid = _make_eid(asset_owner=OW_CUSTOMER)
        ent = Entitlement(free=True, reason="保内")
        assert resolve_old_part_disposal(eid, ent) == "recycle"

    def test_commercial_out_of_warranty_recycle(self, app: Flask) -> None:
        """过保商用电子 → 入库回收。"""
        eid = _make_eid(asset_owner=OW_COMMERCIAL)
        ent = Entitlement(free=False, reason="过保")
        assert resolve_old_part_disposal(eid, ent) == "recycle"

    def test_customer_out_of_warranty_scrap(self, app: Flask) -> None:
        """过保门店资产 → 报废。"""
        eid = _make_eid(asset_owner=OW_CUSTOMER)
        ent = Entitlement(free=False, reason="过保")
        assert resolve_old_part_disposal(eid, ent) == "scrap"

    def test_haisheng_out_of_warranty_contract(self, app: Flask) -> None:
        """过保海晟 → 按代维合同。"""
        eid = _make_eid(asset_owner=OW_HAISHENG)
        ent = Entitlement(free=False, reason="过保")
        assert resolve_old_part_disposal(eid, ent) == "contract"
