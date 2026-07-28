"""P0-1 测试：离店不改状态不联动，完成维修才是唯一触发器。

修正方案：
  离店(d2d_result='5'/'4'/'6'/'7'): 只写 TIT23，不改主表状态，不触发 L1-L11
  完成维修 transition(5): current_status→5 + 读 TIT23 派生 is_success + 触发 L1-L11

验证：
  - 离店后主表 current_status 不变（仍为 2）
  - 离店后新配件 whcd 不变（L4 不触发）
  - 离店后无 EidTrack type='A'（L1 不触发）
  - 完成维修 transition(5) 后触发 L1-L11
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask

from app.extensions import db
from app.models.itsm import (
    AccessoriesUpdate,
    MaintenanceDaily,
    MaintenanceD2D,
)
from app.models.master import (
    Customer,
    Eid,
    EidTrack,
    Item,
)
from app.repositories.itsm_repository import MaintenanceDailyRepository
from app.services.itsm_service import D2DService, MaintenanceDailyService


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
            "short_description": "测试离店联动",
        },
        "T00001",
    )
    # 流转到已分配
    MaintenanceDailyService().transition(record.maintenance_id, "2", "T00001")
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


def _seed_arrive(maintenance_id: str) -> None:
    """到店登记（离店前置条件）。"""
    D2DService.arrive_store(
        maintenance_id,
        {"d2d_engineer": "T00001", "arrive_time": datetime.now(UTC)},
        "T00001",
    )


class TestLeaveStoreNoLinkageP01:
    """P0-1 修正：离店不改状态不联动。"""

    def test_leave_store_result_5_no_status_change(self, app: Flask) -> None:
        """离店 d2d_result='5' → 主表 current_status 不变（仍为 2）。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            new_eid = _seed_eid("EIDNEW0001")
            new_eid.whcd = "W1"
            new_eid.sflg = "1"
            daily = _seed_daily()
            _seed_accessories(daily.maintenance_id, new_eid="EIDNEW0001")
            db.session.commit()
            _seed_arrive(daily.maintenance_id)

            D2DService.leave_store(
                daily.maintenance_id,
                {
                    "d2d_result": "5",
                    "d2d_phenomenon": "设备无法开机",
                    "d2d_handling": "更换配件",
                    "d2d_reason": "配件损坏",
                },
                "T00001",
            )

            db.session.refresh(daily)
            assert daily.current_status == "2", "P0-1: 离店不改 current_status，仍为 2"

    def test_leave_store_result_5_no_l4(self, app: Flask) -> None:
        """离店 d2d_result='5' → 新配件 whcd 不变（L4 不触发）。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            new_eid = _seed_eid("EIDNEW0001")
            new_eid.whcd = "W1"
            new_eid.sflg = "1"
            daily = _seed_daily()
            _seed_accessories(daily.maintenance_id, new_eid="EIDNEW0001")
            db.session.commit()
            _seed_arrive(daily.maintenance_id)

            D2DService.leave_store(
                daily.maintenance_id,
                {
                    "d2d_result": "5",
                    "d2d_phenomenon": "设备无法开机",
                    "d2d_handling": "更换配件",
                    "d2d_reason": "配件损坏",
                },
                "T00001",
            )

            db.session.refresh(new_eid)
            assert new_eid.whcd == "W1", "P0-1: 离店不触发 L4，whcd 不变"
            assert new_eid.sflg == "1", "P0-1: 离店 sflg 不变"

    def test_leave_store_result_5_no_l1(self, app: Flask) -> None:
        """离店 d2d_result='5' → 无 EidTrack type='A'（L1 不触发）。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            _seed_eid("EIDOLD0001")
            _seed_eid("EIDNEW0001")
            daily = _seed_daily()
            _seed_accessories(daily.maintenance_id)
            db.session.commit()
            _seed_arrive(daily.maintenance_id)

            D2DService.leave_store(
                daily.maintenance_id,
                {
                    "d2d_result": "5",
                    "d2d_phenomenon": "设备无法开机",
                    "d2d_handling": "更换配件",
                    "d2d_reason": "配件损坏",
                },
                "T00001",
            )

            tracks = (
                db.session.query(EidTrack)
                .filter(
                    EidTrack.eid == "EIDOLD0001",
                    EidTrack.type == "A",
                )
                .all()
            )
            assert len(tracks) == 0, "P0-1: 离店不触发 L1，无 EidTrack type='A'"

    def test_leave_store_writes_d2d_record(self, app: Flask) -> None:
        """离店 d2d_result='5' → 写 TIT23 离店记录。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            daily = _seed_daily()
            db.session.commit()
            _seed_arrive(daily.maintenance_id)

            D2DService.leave_store(
                daily.maintenance_id,
                {
                    "d2d_result": "5",
                    "d2d_phenomenon": "设备无法开机",
                    "d2d_handling": "更换配件",
                    "d2d_reason": "配件损坏",
                },
                "T00001",
            )

            d2d_records = (
                db.session.query(MaintenanceD2D)
                .filter(
                    MaintenanceD2D.maintenance_id == daily.maintenance_id,
                    MaintenanceD2D.d2d_type == "2",
                )
                .all()
            )
            assert len(d2d_records) >= 1, "P0-1: 离店应写 TIT23 离店记录"
            assert d2d_records[0].d2d_result == "5"


class TestCompleteMaintenanceLinkageP01:
    """P0-1 修正：完成维修 transition(5) 才触发 L1-L11。"""

    def test_transition_5_triggers_l4(self, app: Flask) -> None:
        """完成维修 transition(5) → 触发 L4（新配件 whcd 清空）。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            new_eid = _seed_eid("EIDNEW0001")
            new_eid.whcd = "W1"
            new_eid.sflg = "1"
            daily = _seed_daily()
            _seed_accessories(daily.maintenance_id, new_eid="EIDNEW0001")
            db.session.commit()

            # 完成维修（不经过离店，直接 transition 2→5）
            MaintenanceDailyService().transition(daily.maintenance_id, "5", "T00001")

            db.session.refresh(new_eid)
            assert new_eid.whcd is None, "P0-1: 完成维修应触发 L4 清空 whcd"
            assert new_eid.sflg == "1"
            assert new_eid.refid == daily.maintenance_id

    def test_transition_5_triggers_l1(self, app: Flask) -> None:
        """完成维修 transition(5) → 触发 L1（写 EidTrack type='A'）。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            _seed_eid("EIDOLD0001")
            _seed_eid("EIDNEW0001")
            daily = _seed_daily()
            _seed_accessories(daily.maintenance_id)
            db.session.commit()

            MaintenanceDailyService().transition(daily.maintenance_id, "5", "T00001")

            tracks = (
                db.session.query(EidTrack)
                .filter(
                    EidTrack.eid == "EIDOLD0001",
                    EidTrack.type == "A",
                )
                .all()
            )
            assert len(tracks) >= 1, "P0-1: 完成维修应触发 L1 写 EidTrack"

    def test_transition_5_derives_is_success_from_d2d(self, app: Flask) -> None:
        """完成维修 transition(5) → 读 TIT23 派生 is_success。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            daily = _seed_daily()
            db.session.commit()
            _seed_arrive(daily.maintenance_id)

            # 离店 d2d_result='5'
            D2DService.leave_store(
                daily.maintenance_id,
                {
                    "d2d_result": "5",
                    "d2d_phenomenon": "设备无法开机",
                    "d2d_handling": "更换配件",
                    "d2d_reason": "配件损坏",
                },
                "T00001",
            )

            # 完成维修
            MaintenanceDailyService().transition(daily.maintenance_id, "5", "T00001")

            db.session.refresh(daily)
            # is_success 应按 d2d_result='5' 派生
            assert daily.is_success is not None, "P0-1: 完成维修应派生 is_success"
            assert daily.current_status == "5"


class TestRevisitCloseNoLinkage:
    """方案 B：5→3 回访确认关单不触发联动（联动已在 2→5 完成）。"""

    def test_transition_3_no_l4(self, app: Flask) -> None:
        """5→3 回访确认关单 → 不触发 L4（whcd 已在 2→5 时清空，保持 None）。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            new_eid = _seed_eid("EIDNEW0001")
            new_eid.whcd = "W1"
            new_eid.sflg = "1"
            daily = _seed_daily()
            _seed_accessories(daily.maintenance_id, new_eid="EIDNEW0001")
            db.session.commit()

            # 完成维修 2→5（触发 L4，whcd 清空）
            MaintenanceDailyService().transition(daily.maintenance_id, "5", "T00001")
            db.session.refresh(new_eid)
            assert new_eid.whcd is None, "前置：完成维修应清空 whcd"

            # 回访确认关单 5→3（不触发联动，whcd 保持 None）
            MaintenanceDailyService().transition(daily.maintenance_id, "3", "T00001")
            db.session.refresh(daily)
            db.session.refresh(new_eid)
            assert daily.current_status == "3", "5→3 后 current_status=3"
            assert new_eid.whcd is None, "5→3 不触发 L4，whcd 保持 None"

    def test_transition_3_no_l1(self, app: Flask) -> None:
        """5→3 回访确认关单 → 不触发 L1（无新增 EidTrack）。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            _seed_eid("EIDOLD0001")
            _seed_eid("EIDNEW0001")
            daily = _seed_daily()
            _seed_accessories(daily.maintenance_id)
            db.session.commit()

            # 完成维修 2→5（触发 L1）
            MaintenanceDailyService().transition(daily.maintenance_id, "5", "T00001")
            tracks_after_5 = (
                db.session.query(EidTrack)
                .filter(EidTrack.eid == "EIDOLD0001", EidTrack.type == "A")
                .count()
            )
            assert tracks_after_5 >= 1, "前置：完成维修应写 EidTrack"

            # 回访确认关单 5→3（不触发 L1，EidTrack 数量不变）
            MaintenanceDailyService().transition(daily.maintenance_id, "3", "T00001")
            tracks_after_3 = (
                db.session.query(EidTrack)
                .filter(EidTrack.eid == "EIDOLD0001", EidTrack.type == "A")
                .count()
            )
            assert tracks_after_3 == tracks_after_5, "5→3 不触发 L1，EidTrack 数量不变"

    def test_transition_3_changes_status_only(self, app: Flask) -> None:
        """5→3 回访确认关单 → 只改状态，is_success 不变。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            daily = _seed_daily()
            db.session.commit()
            _seed_arrive(daily.maintenance_id)
            D2DService.leave_store(
                daily.maintenance_id,
                {"d2d_result": "5", "d2d_phenomenon": "故障", "d2d_handling": "维修"},
                "T00001",
            )

            # 完成维修 2→5
            MaintenanceDailyService().transition(daily.maintenance_id, "5", "T00001")
            db.session.refresh(daily)
            is_success_after_5 = daily.is_success

            # 回访确认关单 5→3
            MaintenanceDailyService().transition(daily.maintenance_id, "3", "T00001")
            db.session.refresh(daily)
            assert daily.current_status == "3"
            assert daily.is_success == is_success_after_5, "5→3 不改 is_success"
