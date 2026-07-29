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


class TestResolveEntitlementLevel0:
    """0级：人为损坏判定（最高优先）。"""

    def test_damage_type_2_charge(self, app: Flask) -> None:
        """damage_type='2' 人为损坏 → 一律收费。"""
        eid = _make_eid(asset_owner=OW_COMMERCIAL)
        rl = _make_rl(business_mode="02")
        result = resolve_entitlement(eid, rl, damage_type='2')
        assert result.free is False
        assert result.reason == "人为损坏"

    def test_damage_type_2_overrides_rental(self, app: Flask) -> None:
        """人为损坏覆盖租赁免费规则。"""
        eid = _make_eid(asset_owner=OW_COMMERCIAL)
        rl = _make_rl(business_mode="02")
        result = resolve_entitlement(eid, rl, damage_type='2')
        assert result.free is False  # 人为>租赁

    def test_damage_type_1_normal_flow(self, app: Flask) -> None:
        """damage_type='1' 非人为 → 走正常流程。"""
        eid = _make_eid(asset_owner=OW_COMMERCIAL)
        rl = _make_rl(business_mode="02")
        result = resolve_entitlement(eid, rl, damage_type='1')
        assert result.free is True  # 非人为租赁免费

    def test_damage_type_none_normal_flow(self, app: Flask) -> None:
        """damage_type=None → 走正常流程。"""
        eid = _make_eid(asset_owner=OW_COMMERCIAL)
        rl = _make_rl(business_mode="02")
        result = resolve_entitlement(eid, rl)
        assert result.free is True


class TestResolveEntitlementLevel1:
    """1级：特殊客户协议（P2 接入 SpecialAgreement 表）。"""

    def test_level1_free_agreement(self, app: Flask) -> None:
        """有效特殊协议 is_free='1' → 免费。"""
        from datetime import date, timedelta

        from app.extensions import db
        from app.models.entitlement import SpecialAgreement

        with app.app_context():
            db.session.query(SpecialAgreement).delete()
            db.session.add(SpecialAgreement(
                agreement_id="AG001",
                cust_cd="CUST001",
                agreement_nm="VIP免费协议",
                is_free="1",
                effective_date=date.today() - timedelta(days=10),
                expire_date=date.today() + timedelta(days=10),
                useflg="1",
            ))
            db.session.commit()

            eid = _make_eid(asset_owner=OW_CUSTOMER)
            rl = _make_rl(business_mode="01", cust_cd="CUST001")
            result = resolve_entitlement(eid, rl)
            assert result.free is True
            assert "特殊协议" in result.reason

    def test_level1_expired_agreement_skipped(self, app: Flask) -> None:
        """过期协议不生效，走后续优先级。"""
        from datetime import date, timedelta

        from app.extensions import db
        from app.models.entitlement import SpecialAgreement

        with app.app_context():
            db.session.query(SpecialAgreement).delete()
            db.session.add(SpecialAgreement(
                agreement_id="AG002",
                cust_cd="CUST001",
                agreement_nm="过期协议",
                is_free="1",
                effective_date=date.today() - timedelta(days=20),
                expire_date=date.today() - timedelta(days=5),
                useflg="1",
            ))
            db.session.commit()

            eid = _make_eid(asset_owner=OW_CUSTOMER)
            rl = _make_rl(business_mode="01", cust_cd="CUST001")
            result = resolve_entitlement(eid, rl)
            assert "特殊协议" not in result.reason

    def test_level1_charge_agreement(self, app: Flask) -> None:
        """is_free='0' 协议 → 收费。"""
        from datetime import date, timedelta

        from app.extensions import db
        from app.models.entitlement import SpecialAgreement

        with app.app_context():
            db.session.query(SpecialAgreement).delete()
            db.session.add(SpecialAgreement(
                agreement_id="AG003",
                cust_cd="CUST001",
                agreement_nm="收费协议",
                is_free="0",
                effective_date=date.today() - timedelta(days=10),
                expire_date=date.today() + timedelta(days=10),
                useflg="1",
            ))
            db.session.commit()

            eid = _make_eid(asset_owner=OW_CUSTOMER)
            rl = _make_rl(business_mode="01", cust_cd="CUST001")
            result = resolve_entitlement(eid, rl)
            assert result.free is False
            assert "特殊协议" in result.reason


class TestResolveEntitlementLevel2:
    """2级：维保合同（P2 接入 ServiceContract 表）。"""

    def test_level2_free_contract_by_eid(self, app: Flask) -> None:
        """按 eid 匹配维保合同 is_free='1' → 免费。"""
        from datetime import date, timedelta

        from app.extensions import db
        from app.models.entitlement import ServiceContract

        with app.app_context():
            db.session.query(ServiceContract).delete()
            db.session.add(ServiceContract(
                contract_id="CT001",
                contract_no="HT2026001",
                cust_cd="CUST001",
                eid="EIDTEST001",
                contract_nm="设备维保合同",
                is_free="1",
                effective_date=date.today() - timedelta(days=10),
                expire_date=date.today() + timedelta(days=10),
                useflg="1",
            ))
            db.session.commit()

            eid = _make_eid(asset_owner=OW_CUSTOMER, eid="EIDTEST001")
            rl = _make_rl(business_mode="01", cust_cd="CUST001")
            result = resolve_entitlement(eid, rl)
            assert result.free is True
            assert "维保合同" in result.reason

    def test_level2_contract_fallback_to_cust_cd(self, app: Flask) -> None:
        """eid 无匹配时按 cust_cd 兜底。"""
        from datetime import date, timedelta

        from app.extensions import db
        from app.models.entitlement import ServiceContract

        with app.app_context():
            db.session.query(ServiceContract).delete()
            db.session.add(ServiceContract(
                contract_id="CT002",
                contract_no="HT2026002",
                cust_cd="CUST002",
                eid=None,
                contract_nm="客户维保合同",
                is_free="1",
                effective_date=date.today() - timedelta(days=10),
                expire_date=date.today() + timedelta(days=10),
                useflg="1",
            ))
            db.session.commit()

            eid = _make_eid(asset_owner=OW_CUSTOMER, eid="EIDNOCONTRACT")
            rl = _make_rl(business_mode="01", cust_cd="CUST002")
            result = resolve_entitlement(eid, rl)
            assert result.free is True
            assert "维保合同" in result.reason

    def test_level2_expired_contract_skipped(self, app: Flask) -> None:
        """过期合同不生效。"""
        from datetime import date, timedelta

        from app.extensions import db
        from app.models.entitlement import ServiceContract

        with app.app_context():
            db.session.query(ServiceContract).delete()
            db.session.add(ServiceContract(
                contract_id="CT003",
                cust_cd="CUST001",
                eid="EIDTEST001",
                contract_nm="过期合同",
                is_free="1",
                effective_date=date.today() - timedelta(days=20),
                expire_date=date.today() - timedelta(days=5),
                useflg="1",
            ))
            db.session.commit()

            eid = _make_eid(asset_owner=OW_CUSTOMER, eid="EIDTEST001")
            rl = _make_rl(business_mode="01", cust_cd="CUST001")
            result = resolve_entitlement(eid, rl)
            assert "维保合同" not in result.reason


class TestResolveEntitlementLevel3:
    """3级：代维按合同 + 租赁/借用/免费投放/合作运营免费。"""

    def test_level3_contract_maintenance_charge(self, app: Flask) -> None:
        """代维 business_mode='04' → 按合同，1a 阶段无合同默认收费。"""
        eid = _make_eid(asset_owner=OW_COMMERCIAL)
        rl = _make_rl(business_mode="04")
        result = resolve_entitlement(eid, rl)
        assert result.free is False
        assert "代维" in result.reason

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

    def test_haisheng_returns_contract(self, app: Flask) -> None:
        """海晟设备 → '03' 代维。"""
        eid = _make_eid(asset_owner=OW_HAISHENG)
        assert resolve_service_responsibility(eid) == SR_CONTRACTOR

    def test_commercial_returns_internal(self, app: Flask) -> None:
        """商用电子 → '01' 内部。"""
        eid = _make_eid(asset_owner=OW_COMMERCIAL)
        assert resolve_service_responsibility(eid) == SR_INTERNAL

    def test_customer_returns_internal(self, app: Flask) -> None:
        """门店资产 → '01' 内部。"""
        eid = _make_eid(asset_owner=OW_CUSTOMER)
        assert resolve_service_responsibility(eid) == SR_INTERNAL

    def test_in_warranty_still_internal(self, app: Flask) -> None:
        """保内设备仍是内部维护（商用电子我们自己修，不是厂商修）。"""
        eid = _make_eid(
            asset_owner=OW_COMMERCIAL,
            warranty_expire=datetime.now() + timedelta(days=30),
        )
        assert resolve_service_responsibility(eid) == SR_INTERNAL

    def test_no_warranty_expire_returns_internal(self, app: Flask) -> None:
        """无 warranty_expire → '01' 内部。"""
        eid = _make_eid(asset_owner=OW_COMMERCIAL, warranty_expire=None)
        assert resolve_service_responsibility(eid) == SR_INTERNAL


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
