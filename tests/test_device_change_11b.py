"""11b 测试：plantyp=10 DeviceChangeService BG 子类型写 type='T' + rl 转移 + 回写。

验证：
- BG 子类型关单（to_status=5）时：
  1. 写 tmm43_eid_track type='T'（客户转移，A 客户→B 客户）
  2. 旧门店 rl 失效（useflg=0, asset_status=RETURNED）
  3. 新门店 rl 新建（useflg=1, asset_status=ACTIVE）
  4. 回写 plan_status='01'
- CK/BQ 子类型关单时：只回写 plan_status='01'，不写 EidTrack，不转移 rl
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask

from app.extensions import db
from app.models.itsm import DeviceChange
from app.models.master import CustPosRl, Customer, Eid, EidTrack
from app.models.sales import PlanCust
from app.repositories.itsm_repository import DeviceChangeRepository
from app.services.itsm_service import DeviceChangeService


def _seed_customer(cust_cd: str, cust_card: str) -> Customer:
    """创建测试客户。"""
    record = Customer(
        cust_cd=cust_cd,
        cust_nm=f"测试客户{cust_cd}",
        cust_card=cust_card,
        useflg="1",
        customer_status="ACTIVE",
    )
    db.session.add(record)
    return record


def _seed_eid(eid: str, itemcd: str = "IT0001") -> Eid:
    """创建测试 EID。"""
    record = Eid(
        itemcd=itemcd,
        eid=eid,
        opercd="T00001",
        gendate=datetime.now(UTC),
        useflg="1",
        sflg="1",
    )
    db.session.add(record)
    return record


def _seed_rl(cust_cd: str, eid: str, itemcd: str = "IT0001") -> CustPosRl:
    """创建测试 CustPosRl。"""
    record = CustPosRl(
        cust_cd=cust_cd,
        eid=eid,
        item_cd=itemcd,
        useflg="1",
        posupddate=datetime.now(UTC),
        asset_status="ACTIVE",
        created_from="MAINTENANCE_OPEN",
    )
    db.session.add(record)
    return record


def _seed_plan(planno: str, imple_billid: str) -> PlanCust:
    """创建测试预计划（plan_status='04' 实施中）。"""
    record = PlanCust(
        planno=planno,
        plantyp="10",
        custnew="N",
        custcard="CARD001",
        custcd="CUST001",
        imple_billid=imple_billid,
        plan_status="04",
        opercd="T00001",
        gendate=datetime.now(UTC),
    )
    db.session.add(record)
    return record


def _seed_device_change(
    change_type: str,
    store_id: str = "CUST001",
    new_store_id: str = "CUST002",
    device_id: str = "EIDBG00000001",
) -> DeviceChange:
    """创建测试设备变更单。"""
    record = DeviceChangeRepository.create(
        {
            "store_id": store_id,
            "change_type": change_type,
            "device_id": device_id,
            "new_store_id": new_store_id if change_type == "BG" else "",
            "new_store_card": "CARD003" if change_type in ("CK", "BG") else "",
        },
        "T00001",
    )
    return record


def _transition_to_5(svc: DeviceChangeService, change_id: str) -> None:
    """执行 1→2→5 状态流转。"""
    svc.transition(change_id, "2", "T00001")
    svc.transition(change_id, "5", "T00001")


def _cleanup() -> None:
    """清理测试数据。"""
    db.session.query(EidTrack).filter(EidTrack.eid.like("EIDBG%")).delete(synchronize_session=False)
    db.session.query(CustPosRl).filter(CustPosRl.eid.like("EIDBG%")).delete(synchronize_session=False)
    db.session.query(PlanCust).filter(PlanCust.planno.like("PLBG%")).delete(synchronize_session=False)
    db.session.query(DeviceChange).filter(DeviceChange.device_id.like("EIDBG%")).delete(synchronize_session=False)
    db.session.query(Eid).filter(Eid.eid.like("EIDBG%")).delete(synchronize_session=False)
    db.session.query(Customer).filter(Customer.cust_cd.in_(["CUST001", "CUST002"])).delete(synchronize_session=False)
    db.session.commit()


class TestDeviceChangeBG:
    """11b: BG 子类型关单写 type='T' + rl 转移 + 回写。"""

    def test_bg_close_writes_t_track_and_transfers_rl(self, app: Flask) -> None:
        """BG 关单：写 type='T' + 旧 rl 失效 + 新 rl 新建 + 回写 plan_status='01'。"""
        with app.app_context():
            _cleanup()
            _seed_customer("CUST001", "CARD001")
            _seed_customer("CUST002", "CARD002")
            _seed_eid("EIDBG00000001")
            _seed_rl("CUST001", "EIDBG00000001")

            record = _seed_device_change("BG")
            _seed_plan("PLBG000001", record.device_change_id)

            db.session.commit()

            svc = DeviceChangeService()
            _transition_to_5(svc, record.device_change_id)

            # 验证 type='T' EidTrack
            t_tracks = (
                db.session.query(EidTrack)
                .filter(EidTrack.eid == "EIDBG00000001", EidTrack.type == "T")
                .all()
            )
            assert len(t_tracks) == 1
            assert t_tracks[0].cust_cd == "CUST001"
            assert t_tracks[0].n_cust_cd == "CUST002"

            # 验证旧 rl 失效
            old_rl = (
                db.session.query(CustPosRl)
                .filter(CustPosRl.eid == "EIDBG00000001", CustPosRl.cust_cd == "CUST001")
                .first()
            )
            assert old_rl is not None
            assert old_rl.useflg == "0"
            assert old_rl.asset_status == "RETURNED"

            # 验证新 rl 新建
            new_rl = (
                db.session.query(CustPosRl)
                .filter(CustPosRl.eid == "EIDBG00000001", CustPosRl.cust_cd == "CUST002")
                .first()
            )
            assert new_rl is not None
            assert new_rl.useflg == "1"
            assert new_rl.asset_status == "ACTIVE"
            assert new_rl.created_from == "DEVICE_CHANGE"

            # 验证回写 plan_status='01'
            plan = db.session.query(PlanCust).filter(PlanCust.planno == "PLBG000001").first()
            assert plan is not None
            assert plan.plan_status == "01"

            _cleanup()

    def test_ck_close_only_writes_back_plan(self, app: Flask) -> None:
        """CK 关单：只回写 plan_status='01'，不写 EidTrack，不转移 rl。"""
        with app.app_context():
            _cleanup()
            _seed_customer("CUST001", "CARD001")
            _seed_eid("EIDBG00000002")
            _seed_rl("CUST001", "EIDBG00000002")

            record = _seed_device_change("CK", device_id="EIDBG00000002")
            _seed_plan("PLBG000002", record.device_change_id)

            db.session.commit()

            svc = DeviceChangeService()
            _transition_to_5(svc, record.device_change_id)

            # 验证无 type='T' EidTrack
            t_tracks = (
                db.session.query(EidTrack)
                .filter(EidTrack.eid == "EIDBG00000002", EidTrack.type == "T")
                .all()
            )
            assert len(t_tracks) == 0

            # 验证 rl 不变（仍为 ACTIVE）
            rl = (
                db.session.query(CustPosRl)
                .filter(CustPosRl.eid == "EIDBG00000002", CustPosRl.cust_cd == "CUST001")
                .first()
            )
            assert rl is not None
            assert rl.useflg == "1"
            assert rl.asset_status == "ACTIVE"

            # 验证回写 plan_status='01'
            plan = db.session.query(PlanCust).filter(PlanCust.planno == "PLBG000002").first()
            assert plan is not None
            assert plan.plan_status == "01"

            _cleanup()

    def test_bq_close_only_writes_back_plan(self, app: Flask) -> None:
        """BQ 关单：只回写 plan_status='01'，不写 EidTrack，不转移 rl。"""
        with app.app_context():
            _cleanup()
            _seed_customer("CUST001", "CARD001")
            _seed_eid("EIDBG00000003")
            _seed_rl("CUST001", "EIDBG00000003")

            record = _seed_device_change("BQ", device_id="EIDBG00000003")
            _seed_plan("PLBG000003", record.device_change_id)

            db.session.commit()

            svc = DeviceChangeService()
            _transition_to_5(svc, record.device_change_id)

            # 验证无 type='T' EidTrack
            t_tracks = (
                db.session.query(EidTrack)
                .filter(EidTrack.eid == "EIDBG00000003", EidTrack.type == "T")
                .all()
            )
            assert len(t_tracks) == 0

            # 验证 rl 不变
            rl = (
                db.session.query(CustPosRl)
                .filter(CustPosRl.eid == "EIDBG00000003", CustPosRl.cust_cd == "CUST001")
                .first()
            )
            assert rl is not None
            assert rl.useflg == "1"
            assert rl.asset_status == "ACTIVE"

            # 验证回写 plan_status='01'
            plan = db.session.query(PlanCust).filter(PlanCust.planno == "PLBG000003").first()
            assert plan is not None
            assert plan.plan_status == "01"

            _cleanup()
