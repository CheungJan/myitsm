"""销售管理 API 测试。"""

from __future__ import annotations

import json
from typing import Any

from flask import Flask
from flask.testing import FlaskClient


def _auth_header(app: Flask) -> dict[str, str]:
    """生成 JWT 认证头。"""
    import jwt

    payload = {"sub": "T00001", "exp": 9999999999}
    token: str = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}", "X-User-Cd": "T00001"}


def _post(client: FlaskClient, url: str, data: dict[str, Any], headers: dict[str, str]) -> Any:
    return client.post(url, data=json.dumps(data), content_type="application/json", headers=headers)


class TestPlanCust:
    """预计划测试。"""

    def test_create_and_get(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/sales/plans",
            {
                "plantyp": "10",
                "custnm": "测试客户A",
                "busityp": "01",
                "address": "广州市天河区",
                "contactor": "张三",
                "phoneno": "13800138000",
            },
            headers,
        )
        assert resp.status_code == 201
        planno = resp.get_json()["data"]["planno"]

        resp2 = client.get(f"/api/v1/sales/plans/{planno}", headers=headers)
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["custnm"] == "测试客户A"

    def test_update(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/sales/plans",
            {"plantyp": "20", "custnm": "测试客户B"},
            headers,
        )
        planno = resp.get_json()["data"]["planno"]

        resp2 = client.put(
            f"/api/v1/sales/plans/{planno}",
            data=json.dumps({"plan_status": "01", "imple_mark": "实施中"}),
            content_type="application/json",
            headers=headers,
        )
        assert resp2.status_code == 200

    def test_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get("/api/v1/sales/plans?page=1&per_page=10", headers=headers)
        assert resp.status_code == 200
        assert "items" in resp.get_json()["data"]


class TestPlanOrchestration:
    """预计划编排测试。"""

    def test_create_with_plantyp_00(self, app: Flask, client: FlaskClient) -> None:
        """plantyp=00 新机开通不抛 TypeError。"""
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/sales/plans",
            {"plantyp": "00", "custnm": "新机测试", "custcd": "T001"},
            headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()["data"]
        assert data["plantyp"] == "00"
        assert data["plan_status"] == "00"

    def test_transition_00_to_02(self, app: Flask, client: FlaskClient) -> None:
        """状态流转 00→02（计划中→分派中）。"""
        headers = _auth_header(app)
        resp = _post(client, "/api/v1/sales/plans", {"plantyp": "10", "custnm": "流转测试"}, headers)
        planno = resp.get_json()["data"]["planno"]

        resp2 = _post(client, f"/api/v1/sales/plans/{planno}/transition", {"to_status": "02"}, headers)
        assert resp2.status_code == 200
        data = resp2.get_json()["data"]
        assert data["to_status"] == "02"

    def test_implement_without_serve_blocks(self, app: Flask, client: FlaskClient) -> None:
        """无已呼出记录时实施被拒绝。"""
        headers = _auth_header(app)
        resp = _post(client, "/api/v1/sales/plans", {"plantyp": "10", "custnm": "无呼出测试", "custcd": "T002"}, headers)
        planno = resp.get_json()["data"]["planno"]
        _post(client, f"/api/v1/sales/plans/{planno}/transition", {"to_status": "02"}, headers)

        resp3 = _post(client, f"/api/v1/sales/plans/{planno}/implement", {}, headers)
        assert resp3.status_code == 400
        assert "呼出" in resp3.get_json()["message"]

    def test_void_cascade(self, app: Flask, client: FlaskClient) -> None:
        """作废 00 状态预计划。"""
        headers = _auth_header(app)
        resp = _post(client, "/api/v1/sales/plans", {"plantyp": "20", "custnm": "作废测试", "custcd": "T003"}, headers)
        planno = resp.get_json()["data"]["planno"]

        resp2 = _post(client, f"/api/v1/sales/plans/{planno}/void", {"remark": "测试作废"}, headers)
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["to_status"] == "09"

    def test_complete_requires_02(self, app: Flask, client: FlaskClient) -> None:
        """00状态不能直接完成。"""
        headers = _auth_header(app)
        resp = _post(client, "/api/v1/sales/plans", {"plantyp": "10", "custnm": "完成测试"}, headers)
        planno = resp.get_json()["data"]["planno"]

        resp2 = _post(client, f"/api/v1/sales/plans/{planno}/complete", {}, headers)
        assert resp2.status_code == 400

    def test_implement_happy_path(self, app: Flask, client: FlaskClient) -> None:
        """正向链路：创建→呼出→实施→下游工单生成且imple_billid回写。"""
        headers = _auth_header(app)

        # 1. 创建预计划 plantyp=00 (新机开通)
        resp = _post(
            client, "/api/v1/sales/plans",
            {"plantyp": "00", "custnm": "正向测试", "custcd": "T010", "custcard": "HP001"},
            headers,
        )
        assert resp.status_code == 201
        planno = resp.get_json()["data"]["planno"]

        # 2. 查呼出单列表，将第一条呼出单置为已呼出(status=01)
        serve_resp = client.get(f"/api/v1/sales/plans/{planno}/serve", headers=headers)
        assert serve_resp.status_code == 200
        serves = serve_resp.get_json()["data"]
        assert len(serves) >= 1
        dtlid = serves[0]["dtlid"]

        _post(client, f"/api/v1/sales/plan-serve/{dtlid}/transition", {"to_status": "01"}, headers)
        # 验证呼出单已更新
        serve2 = client.get(f"/api/v1/sales/plans/{planno}/serve", headers=headers)
        assert serve2.get_json()["data"][0]["status"] == "01"

        # 3. 状态流转 00→02（计划中→分派中）
        _post(client, f"/api/v1/sales/plans/{planno}/transition", {"to_status": "02"}, headers)

        # 4. 实施确认
        impl_resp = _post(client, f"/api/v1/sales/plans/{planno}/implement", {}, headers)
        assert impl_resp.status_code == 200
        impl_data = impl_resp.get_json()["data"]
        assert impl_data["to_status"] == "04"
        downstream_id = impl_data["downstream_id"]
        assert downstream_id, "下游单据ID不应为空"

        # 5. 验证预计划上 imple_billid 已回写
        detail = client.get(f"/api/v1/sales/plans/{planno}", headers=headers)
        assert detail.get_json()["data"]["imple_billid"] == downstream_id
        assert detail.get_json()["data"]["plan_status"] == "04"

        # 6. 验证下游工单真实存在
        itsm_resp = client.get(f"/api/v1/itsm/maintenance-open/{downstream_id}", headers=headers)
        assert itsm_resp.status_code == 200
        assert itsm_resp.get_json()["data"]["store_id"] == "T010"


class TestSalesBill:
    """销售单据测试。"""

    def test_create_and_audit(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/sales/bills",
            {"sltyp": "01", "custcd": "C0000001", "rgsqty": 10},
            headers,
        )
        assert resp.status_code == 201
        slbillid = resp.get_json()["data"]["slbillid"]

        resp2 = _post(client, f"/api/v1/sales/bills/{slbillid}/audit", {}, headers)
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["success"] is True

    def test_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get("/api/v1/sales/bills?page=1", headers=headers)
        assert resp.status_code == 200


class TestSalesExtend:
    """延期测试。"""

    def test_create_and_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/sales/extends",
            {
                "slbillid": "SL000001",
                "custcd": "C0000001",
                "busityp": "01",
                "details": [{"custcd": "C0000001", "custcard": "CK001"}],
            },
            headers,
        )
        assert resp.status_code == 201

        resp2 = client.get("/api/v1/sales/extends?page=1", headers=headers)
        assert resp2.status_code == 200
        assert "items" in resp2.get_json()["data"]


class TestPlanEndToEnd:
    """端到端测试：P0-P5 全链路联调（plantyp=00 新机开通）。"""

    @staticmethod
    def _seed_inventory(app: Flask) -> None:
        """插入测试基础数据：仓库、物料、EID、库存（幂等，先清后插）。"""
        from datetime import UTC, datetime as _dt

        from app.extensions import db as _db
        from app.models.master import Eid as EidModel, Item as ItemModel
        from app.models.warehouse import StockDetail as SdModel, Warehouse as WhModel

        with app.app_context():
            # 清理残留（前序测试 commit 后的持久数据）
            from app.models.sales import PlanCust as _PC, PlanServe as _PS
            from app.models.warehouse import StockOut as _SO
            from app.models.master import (
                Customer as _CUST, CustPosRl as _RL, EidTrack as _ET,
            )
            from app.models.itsm import MaintenanceOpen as _MO

            for tbl, flt in (
                (_ET, _ET.eid == "EID0000000001"),
                (_RL, _RL.eid == "EID0000000001"),
                (_MO, _MO.from_custcard == "HP001"),
                (_SO, _SO.refbillid.like("C%")),
                (_PS, _PS.planno.like("C%")),
                (_PC, _PC.custcard == "HP001"),
                (_CUST, _CUST.cust_card == "HP001"),
                (SdModel, SdModel.whcd == "W1"),
                (EidModel, EidModel.eid == "EID0000000001"),
                (ItemModel, ItemModel.item_cd == "IT0001"),
                (WhModel, WhModel.whcd == "W1"),
            ):
                _db.session.query(tbl).filter(flt).delete(synchronize_session=False)

            _db.session.add(WhModel(whcd="W1", whnm="测试仓库", useflg="1"))
            _db.session.add(ItemModel(item_cd="IT0001", item_nm="测试物料", useflg="1"))
            _db.session.add(EidModel(
                itemcd="IT0001", eid="EID0000000001",
                whcd="W1", sflg="8", useflg="1",
                opercd="T00001", gendate=_dt.now(UTC),
            ))
            _db.session.add(SdModel(
                whcd="W1", itemcd="IT0001", itemqty=10,
                opercd="T00001", gendate=_dt.now(UTC), useflg="1",
            ))
            _db.session.commit()

    def _create_and_implement(
        self, app: Flask, client: FlaskClient, headers: dict[str, str],
    ) -> tuple[str, str]:
        """创建预计划→呼出→流转02→实施，返回 (planno, downstream_id)。"""
        # 1. 创建预计划 plantyp=00，指定 posid（EID）
        resp = _post(
            client, "/api/v1/sales/plans",
            {
                "plantyp": "00", "custnm": "E2E测试", "custcd": "T010",
                "custcard": "HP001", "posid": "EID0000000001",
            },
            headers,
        )
        assert resp.status_code == 201, resp.get_json()
        planno = resp.get_json()["data"]["planno"]

        # 2. 呼出单 transition → 01
        serve_resp = client.get(f"/api/v1/sales/plans/{planno}/serve", headers=headers)
        serves = serve_resp.get_json()["data"]
        assert len(serves) >= 1
        _post(
            client, f"/api/v1/sales/plan-serve/{serves[0]['dtlid']}/transition",
            {"to_status": "01"}, headers,
        )

        # 3. 预计划 transition 00→02
        _post(client, f"/api/v1/sales/plans/{planno}/transition", {"to_status": "02"}, headers)

        # 4. 实施确认 → 04，生成下游 MO（P0）
        impl_resp = _post(client, f"/api/v1/sales/plans/{planno}/implement", {}, headers)
        assert impl_resp.status_code == 200
        impl_data = impl_resp.get_json()["data"]
        assert impl_data["to_status"] == "04"  # P0: 02→04
        downstream_id = impl_data["downstream_id"]
        assert downstream_id
        return planno, downstream_id

    def _create_and_audit_outbound(
        self, client: FlaskClient, headers: dict[str, str], planno: str,
    ) -> str:
        """生成出库草稿（P2）+ 仓库审核，返回 outbillid。"""
        out_resp = _post(
            client, f"/api/v1/sales/plans/{planno}/outbound",
            {"whcd": "W1", "eids": ["EID0000000001"]},
            headers,
        )
        assert out_resp.status_code == 201, out_resp.get_json()
        outbillid = out_resp.get_json()["data"]["outbillid"]
        assert outbillid  # P2: StockOutDetailEid 已写入

        audit_resp = _post(
            client, f"/api/v1/warehouse/stock-out/{outbillid}/audit",
            {"auditflg": "2"},
            headers,
        )
        assert audit_resp.status_code == 200, audit_resp.get_json()
        return outbillid

    def test_e2e_mo_close_path(self, app: Flask, client: FlaskClient) -> None:
        """路径 A：implement→出库→审核→MO关单（P0+P2+P3+P4，含回写 01）。"""
        self._seed_inventory(app)
        headers = _auth_header(app)

        planno, downstream_id = self._create_and_implement(app, client, headers)
        self._create_and_audit_outbound(client, headers, planno)

        # MO 状态机：1（新建）→ 2（分配）→ 5（已解决/关单）
        # 写 EidTrack type='C' (P3) + CustPosRl (P4) + 回写 plan_status='01' (P4)
        mo_resp1 = _post(
            client, f"/api/v1/itsm/maintenance-open/{downstream_id}/transition",
            {"to_status": "2"},
            headers,
        )
        assert mo_resp1.status_code == 200, mo_resp1.get_json()
        mo_resp = _post(
            client, f"/api/v1/itsm/maintenance-open/{downstream_id}/transition",
            {"to_status": "5"},
            headers,
        )
        assert mo_resp.status_code == 200, mo_resp.get_json()

        with app.app_context():
            from app.extensions import db as _db
            from app.models.master import CustPosRl as RlModel, EidTrack as EtModel
            from app.models.sales import PlanCust

            # P3: EidTrack type='C'
            tracks = _db.session.query(EtModel).filter(
                EtModel.eid == "EID0000000001"
            ).all()
            types = {t.type for t in tracks}
            assert "C" in types, f"P3: 缺少 type='C' 记录，实际: {types}"

            # P4: CustPosRl
            rl = _db.session.query(RlModel).filter(
                RlModel.eid == "EID0000000001", RlModel.useflg == "1"
            ).first()
            assert rl is not None, "P4: CustPosRl 未写入"
            assert rl.cust_cd == "T010"

            # P4: 回写 plan_status='01'
            plan = _db.session.query(PlanCust).filter(PlanCust.planno == planno).first()
            assert plan.plan_status == "01"

    def test_e2e_complete_path(self, app: Flask, client: FlaskClient) -> None:
        """路径 B：implement→出库→审核→complete（P0+P2+P5，写 type='u'）。"""
        self._seed_inventory(app)
        headers = _auth_header(app)

        planno, _downstream_id = self._create_and_implement(app, client, headers)
        self._create_and_audit_outbound(client, headers, planno)

        # 完成预计划 → 01，写 EidTrack type='u' (P5)
        complete_resp = _post(client, f"/api/v1/sales/plans/{planno}/complete", {}, headers)
        assert complete_resp.status_code == 200, complete_resp.get_json()
        assert complete_resp.get_json()["data"]["to_status"] == "01"

        with app.app_context():
            from app.extensions import db as _db
            from app.models.master import EidTrack as EtModel

            tracks = _db.session.query(EtModel).filter(
                EtModel.eid == "EID0000000001"
            ).all()
            types = {t.type for t in tracks}
            assert "u" in types, f"P5: 缺少 type='u' 记录，实际: {types}"
