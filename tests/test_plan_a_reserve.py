"""方案 A 专属功能测试：EID 预占 + implement 自动出库 + 释放预占。"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask

from app.extensions import db
from app.models.master import Customer, Eid, Item
from app.models.sales import PlanCust
from app.models.warehouse import Warehouse
from app.services.plan_stock_service import PlanStockService
from app.services.sales_service import PlanCustService


def _seed(app: Flask) -> None:
    """插入方案 A 测试数据：仓库、物料、2 台 EID。"""
    with app.app_context():
        # 清测试相关数据（按 custcard 前缀 HP00A 和 EID 前缀 EID00A）
        db.session.query(Customer).filter(Customer.cust_card.like("HP00A%")).delete(
            synchronize_session=False
        )
        db.session.query(PlanCust).filter(PlanCust.custcard.like("HP00A%")).delete(
            synchronize_session=False
        )
        db.session.query(Eid).filter(Eid.eid.like("EID00A%")).delete(synchronize_session=False)
        db.session.query(Item).filter(Item.item_cd == "IT00A").delete(synchronize_session=False)
        db.session.query(Warehouse).filter(Warehouse.whcd == "W0A").delete(
            synchronize_session=False
        )

        db.session.add(Warehouse(whcd="W0A", whnm="方案A测试仓", whtyp="03", useflg="1"))
        db.session.add(Item(item_cd="IT00A", item_nm="方案A测试物料", useflg="1"))
        for eid_val in ("EID00A0000001", "EID00A0000002"):
            db.session.add(
                Eid(
                    itemcd="IT00A",
                    eid=eid_val,
                    opercd="T00001",
                    gendate=datetime.now(UTC),
                    useflg="1",
                    sflg="8",
                    whcd="W0A",
                    asset_type="01",
                    itemtyp="GA",
                )
            )
        db.session.commit()


class TestPlanAReserve:
    """方案 A：EID 预占 + 自动出库 + 释放。"""

    def test_create_plan_with_posid_reserves_eid(self, app: Flask) -> None:
        """预计划创建时 posid 已选，EID.reserve_planno 被锁定。"""
        _seed(app)
        with app.app_context():
            result = PlanCustService.create(
                {
                    "plantyp": "00",
                    "custnm": "方案A",
                    "custcd": "T00A",
                    "custcard": "HP00A",
                    "posid": "EID00A0000001",
                    "pos_item": "IT00A",
                },
                creator="T00001",
            )
            assert result.get("success") is not False, result
            planno = result["planno"]

            eid = db.session.query(Eid).filter(Eid.eid == "EID00A0000001").first()
            assert eid.reserve_planno == planno

    def test_create_plan_posid_already_reserved_rejected(self, app: Flask) -> None:
        """EID 已被其他预计划预占时，创建被拒绝。"""
        _seed(app)
        with app.app_context():
            r1 = PlanCustService.create(
                {
                    "plantyp": "00",
                    "custnm": "方案A1",
                    "custcd": "T00A1",
                    "custcard": "HP00A1",
                    "posid": "EID00A0000001",
                    "pos_item": "IT00A",
                },
                creator="T00001",
            )
            assert r1.get("success") is not False

            r2 = PlanCustService.create(
                {
                    "plantyp": "00",
                    "custnm": "方案A2",
                    "custcd": "T00A2",
                    "custcard": "HP00A2",
                    "posid": "EID00A0000001",
                    "pos_item": "IT00A",
                },
                creator="T00001",
            )
            assert r2.get("success") is False
            assert "已被预计划" in r2.get("error", "")

    def test_list_available_eids_excludes_reserved(self, app: Flask) -> None:
        """list_available_eids 默认排除已预占的 EID。"""
        _seed(app)
        with app.app_context():
            PlanCustService.create(
                {
                    "plantyp": "00",
                    "custnm": "方案A",
                    "custcd": "T00A",
                    "custcard": "HP00A",
                    "posid": "EID00A0000001",
                    "pos_item": "IT00A",
                },
                creator="T00001",
            )

            data = PlanStockService.list_available_eids(model_cd="IT00A")
            eids = [it["eid"] for it in data["items"]]
            assert "EID00A0000001" not in eids, "已预占 EID 不应出现在可用列表"
            assert "EID00A0000002" in eids, "未预占 EID 应出现"

    def test_list_available_eids_include_reserved_when_flag_off(self, app: Flask) -> None:
        """exclude_reserved=False 时返回所有在库 EID（含已预占）。"""
        _seed(app)
        with app.app_context():
            PlanCustService.create(
                {
                    "plantyp": "00",
                    "custnm": "方案A",
                    "custcd": "T00A",
                    "custcard": "HP00A",
                    "posid": "EID00A0000001",
                    "pos_item": "IT00A",
                },
                creator="T00001",
            )

            data = PlanStockService.list_available_eids(model_cd="IT00A", exclude_reserved=False)
            eids = [it["eid"] for it in data["items"]]
            assert "EID00A0000001" in eids, "exclude_reserved=False 应含已预占"

    def test_void_plan_releases_reserve(self, app: Flask) -> None:
        """预计划作废时释放 EID 预占。"""
        _seed(app)
        with app.app_context():
            result = PlanCustService.create(
                {
                    "plantyp": "00",
                    "custnm": "方案A",
                    "custcd": "T00A",
                    "custcard": "HP00A",
                    "posid": "EID00A0000001",
                    "pos_item": "IT00A",
                },
                creator="T00001",
            )
            planno = result["planno"]

            void_result = PlanCustService.void(planno, operator="T00001", remark="测试作废")
            assert void_result["success"] is True

            eid = db.session.query(Eid).filter(Eid.eid == "EID00A0000001").first()
            assert eid.reserve_planno is None, "作废后预占应释放"
