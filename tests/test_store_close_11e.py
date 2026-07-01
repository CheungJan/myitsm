"""11e 测试：plantyp=40 StoreCloseService 写 type='R' 批量 + rl 全失效 + 回写。

验证门店关闭关单（to_status=5）时：
  1. 对门店所有活跃 EID 写 tmm43_eid_track type='R'（回收），cust_cd=门店，n_cust_cd=None
  2. 门店所有活跃 tmm35_cust_pos_rl 失效（useflg=0, asset_status=RETURNED）
  3. 回写 plan_status='01'（仅当当前='04'）
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask

from app.extensions import db
from app.models.itsm import StoreClose
from app.models.master import CustPosRl, Customer, Eid, EidTrack
from app.models.sales import PlanCust
from app.repositories.itsm_repository import StoreCloseRepository
from app.services.itsm_service import StoreCloseService


def _seed_customer(cust_cd: str, cust_card: str) -> Customer:
    """创建测试客户（已存在则复用）。"""
    existing = db.session.get(Customer, cust_cd)
    if existing:
        return existing
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
    """创建测试 EID（已存在则复用）。"""
    existing = (
        db.session.query(Eid).filter(Eid.eid == eid).first()
    )
    if existing:
        return existing
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
    """创建测试预计划（plantyp=40，plan_status='04' 实施中）。"""
    record = PlanCust(
        planno=planno,
        plantyp="40",
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


def _seed_store_close(store_id: str = "CUST001") -> StoreClose:
    """创建测试门店关闭单。"""
    record = StoreCloseRepository.create(
        {
            "store_id": store_id,
            "close_type": "01",
        },
        "T00001",
    )
    return record


def _transition_to_5(svc: StoreCloseService, close_id: str) -> None:
    """执行 1→2→5 状态流转。"""
    svc.transition(close_id, "2", "T00001")
    svc.transition(close_id, "5", "T00001")


class TestStoreClose11e:
    """11e 门店关闭关单写 EidTrack + rl 全失效 + 回写计划。"""

    def test_store_close_writes_r_tracks_and_invalidates_all_rl(self, app: Flask) -> None:
        """门店关闭关单：所有活跃 EID 写 type='R'，rl 全失效，回写 plan_status='01'。"""
        with app.app_context():
            _seed_customer("CUST001", "CARD001")
            _seed_eid("EIDCL0000001")
            _seed_eid("EIDCL0000002")
            _seed_eid("EIDCL0000003")
            _seed_rl("CUST001", "EIDCL0000001")
            _seed_rl("CUST001", "EIDCL0000002")
            _seed_rl("CUST001", "EIDCL0000003")
            close = _seed_store_close()
            _seed_plan("PL000011", close.store_close_id)
            db.session.commit()

            svc = StoreCloseService()
            _transition_to_5(svc, close.store_close_id)

            # 校验 EidTrack：3 个 EID 各写 1 条 R
            tracks = (
                db.session.query(EidTrack)
                .filter(
                    EidTrack.eid.in_([
                        "EIDCL0000001", "EIDCL0000002", "EIDCL0000003"
                    ]),
                    EidTrack.type == "R",
                )
                .all()
            )
            assert len(tracks) == 3, f"应写 3 条 R 记录，实际 {len(tracks)}"
            for t in tracks:
                assert t.cust_cd == "CUST001"
                assert t.n_cust_cd in (None, "")

            # 校验 rl：全部失效
            active_rls = (
                db.session.query(CustPosRl)
                .filter(
                    CustPosRl.cust_cd == "CUST001",
                    CustPosRl.useflg == "1",
                )
                .all()
            )
            assert len(active_rls) == 0, f"应无活跃 rl，实际 {len(active_rls)}"

            # 校验回写 plan_status='01'
            plan = db.session.get(PlanCust, "PL000011")
            assert plan.plan_status == "01"

    def test_store_close_no_plan_no_writeback(self, app: Flask) -> None:
        """无关联预计划时，关单仍写 EidTrack + rl 失效，但不回写计划。"""
        with app.app_context():
            _seed_customer("CUST002", "CARD002")
            _seed_eid("EIDCL0000004")
            _seed_rl("CUST002", "EIDCL0000004")
            close = _seed_store_close(store_id="CUST002")
            db.session.commit()

            svc = StoreCloseService()
            _transition_to_5(svc, close.store_close_id)

            # 仍写 EidTrack
            tracks = (
                db.session.query(EidTrack)
                .filter(
                    EidTrack.eid == "EIDCL0000004",
                    EidTrack.type == "R",
                )
                .all()
            )
            assert len(tracks) == 1
            # 仍失效 rl
            active_rl = (
                db.session.query(CustPosRl)
                .filter(
                    CustPosRl.eid == "EIDCL0000004",
                    CustPosRl.useflg == "1",
                )
                .first()
            )
            assert active_rl is None

    def test_store_close_plan_not_04_no_writeback(self, app: Flask) -> None:
        """预计划 plan_status != '04' 时，不回写计划状态。"""
        with app.app_context():
            _seed_customer("CUST003", "CARD003")
            _seed_eid("EIDCL0000005")
            _seed_rl("CUST003", "EIDCL0000005")
            close = _seed_store_close(store_id="CUST003")
            plan = PlanCust(
                planno="PL000013",
                plantyp="40",
                custnew="N",
                custcard="CARD003",
                custcd="CUST003",
                imple_billid=close.store_close_id,
                plan_status="01",
                opercd="T00001",
                gendate=datetime.now(UTC),
            )
            db.session.add(plan)
            db.session.commit()

            svc = StoreCloseService()
            _transition_to_5(svc, close.store_close_id)

            plan = db.session.get(PlanCust, "PL000013")
            assert plan.plan_status == "01"  # 未被回写
