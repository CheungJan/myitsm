"""P0-1 测试：离店 d2d_result='5' 触发 L1-L11 联动。

验证离店登记时 d2d_result='5'（已解决=关单）：
  - L4：新配件 whcd 清空（已安装）
  - L5：旧配件 in_wh='2' 报废 sflg='2'
  - L2：新配件 warranty_expire 回填
  - L1：写 EidTrack type='A'

对比：d2d_result='4'（未解决）不触发联动。
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask

from app.extensions import db
from app.models.itsm import (
    AccessoriesUpdate,
    MaintenanceDaily,
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


class TestLeaveStoreLinkageP01:
    """P0-1：离店 d2d_result='5' 触发 L1-L11 联动。"""

    def test_leave_store_result_5_triggers_l4(self, app: Flask) -> None:
        """离店 d2d_result='5' → 新配件 whcd 清空（L4）。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            new_eid = _seed_eid("EIDNEW0001")
            new_eid.whcd = "W1"  # 工程师仓持有
            new_eid.sflg = "1"
            daily = _seed_daily()
            _seed_accessories(daily.maintenance_id, new_eid="EIDNEW0001")
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

            db.session.refresh(new_eid)
            assert new_eid.whcd is None, "P0-1: 离店 d2d_result='5' 应触发 L4 清空 whcd"
            assert new_eid.sflg == "1", "P0-1: sflg 保持 '1'"
            assert new_eid.refid == daily.maintenance_id, "P0-1: refid 应为工单号"

    def test_leave_store_result_5_triggers_l1(self, app: Flask) -> None:
        """离店 d2d_result='5' → 写 EidTrack type='A'（L1）。"""
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
            assert len(tracks) >= 1, "P0-1: 离店 d2d_result='5' 应写 EidTrack type='A'"

    def test_leave_store_result_5_triggers_l5_scrap(self, app: Flask) -> None:
        """离店 d2d_result='5' + in_wh='2' → 旧配件 sflg='2'（L5 报废）。"""
        with app.app_context():
            _seed_customer()
            _seed_item("IT0001")
            old_eid = _seed_eid("EIDOLD0001")
            old_eid.whcd = "W1"
            old_eid.sflg = "1"
            daily = _seed_daily()
            acc = _seed_accessories(daily.maintenance_id, old_eid="EIDOLD0001")
            acc.in_wh = "2"  # 报废
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

            db.session.refresh(old_eid)
            assert old_eid.sflg == "2", "P0-1: 离店 d2d_result='5' 应触发 L5 报废"

    def test_leave_store_result_4_no_linkage(self, app: Flask) -> None:
        """离店 d2d_result='4'（未解决）→ 不触发 L4（中间态）。"""
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
                    "d2d_result": "4",  # 未解决
                    "d2d_phenomenon": "设备无法开机",
                    "d2d_handling": "尝试维修未果",
                },
                "T00001",
            )

            db.session.refresh(new_eid)
            # d2d_result='4' 是中间态，不触发 L4
            assert new_eid.whcd == "W1", "P0-1: d2d_result='4' 不应触发 L4"
            assert new_eid.sflg == "1", "P0-1: d2d_result='4' sflg 不变"
