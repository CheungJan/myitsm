"""V2 测试：关单联动 L1-L11 集成测试。

验证日常维护单关单（to_status=5）时：
  L1：写 tmm43_eid_track type='A'（配件更换属性变更）
  L2：更新 tmm43_eid.warranty_expire（新配件保修期）
  L3：更新 tmm44_pos_r_eid（整机更换旧eid失效+新eid关联）
  L11：写 TIT10_POS_DETAIL（c_type=4 整机更换记录）
  C7：PF→OW 映射（开通单关单时）
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask

from app.extensions import db
from app.models.itsm import (
    AccessoriesUpdate,
    MaintenanceDaily,
    MaintenanceOpen,
    PosDetail,
)
from app.models.master import (
    Customer,
    CustPosRl,
    Eid,
    EidTrack,
    Item,
    PosREid,
)
from app.models.sales import PlanCust
from app.repositories.itsm_repository import (
    MaintenanceDailyRepository,
    MaintenanceOpenRepository,
)
from app.services.itsm_service import (
    MaintenanceDailyService,
    MaintenanceOpenService,
)


def _seed_customer(cust_cd: str = "CUSTV2") -> Customer:
    existing = db.session.get(Customer, cust_cd)
    if existing:
        return existing
    record = Customer(
        cust_cd=cust_cd,
        cust_nm=f"测试客户{cust_cd}",
        cust_card="CARD001",
        useflg="1",
        customer_status="ACTIVE",
    )
    db.session.add(record)
    return record


def _seed_eid(eid: str, itemcd: str = "IT0001", asset_owner: str = "03") -> Eid:
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
        asset_owner=asset_owner,
    )
    db.session.add(record)
    return record


def _seed_item(item_cd: str = "IT0001", newperiod: int = 365, oldperiod: int = 92) -> Item:
    existing = db.session.get(Item, item_cd)
    if existing:
        return existing
    record = Item(
        item_cd=item_cd,
        item_nm=f"测试物料{item_cd}",
        newperiod=newperiod,
        oldperiod=oldperiod,
    )
    db.session.add(record)
    return record


def _seed_daily(store_id: str = "CUSTV2") -> MaintenanceDaily:
    record = MaintenanceDailyRepository.create(
        {
            "store_id": store_id,
            "fault_type": "01",
            "short_description": "测试关单联动",
        },
        "T00001",
    )
    return record


def _seed_accessories(
    maintenance_id: str,
    old_eid: str = "EIDOLD0001",
    new_eid: str = "EIDNEW0001",
    c_type: str = "1",
    itemcd: str = "IT0001",
) -> AccessoriesUpdate:
    record = AccessoriesUpdate(
        maintenance_id=maintenance_id,
        store_id="CUSTV2",
        device_id="EIDDEVICE01",
        old_accessories_id=old_eid,
        new_accessories_id=new_eid,
        accessories_type=itemcd,
        itemcd=itemcd,
        c_type=c_type,
        is_new="1",
        creator="T00001",
        create_time=datetime.now(UTC),
    )
    db.session.add(record)
    return record


def _transition_to_5(svc: MaintenanceDailyService, mid: str) -> None:
    """执行 1→2→5 状态流转。"""
    svc.transition(mid, "2", "T00001")
    svc.transition(mid, "5", "T00001")


class TestCloseLinkageL1:
    """L1：关单写 EidTrack type='A'。"""

    def test_close_writes_eid_track(self, app: Flask) -> None:
        """关单后 tmm43_eid_track 新增 type='A' 记录。"""
        with app.app_context():
            _seed_customer()
            _seed_eid("EIDOLD0001")
            _seed_eid("EIDNEW0001")
            daily = _seed_daily()
            _seed_accessories(daily.maintenance_id)
            db.session.commit()

            svc = MaintenanceDailyService()
            _transition_to_5(svc, daily.maintenance_id)

            tracks = (
                db.session.query(EidTrack)
                .filter(
                    EidTrack.eid == "EIDOLD0001",
                    EidTrack.type == "A",
                )
                .all()
            )
            assert len(tracks) >= 1, "关单应写 type='A' EidTrack"
            assert tracks[0].refid == daily.maintenance_id


class TestCloseLinkageL2:
    """L2：关单更新 tmm43_eid.warranty_expire。"""

    def test_close_updates_warranty_expire(self, app: Flask) -> None:
        """关单后新配件 warranty_expire 被回填。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001", newperiod=365, oldperiod=92)
            _seed_eid("EIDOLD0001")
            new_eid = _seed_eid("EIDNEW0001")
            daily = _seed_daily()
            _seed_accessories(daily.maintenance_id)
            db.session.commit()

            assert new_eid.warranty_expire is None

            svc = MaintenanceDailyService()
            _transition_to_5(svc, daily.maintenance_id)

            db.session.refresh(new_eid)
            assert new_eid.warranty_expire is not None, "关单应回填 warranty_expire"
            assert new_eid.install_date is not None, "关单应回填 install_date"


class TestCloseLinkageL3:
    """L3：关单更新 tmm44_pos_r_eid（整机更换）。"""

    def test_close_updates_pos_r_eid_for_exchange(self, app: Flask) -> None:
        """c_type=4 整机更换：旧 eid 失效 + 新 eid 关联。"""
        with app.app_context():
            _seed_customer()
            _seed_eid("EIDOLD0001")
            _seed_eid("EIDNEW0001")
            # 旧 eid 已关联 pos_r_eid
            old_pos = PosREid(
                posid="POS001",
                eid="EIDOLD0001",
                itemcd="IT0001",
                opercd="T00001",
                gendate=datetime.now(UTC),
                useflg="1",
            )
            db.session.add(old_pos)
            daily = _seed_daily()
            _seed_accessories(
                daily.maintenance_id,
                c_type="4",  # 整机更换
            )
            db.session.commit()

            svc = MaintenanceDailyService()
            _transition_to_5(svc, daily.maintenance_id)

            db.session.refresh(old_pos)
            assert old_pos.useflg == "0", "旧 eid 应失效"

            new_pos = (
                db.session.query(PosREid)
                .filter(PosREid.eid == "EIDNEW0001", PosREid.useflg == "1")
                .first()
            )
            assert new_pos is not None, "新 eid 应关联 pos_r_eid"


class TestCloseLinkageL11:
    """L11：关单写 TIT10_POS_DETAIL（c_type=4 整机更换）。"""

    def test_close_writes_pos_detail_for_exchange(self, app: Flask) -> None:
        """c_type=4 整机更换：写旧/新整机 PosDetail 记录。"""
        with app.app_context():
            _seed_customer()
            _seed_eid("EIDOLD0001")
            _seed_eid("EIDNEW0001")
            daily = _seed_daily()
            _seed_accessories(
                daily.maintenance_id,
                c_type="4",  # 整机更换
            )
            db.session.commit()

            svc = MaintenanceDailyService()
            _transition_to_5(svc, daily.maintenance_id)

            details = (
                db.session.query(PosDetail)
                .filter(PosDetail.bill_id == daily.maintenance_id)
                .all()
            )
            assert len(details) == 2, "整机更换应写 2 条 PosDetail（旧+新）"
            noflgs = {d.noflg for d in details}
            assert noflgs == {"0", "1"}, "应包含旧设备(noflg=0)和新设备(noflg=1)"


class TestCloseLinkageC7:
    """C7：PF→OW 映射（开通单关单时）。"""

    def test_pf_to_ow_mapping_warehouse(self, app: Flask) -> None:
        """PF='00' 商用仓库 → OW='01' 商用电子。"""
        with app.app_context():
            _seed_customer()
            eid_rec = _seed_eid("EIDOPEN001", asset_owner="03")
            _seed_item("IT0001")

            # 创建开通单
            open_rec = MaintenanceOpenRepository.create(
                {
                    "store_id": "CUSTV2",
                    "device_id": "EIDOPEN001",
                },
                "T00001",
            )
            # 创建预计划 pos_from='00'
            plan = PlanCust(
                planno="PL000001",
                plantyp="10",
                custnew="N",
                custcard="CARD001",
                custcd="CUSTV2",
                imple_billid=open_rec.new_opening_id,
                plan_status="04",
                pos_from="00",  # 商用仓库
                posid="EIDOPEN001",
                opercd="T00001",
                gendate=datetime.now(UTC),
            )
            db.session.add(plan)
            db.session.commit()

            svc = MaintenanceOpenService()
            svc.transition(open_rec.new_opening_id, "2", "T00001")
            svc.transition(open_rec.new_opening_id, "5", "T00001")

            db.session.refresh(eid_rec)
            assert eid_rec.asset_owner == "01", "PF='00' 应映射为 OW='01' 商用电子"

    def test_pf_to_ow_mapping_inherit(self, app: Flask) -> None:
        """PF='01' 门店移机 → 继承原 OW 值。"""
        with app.app_context():
            _seed_customer()
            eid_rec = _seed_eid("EIDOPEN002", asset_owner="03")  # 门店资产
            _seed_item("IT0001")

            open_rec = MaintenanceOpenRepository.create(
                {
                    "store_id": "CUSTV2",
                    "device_id": "EIDOPEN002",
                },
                "T00001",
            )
            plan = PlanCust(
                planno="PL000002",
                plantyp="10",
                custnew="N",
                custcard="CARD001",
                custcd="CUSTV2",
                imple_billid=open_rec.new_opening_id,
                plan_status="04",
                pos_from="01",  # 门店移机，继承
                posid="EIDOPEN002",
                opercd="T00001",
                gendate=datetime.now(UTC),
            )
            db.session.add(plan)
            db.session.commit()

            svc = MaintenanceOpenService()
            svc.transition(open_rec.new_opening_id, "2", "T00001")
            svc.transition(open_rec.new_opening_id, "5", "T00001")

            db.session.refresh(eid_rec)
            assert eid_rec.asset_owner == "03", "PF='01' 应继承原 OW='03'"


class TestCloseLinkageL4:
    """L4：关单清空新配件 whcd（标记已安装）。"""

    def test_close_clears_new_part_whcd(self, app: Flask) -> None:
        """关单后新配件 whcd=NULL（已安装），sflg 保持 '1'。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            new_eid = _seed_eid("EIDNEW0001")
            new_eid.whcd = "W1"  # 服务领用后持有在工程师仓
            new_eid.sflg = "1"
            daily = _seed_daily()
            _seed_accessories(daily.maintenance_id, new_eid="EIDNEW0001")
            db.session.commit()

            svc = MaintenanceDailyService()
            _transition_to_5(svc, daily.maintenance_id)

            db.session.refresh(new_eid)
            assert new_eid.whcd is None, "L4：关单后新配件 whcd 应清空（已安装）"
            assert new_eid.sflg == "1", "L4：sflg 保持 '1'（已使用）"
            assert new_eid.refid == daily.maintenance_id, "L4：refid 应为工单号"

    def test_close_no_new_part_skips_l4(self, app: Flask) -> None:
        """无新配件的工单不触发 L4。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            old_eid = _seed_eid("EIDOLD0001")
            old_eid.whcd = "W1"
            daily = _seed_daily()
            # c_type='3' 纯服务费，无新配件
            _seed_accessories(daily.maintenance_id, new_eid="", c_type="3")
            db.session.commit()

            svc = MaintenanceDailyService()
            _transition_to_5(svc, daily.maintenance_id)

            db.session.refresh(old_eid)
            # 旧配件不受 L4 影响
            assert old_eid.whcd == "W1"


class TestCloseLinkageL5:
    """L5：关单处理旧配件报废（in_wh='2'）。"""

    def test_close_scraps_old_part_in_wh_2(self, app: Flask) -> None:
        """in_wh='2' 的旧配件关单后 sflg='2'（已报废）。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            old_eid = _seed_eid("EIDOLD0001")
            old_eid.whcd = "W1"
            old_eid.sflg = "1"
            daily = _seed_daily()
            acc = _seed_accessories(daily.maintenance_id, old_eid="EIDOLD0001")
            acc.in_wh = "2"  # 标记不入库=报废
            db.session.commit()

            svc = MaintenanceDailyService()
            _transition_to_5(svc, daily.maintenance_id)

            db.session.refresh(old_eid)
            assert old_eid.sflg == "2", "L5：in_wh='2' 旧配件应 sflg='2'（已报废）"
            assert old_eid.whcd is None, "L5：报废旧配件 whcd 应清空"
            assert old_eid.refid == daily.maintenance_id, "L5：refid 应为工单号"

    def test_close_keeps_old_part_in_wh_not_2(self, app: Flask) -> None:
        """in_wh!='2' 的旧配件不触发 L5 报废（走 L6 入库流程）。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            old_eid = _seed_eid("EIDOLD0001", asset_owner="03")  # 门店资产
            old_eid.whcd = "W1"
            old_eid.sflg = "1"
            daily = _seed_daily()
            acc = _seed_accessories(daily.maintenance_id, old_eid="EIDOLD0001")
            acc.in_wh = None  # 未标记报废，走 L6 入库
            db.session.commit()

            svc = MaintenanceDailyService()
            _transition_to_5(svc, daily.maintenance_id)

            db.session.refresh(old_eid)
            # L5 不处理 in_wh!='2' 的记录，sflg 不变（L6 草稿审核后才改）
            assert old_eid.sflg == "1", "L5：in_wh!='2' 旧配件不触发报废"
