"""11c 测试：plantyp=20 MaintenanceRenovateService 写 type='R'+'C' + rl 旧机失效/新机新建 + 回写。

验证翻新单关单（to_status=5）时：
  1. 旧机写 tmm43_eid_track type='R'（回收），cust_cd=门店，n_cust_cd=None
  2. 新机写 tmm43_eid_track type='C'（分配），cust_cd=None，n_cust_cd=门店
  3. 旧机 rl 失效（useflg=0, asset_status=RETURNED）
  4. 新机 rl 新建（useflg=1, asset_status=ACTIVE）
  5. 回写 plan_status='01'（仅当当前='04'）
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask

from app.extensions import db
from app.models.itsm import MaintenanceRenovate
from app.models.master import Customer, CustPosRl, Eid, EidTrack
from app.models.sales import PlanCust
from app.models.system import SysParm
from app.models.warehouse import StockIn, StockInDetail, Warehouse
from app.repositories.itsm_repository import MaintenanceRenovateRepository
from app.services.itsm_service import MaintenanceRenovateService


def _seed_customer(cust_cd: str, cust_card: str) -> Customer:
    """创建测试客户（已存在则复用，避免跨测试唯一键冲突）。"""
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
    existing = db.session.query(Eid).filter(Eid.eid == eid).first()
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
    """创建测试预计划（plantyp=20，plan_status='04' 实施中）。"""
    record = PlanCust(
        planno=planno,
        plantyp="20",
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


def _seed_renovate(
    store_id: str = "CUST001",
    old_device_id: str = "EIDOLD0000001",
    new_device_id: str = "EIDNEW0000001",
) -> MaintenanceRenovate:
    """创建测试翻新单。"""
    record = MaintenanceRenovateRepository.create(
        {
            "store_id": store_id,
            "old_device_id": old_device_id,
            "new_device_id": new_device_id,
            "count": 1,
        },
        "T00001",
    )
    return record


def _transition_to_5(svc: MaintenanceRenovateService, renew_id: str) -> None:
    """执行 1→2→5 状态流转。"""
    svc.transition(renew_id, "2", "T00001")
    svc.transition(renew_id, "5", "T00001")


class TestMaintenanceRenovate11c:
    """11c 翻新单关单写 EidTrack + rl + 回写计划。"""

    def test_renovate_close_writes_r_and_c_track_and_transfers_rl(self, app: Flask) -> None:
        """翻新单关单：旧机写 type='R'，新机写 type='C'，旧机 rl 失效，
        新机 rl 新建，回写 plan_status='01'。
        """
        with app.app_context():
            # 准备数据
            _seed_customer("CUST001", "CARD001")
            _seed_eid("EIDOLD0000001")
            _seed_eid("EIDNEW0000001")
            _seed_rl("CUST001", "EIDOLD0000001")  # 旧机已绑定到门店
            renovate = _seed_renovate()
            _seed_plan("PL000001", renovate.renew_id)
            db.session.commit()

            # 执行关单
            svc = MaintenanceRenovateService()
            _transition_to_5(svc, renovate.renew_id)

            # 校验 EidTrack（只查业务语义层 R/C 记录，排除 11a 的 i/u/d）
            tracks = (
                db.session.query(EidTrack)
                .filter(
                    EidTrack.eid.in_(["EIDOLD0000001", "EIDNEW0000001"]),
                    EidTrack.type.in_(["R", "C"]),
                )
                .order_by(EidTrack.eid, EidTrack.change_date)
                .all()
            )
            # 旧机写 R，新机写 C
            r_tracks = [t for t in tracks if t.eid == "EIDOLD0000001"]
            c_tracks = [t for t in tracks if t.eid == "EIDNEW0000001"]
            assert len(r_tracks) == 1, f"旧机应写 1 条 R 记录，实际 {len(r_tracks)}"
            assert r_tracks[0].type == "R"
            assert r_tracks[0].cust_cd == "CUST001"
            assert r_tracks[0].n_cust_cd in (None, "")
            assert len(c_tracks) == 1, f"新机应写 1 条 C 记录，实际 {len(c_tracks)}"
            assert c_tracks[0].type == "C"
            assert c_tracks[0].cust_cd in (None, "")
            assert c_tracks[0].n_cust_cd == "CUST001"

            # 校验 rl：旧机失效，新机新建
            old_rl = (
                db.session.query(CustPosRl)
                .filter(CustPosRl.eid == "EIDOLD0000001")
                .order_by(CustPosRl.id.desc())
                .first()
            )
            assert old_rl.useflg == "0"
            assert old_rl.asset_status == "RETURNED"

            # 校验旧机 tmm43_eid.sflg='3'（待检），对齐 PB USP_PLAN_CONFRIM
            # 注：sflg='2' 是"已报废"，'3' 才是"待检/待核实"
            old_eid = db.session.query(Eid).filter(Eid.eid == "EIDOLD0000001").first()
            assert old_eid is not None
            assert old_eid.sflg == "3"

            new_rl = (
                db.session.query(CustPosRl)
                .filter(
                    CustPosRl.eid == "EIDNEW0000001",
                    CustPosRl.cust_cd == "CUST001",
                    CustPosRl.useflg == "1",
                )
                .first()
            )
            assert new_rl is not None, "新机应新建活跃 rl"
            assert new_rl.asset_status == "ACTIVE"

            # 校验回写 plan_status='01'
            plan = db.session.get(PlanCust, "PL000001")
            assert plan.plan_status == "01"

    def test_renovate_close_no_plan_no_writeback(self, app: Flask) -> None:
        """无关联预计划时，关单仍写 EidTrack + rl，但不回写计划。"""
        with app.app_context():
            _seed_customer("CUST001", "CARD001")
            _seed_eid("EIDOLD0000002")
            _seed_eid("EIDNEW0000002")
            _seed_rl("CUST001", "EIDOLD0000002")
            renovate = _seed_renovate(
                old_device_id="EIDOLD0000002",
                new_device_id="EIDNEW0000002",
            )
            db.session.commit()

            svc = MaintenanceRenovateService()
            _transition_to_5(svc, renovate.renew_id)

            # 仍写 EidTrack（只查业务语义层 R/C）
            tracks = (
                db.session.query(EidTrack)
                .filter(
                    EidTrack.eid.in_(["EIDOLD0000002", "EIDNEW0000002"]),
                    EidTrack.type.in_(["R", "C"]),
                )
                .all()
            )
            assert len(tracks) == 2
            # 仍转移 rl
            old_rl = (
                db.session.query(CustPosRl)
                .filter(CustPosRl.eid == "EIDOLD0000002")
                .order_by(CustPosRl.id.desc())
                .first()
            )
            assert old_rl.useflg == "0"

    def test_renovate_close_plan_not_04_no_writeback(self, app: Flask) -> None:
        """预计划 plan_status != '04' 时，不回写计划状态。"""
        with app.app_context():
            _seed_customer("CUST001", "CARD001")
            _seed_eid("EIDOLD0000003")
            _seed_eid("EIDNEW0000003")
            _seed_rl("CUST001", "EIDOLD0000003")
            renovate = _seed_renovate(
                old_device_id="EIDOLD0000003",
                new_device_id="EIDNEW0000003",
            )
            # plan_status='01'（已完成），不应回写
            plan = PlanCust(
                planno="PL000003",
                plantyp="20",
                custnew="N",
                custcard="CARD001",
                custcd="CUST001",
                imple_billid=renovate.renew_id,
                plan_status="01",
                opercd="T00001",
                gendate=datetime.now(UTC),
            )
            db.session.add(plan)
            db.session.commit()

            svc = MaintenanceRenovateService()
            _transition_to_5(svc, renovate.renew_id)

            plan = db.session.get(PlanCust, "PL000003")
            assert plan.plan_status == "01"  # 未被回写

    def test_renovate_not_found_returns_error(self, app: Flask) -> None:
        """翻新单不存在时返回错误，不抛异常。"""
        with app.app_context():
            svc = MaintenanceRenovateService()
            result = svc.transition("NON_EXIST_ID", "2", "T00001")
            assert result["success"] is False
            assert "不存在" in result["error"]

    def test_renovate_invalid_transition_no_side_effects(self, app: Flask) -> None:
        """非法状态流转（1→5 跳过 2）被状态机拒绝，不写 EidTrack/rl/回写。"""
        with app.app_context():
            _seed_customer("CUST001", "CARD001")
            _seed_eid("EIDOLD0000010")
            _seed_eid("EIDNEW0000010")
            _seed_rl("CUST001", "EIDOLD0000010")
            renovate = _seed_renovate(
                old_device_id="EIDOLD0000010",
                new_device_id="EIDNEW0000010",
            )
            _seed_plan("PL000010", renovate.renew_id)
            db.session.commit()

            svc = MaintenanceRenovateService()
            # 1→5 非法（应先 1→2 再 2→5）
            result = svc.transition(renovate.renew_id, "5", "T00001")
            assert result["success"] is False

            # 校验无 EidTrack 业务语义层记录
            tracks = (
                db.session.query(EidTrack)
                .filter(
                    EidTrack.eid.in_(["EIDOLD0000010", "EIDNEW0000010"]),
                    EidTrack.type.in_(["R", "C"]),
                )
                .all()
            )
            assert len(tracks) == 0, "非法流转不应写 EidTrack"

            # 校验 rl 未失效
            old_rl = (
                db.session.query(CustPosRl)
                .filter(
                    CustPosRl.eid == "EIDOLD0000010",
                    CustPosRl.useflg == "1",
                )
                .first()
            )
            assert old_rl is not None, "非法流转不应失效 rl"
            assert old_rl.asset_status == "ACTIVE"

            # 校验 plan_status 未回写
            plan = db.session.get(PlanCust, "PL000010")
            assert plan.plan_status == "04"

    def test_renovate_no_device_id_no_track_no_rl(self, app: Flask) -> None:
        """翻新单无 old_device_id/new_device_id 时，不写 EidTrack，不转移 rl。"""
        with app.app_context():
            _seed_customer("CUST001", "CARD001")
            renovate = _seed_renovate(
                old_device_id="",
                new_device_id="",
            )
            _seed_plan("PL000020", renovate.renew_id)
            db.session.commit()

            svc = MaintenanceRenovateService()
            _transition_to_5(svc, renovate.renew_id)

            # 无设备 ID，不写 R/C 记录（按 planno 过滤避免跨测试污染）
            tracks = (
                db.session.query(EidTrack)
                .filter(
                    EidTrack.refid == "PL000020",
                    EidTrack.type.in_(["R", "C"]),
                )
                .all()
            )
            assert len(tracks) == 0, "无设备 ID 不应写 R/C 记录"

            # plan_status 仍回写（回写逻辑不依赖设备 ID）
            plan = db.session.get(PlanCust, "PL000020")
            assert plan.plan_status == "01"

    def test_renovate_close_auto_creates_recycle_inbound(self, app: Flask) -> None:
        """翻新单关单：配置了 renovate_return_whcd 且旧机为自有资产时，
        自动创建回收入库草稿（IV=7）。
        """
        with app.app_context():
            _seed_customer("CUST001", "CARD001")
            # 旧机为自有资产（asset_owner='02'）
            _seed_eid("EIDOLD0000050")
            old_eid = db.session.query(Eid).filter(Eid.eid == "EIDOLD0000050").first()
            old_eid.asset_owner = "02"
            _seed_eid("EIDNEW0000050")
            _seed_rl("CUST001", "EIDOLD0000050")
            renovate = _seed_renovate(
                old_device_id="EIDOLD0000050",
                new_device_id="EIDNEW0000050",
            )
            db.session.commit()

            # 配置仓库（get_or_create）
            wh = db.session.get(Warehouse, "W1")
            if wh is None:
                wh = Warehouse(whcd="W1", whnm="回收仓", whtyp="01", opercd="T00001")
                db.session.add(wh)
            sp = db.session.get(SysParm, "stock_in_whcd_7")
            if sp is None:
                db.session.add(SysParm(parm_cd="stock_in_whcd_7", parm_nm="翻新返还仓", parm_val="W1"))
            else:
                sp.parm_val = "W1"
            db.session.commit()

            svc = MaintenanceRenovateService()
            _transition_to_5(svc, renovate.renew_id)

            # 校验创建入库草稿 IV=7
            stock_in = (
                db.session.query(StockIn)
                .filter(
                    StockIn.refbillid == renovate.renew_id,
                    StockIn.invtyp == "7",
                )
                .first()
            )
            assert stock_in is not None, "应自动创建回收入库草稿"
            assert stock_in.whcd == "W1"
            assert stock_in.auditflg == "0"  # 草稿

            # 校验明细
            details = (
                db.session.query(StockInDetail)
                .filter(StockInDetail.inbillid == stock_in.inbillid)
                .all()
            )
            assert len(details) == 1
            assert details[0].eid == "EIDOLD0000050"

    def test_renovate_close_no_whcd_no_inbound(self, app: Flask) -> None:
        """翻新单关单：未配置 renovate_return_whcd 时不创建入库草稿。"""
        with app.app_context():
            _seed_customer("CUST001", "CARD001")
            _seed_eid("EIDOLD0000060")
            old_eid = db.session.query(Eid).filter(Eid.eid == "EIDOLD0000060").first()
            old_eid.asset_owner = "02"
            _seed_eid("EIDNEW0000060")
            _seed_rl("CUST001", "EIDOLD0000060")
            renovate = _seed_renovate(
                old_device_id="EIDOLD0000060",
                new_device_id="EIDNEW0000060",
            )
            db.session.commit()

            # 确保未配置 sysparm（删除可能存在的配置）
            sp = db.session.get(SysParm, "stock_in_whcd_7")
            if sp is not None:
                db.session.delete(sp)
            db.session.commit()

            svc = MaintenanceRenovateService()
            _transition_to_5(svc, renovate.renew_id)

            stock_in = (
                db.session.query(StockIn)
                .filter(StockIn.refbillid == renovate.renew_id)
                .first()
            )
            assert stock_in is None, "未配置仓库不应创建入库草稿"

    def test_renovate_close_customer_asset_no_inbound(self, app: Flask) -> None:
        """翻新单关单：旧机为客户资产（asset_owner='03' 门店资产）时不创建入库草稿。"""
        with app.app_context():
            _seed_customer("CUST001", "CARD001")
            _seed_eid("EIDOLD0000070")
            old_eid = db.session.query(Eid).filter(Eid.eid == "EIDOLD0000070").first()
            old_eid.asset_owner = "03"  # 门店资产（客户资产，OW 字典）
            _seed_eid("EIDNEW0000070")
            _seed_rl("CUST001", "EIDOLD0000070")
            renovate = _seed_renovate(
                old_device_id="EIDOLD0000070",
                new_device_id="EIDNEW0000070",
            )
            wh = db.session.get(Warehouse, "W1")
            if wh is None:
                wh = Warehouse(whcd="W1", whnm="回收仓", whtyp="01", opercd="T00001")
                db.session.add(wh)
            sp = db.session.get(SysParm, "stock_in_whcd_7")
            if sp is None:
                db.session.add(SysParm(parm_cd="stock_in_whcd_7", parm_nm="翻新返还仓", parm_val="W1"))
            else:
                sp.parm_val = "W1"
            db.session.commit()

            svc = MaintenanceRenovateService()
            _transition_to_5(svc, renovate.renew_id)

            stock_in = (
                db.session.query(StockIn)
                .filter(StockIn.refbillid == renovate.renew_id)
                .first()
            )
            assert stock_in is None, "客户资产不应创建回收入库草稿"
