"""11d 测试：plantyp=30 RecycleTaskService 写 type='R' + rl 失效 + 回写。

验证回收任务关单（to_status=5）时：
  1. 对每个明细 asset_id 写 tmm43_eid_track type='R'（回收），cust_cd=门店，n_cust_cd=None
  2. 对每个明细 asset_id 失效 tmm35_cust_pos_rl（useflg=0, asset_status=RETURNED）
  3. 回写 plan_status='01'（仅当当前='04'）
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask

from app.extensions import db
from app.models.itsm import RecycleTask, RecycleTaskDtl
from app.models.master import CustPosRl, Customer, Eid, EidTrack
from app.models.sales import PlanCust
from app.repositories.itsm_repository import RecycleTaskRepository
from app.services.itsm_service import RecycleTaskService


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
    """创建测试预计划（plantyp=30，plan_status='04' 实施中）。"""
    record = PlanCust(
        planno=planno,
        plantyp="30",
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


def _seed_recycle_task(
    cust_cd: str = "CUST001",
    asset_ids: list[str] | None = None,
) -> RecycleTask:
    """创建测试回收任务 + 明细。"""
    record = RecycleTaskRepository.create(
        {
            "recycle_type": "30",
            "cust_cd": cust_cd,
            "plan_no": "PL000021",
            "asset_count": len(asset_ids or []),
        },
        "T00001",
    )
    for aid in asset_ids or []:
        db.session.add(RecycleTaskDtl(
            recycle_id=record.recycle_id,
            asset_id=aid,
            asset_type="POS",
        ))
    return record


def _transition_to_5(svc: RecycleTaskService, recycle_id: str) -> None:
    """执行 1→2→5 状态流转。"""
    svc.transition(recycle_id, "2", "T00001")
    svc.transition(recycle_id, "5", "T00001")


class TestRecycleTask11d:
    """11d 回收任务关单写 EidTrack + rl 失效 + 回写计划。"""

    def test_recycle_close_writes_r_track_and_invalidates_rl(self, app: Flask) -> None:
        """回收任务关单：明细 asset 写 type='R'，rl 失效，回写 plan_status='01'。"""
        with app.app_context():
            _seed_customer("CUST001", "CARD001")
            _seed_eid("EIDRCY0000001")
            _seed_eid("EIDRCY0000002")
            _seed_rl("CUST001", "EIDRCY0000001")
            _seed_rl("CUST001", "EIDRCY0000002")
            task = _seed_recycle_task(
                asset_ids=["EIDRCY0000001", "EIDRCY0000002"],
            )
            _seed_plan("PL000021", task.recycle_id)
            db.session.commit()

            svc = RecycleTaskService()
            _transition_to_5(svc, task.recycle_id)

            # 校验 EidTrack：每个 asset 写 1 条 R
            tracks = (
                db.session.query(EidTrack)
                .filter(
                    EidTrack.eid.in_(["EIDRCY0000001", "EIDRCY0000002"]),
                    EidTrack.type == "R",
                )
                .all()
            )
            assert len(tracks) == 2, f"应写 2 条 R 记录，实际 {len(tracks)}"
            for t in tracks:
                assert t.cust_cd == "CUST001"
                assert t.n_cust_cd in (None, "")

            # 校验 rl：全部失效
            rls = (
                db.session.query(CustPosRl)
                .filter(
                    CustPosRl.eid.in_(["EIDRCY0000001", "EIDRCY0000002"]),
                    CustPosRl.useflg == "1",
                )
                .all()
            )
            assert len(rls) == 0, f"应无活跃 rl，实际 {len(rls)}"

            # 校验回写 plan_status='01'
            plan = db.session.get(PlanCust, "PL000021")
            assert plan.plan_status == "01"

    def test_recycle_close_no_plan_no_writeback(self, app: Flask) -> None:
        """无关联预计划时，关单仍写 EidTrack + rl 失效，但不回写计划。"""
        with app.app_context():
            _seed_customer("CUST001", "CARD001")
            _seed_eid("EIDRCY0000003")
            _seed_rl("CUST001", "EIDRCY0000003")
            task = _seed_recycle_task(
                asset_ids=["EIDRCY0000003"],
            )
            db.session.commit()

            svc = RecycleTaskService()
            _transition_to_5(svc, task.recycle_id)

            # 仍写 EidTrack
            tracks = (
                db.session.query(EidTrack)
                .filter(
                    EidTrack.eid == "EIDRCY0000003",
                    EidTrack.type == "R",
                )
                .all()
            )
            assert len(tracks) == 1
            # 仍失效 rl
            active_rl = (
                db.session.query(CustPosRl)
                .filter(
                    CustPosRl.eid == "EIDRCY0000003",
                    CustPosRl.useflg == "1",
                )
                .first()
            )
            assert active_rl is None

    def test_recycle_close_plan_not_04_no_writeback(self, app: Flask) -> None:
        """预计划 plan_status != '04' 时，不回写计划状态。"""
        with app.app_context():
            _seed_customer("CUST001", "CARD001")
            _seed_eid("EIDRCY0000004")
            _seed_rl("CUST001", "EIDRCY0000004")
            task = _seed_recycle_task(
                asset_ids=["EIDRCY0000004"],
            )
            plan = PlanCust(
                planno="PL000024",
                plantyp="30",
                custnew="N",
                custcard="CARD001",
                custcd="CUST001",
                imple_billid=task.recycle_id,
                plan_status="01",
                opercd="T00001",
                gendate=datetime.now(UTC),
            )
            db.session.add(plan)
            db.session.commit()

            svc = RecycleTaskService()
            _transition_to_5(svc, task.recycle_id)

            plan = db.session.get(PlanCust, "PL000024")
            assert plan.plan_status == "01"  # 未被回写
