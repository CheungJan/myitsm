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
        resp = _post(
            client, "/api/v1/sales/plans", {"plantyp": "10", "custnm": "流转测试"}, headers
        )
        planno = resp.get_json()["data"]["planno"]

        resp2 = _post(
            client, f"/api/v1/sales/plans/{planno}/transition", {"to_status": "02"}, headers
        )
        assert resp2.status_code == 200
        data = resp2.get_json()["data"]
        assert data["to_status"] == "02"

    def test_implement_without_serve_allowed(self, app: Flask, client: FlaskClient) -> None:
        """无已呼出记录时仍可实施（呼出为可选辅助流程，对齐 PB 设计）。"""
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/sales/plans",
            {"plantyp": "10", "custnm": "无呼出测试", "custcd": "T002"},
            headers,
        )
        planno = resp.get_json()["data"]["planno"]
        _post(client, f"/api/v1/sales/plans/{planno}/transition", {"to_status": "02"}, headers)

        resp3 = _post(client, f"/api/v1/sales/plans/{planno}/implement", {}, headers)
        assert resp3.status_code == 200, resp3.get_json()
        assert resp3.get_json()["data"]["to_status"] == "04"

    def test_void_cascade(self, app: Flask, client: FlaskClient) -> None:
        """作废 00 状态预计划。"""
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/sales/plans",
            {"plantyp": "20", "custnm": "作废测试", "custcd": "T003"},
            headers,
        )
        planno = resp.get_json()["data"]["planno"]

        resp2 = _post(client, f"/api/v1/sales/plans/{planno}/void", {"remark": "测试作废"}, headers)
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["to_status"] == "09"

    def test_complete_requires_02(self, app: Flask, client: FlaskClient) -> None:
        """00状态不能直接完成。"""
        headers = _auth_header(app)
        resp = _post(
            client, "/api/v1/sales/plans", {"plantyp": "10", "custnm": "完成测试"}, headers
        )
        planno = resp.get_json()["data"]["planno"]

        resp2 = _post(client, f"/api/v1/sales/plans/{planno}/complete", {}, headers)
        assert resp2.status_code == 400

    def test_implement_happy_path(self, app: Flask, client: FlaskClient) -> None:
        """正向链路：创建→呼出→实施→下游工单生成且imple_billid回写。"""
        headers = _auth_header(app)

        # 1. 创建预计划 plantyp=00 (新机开通)
        resp = _post(
            client,
            "/api/v1/sales/plans",
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
        from datetime import UTC
        from datetime import datetime as _dt

        from app.extensions import db as _db
        from app.models.master import Eid as EidModel
        from app.models.master import Item as ItemModel
        from app.models.warehouse import StockDetail as SdModel
        from app.models.warehouse import Warehouse as WhModel

        with app.app_context():
            # 清理残留（前序测试 commit 后的持久数据）
            from app.models.itsm import MaintenanceOpen as _MO
            from app.models.master import Customer as _CUST
            from app.models.master import CustPosRl as _RL
            from app.models.master import EidTrack as _ET
            from app.models.sales import PlanCust as _PC
            from app.models.sales import PlanServe as _PS
            from app.models.warehouse import StockOut as _SO

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
            _db.session.add(
                EidModel(
                    itemcd="IT0001",
                    eid="EID0000000001",
                    whcd="W1",
                    sflg="8",
                    useflg="1",
                    opercd="T00001",
                    gendate=_dt.now(UTC),
                )
            )
            _db.session.add(
                SdModel(
                    whcd="W1",
                    itemcd="IT0001",
                    itemqty=10,
                    opercd="T00001",
                    gendate=_dt.now(UTC),
                    useflg="1",
                )
            )
            _db.session.commit()

    def _create_and_implement(
        self,
        app: Flask,
        client: FlaskClient,
        headers: dict[str, str],
    ) -> tuple[str, str]:
        """创建预计划→呼出→流转02→实施，返回 (planno, downstream_id)。"""
        # 1. 创建预计划 plantyp=00，指定 posid（EID）
        resp = _post(
            client,
            "/api/v1/sales/plans",
            {
                "plantyp": "00",
                "custnm": "E2E测试",
                "custcd": "T010",
                "custcard": "HP001",
                "posid": "EID0000000001",
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
            client,
            f"/api/v1/sales/plan-serve/{serves[0]['dtlid']}/transition",
            {"to_status": "01"},
            headers,
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
        self,
        client: FlaskClient,
        headers: dict[str, str],
        planno: str,
    ) -> str:
        """审核出库单（P2）—— 方案 A：implement 已自动创建出库单，直接查询并审核。"""
        from app.extensions import db as _db
        from app.models.warehouse import StockOut

        outbillid = (
            _db.session.query(StockOut.outbillid)
            .filter(StockOut.refbillid == planno, StockOut.invtyp == "1")
            .scalar()
        )
        assert outbillid, f"方案 A 自动出库未生成，planno={planno}"

        audit_resp = _post(
            client,
            f"/api/v1/warehouse/stock-out/{outbillid}/audit",
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
            client,
            f"/api/v1/itsm/maintenance-open/{downstream_id}/transition",
            {"to_status": "2"},
            headers,
        )
        assert mo_resp1.status_code == 200, mo_resp1.get_json()
        mo_resp = _post(
            client,
            f"/api/v1/itsm/maintenance-open/{downstream_id}/transition",
            {"to_status": "5"},
            headers,
        )
        assert mo_resp.status_code == 200, mo_resp.get_json()

        with app.app_context():
            from app.extensions import db as _db
            from app.models.master import CustPosRl as RlModel
            from app.models.master import EidTrack as EtModel
            from app.models.sales import PlanCust

            # P3: EidTrack type='C'
            tracks = _db.session.query(EtModel).filter(EtModel.eid == "EID0000000001").all()
            types = {t.type for t in tracks}
            assert "C" in types, f"P3: 缺少 type='C' 记录，实际: {types}"

            # P4: CustPosRl
            rl = (
                _db.session.query(RlModel)
                .filter(RlModel.eid == "EID0000000001", RlModel.useflg == "1")
                .first()
            )
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

            tracks = _db.session.query(EtModel).filter(EtModel.eid == "EID0000000001").all()
            types = {t.type for t in tracks}
            assert "u" in types, f"P5: 缺少 type='u' 记录，实际: {types}"

    @staticmethod
    def _seed_renovate_inventory(app: Flask) -> None:
        """插入 plantyp=20 翻新链路测试数据：仓库、物料、旧机/新机 EID、库存。"""
        from datetime import UTC
        from datetime import datetime as _dt

        from app.extensions import db as _db
        from app.models.itsm import MaintenanceRenovate as _MR
        from app.models.master import Customer as _CUST
        from app.models.master import CustPosRl as _RL
        from app.models.master import Eid as EidModel
        from app.models.master import EidTrack as _ET
        from app.models.master import Item as ItemModel
        from app.models.sales import PlanCust as _PC
        from app.models.sales import PlanServe as _PS
        from app.models.warehouse import StockDetail as SdModel
        from app.models.warehouse import Warehouse as WhModel

        with app.app_context():
            # 清理残留
            for tbl, flt in (
                (_ET, _ET.eid.in_(["EIDOLD0000020", "EIDNEW0000020"])),
                (_RL, _RL.eid.in_(["EIDOLD0000020", "EIDNEW0000020"])),
                (_MR, _MR.store_id == "T020"),
                (_PS, _PS.planno.like("C20%")),
                (_PC, _PC.custcard == "HP020"),
                (_CUST, _CUST.cust_card == "HP020"),
                (SdModel, SdModel.whcd == "W20"),
                (EidModel, EidModel.eid.in_(["EIDOLD0000020", "EIDNEW0000020"])),
                (ItemModel, ItemModel.item_cd == "IT0020"),
                (WhModel, WhModel.whcd == "W20"),
            ):
                _db.session.query(tbl).filter(flt).delete(synchronize_session=False)

            _db.session.add(WhModel(whcd="W20", whnm="翻新测试仓库", useflg="1"))
            _db.session.add(ItemModel(item_cd="IT0020", item_nm="翻新测试物料", useflg="1"))
            # 旧机 EID（已绑定到门店）
            _db.session.add(
                EidModel(
                    itemcd="IT0020",
                    eid="EIDOLD0000020",
                    whcd="W20",
                    sflg="1",
                    useflg="1",
                    opercd="T00001",
                    gendate=_dt.now(UTC),
                )
            )
            # 新机 EID（在库）
            _db.session.add(
                EidModel(
                    itemcd="IT0020",
                    eid="EIDNEW0000020",
                    whcd="W20",
                    sflg="8",
                    useflg="1",
                    opercd="T00001",
                    gendate=_dt.now(UTC),
                )
            )
            _db.session.add(
                SdModel(
                    whcd="W20",
                    itemcd="IT0020",
                    itemqty=10,
                    opercd="T00001",
                    gendate=_dt.now(UTC),
                    useflg="1",
                )
            )
            _db.session.commit()

    def test_e2e_renovate_close_path(self, app: Flask, client: FlaskClient) -> None:
        """plantyp=20 E2E：预计划→实施→翻新单关单。

        验证 11c：R+C track + rl 旧机失效/新机新建 + 回写。
        """
        self._seed_renovate_inventory(app)
        headers = _auth_header(app)

        # 1. 创建预计划 plantyp=20，指定 posid（旧机 EID），用新磁卡号避免冲突
        resp = _post(
            client,
            "/api/v1/sales/plans",
            {
                "plantyp": "20",
                "custnm": "翻新E2E",
                "custcd": "T020",
                "custcard": "HP020",
                "posid": "EIDOLD0000020",
            },
            headers,
        )
        assert resp.status_code == 201, resp.get_json()
        planno = resp.get_json()["data"]["planno"]

        # 预计划创建 TEMP 客户 T020 后，手动插入旧机 rl（模拟旧机已绑定到门店）
        with app.app_context():
            from datetime import UTC
            from datetime import datetime as _dt

            from app.extensions import db as _db
            from app.models.master import CustPosRl as _RL

            _db.session.add(
                _RL(
                    cust_cd="T020",
                    eid="EIDOLD0000020",
                    item_cd="IT0020",
                    useflg="1",
                    posupddate=_dt.now(UTC),
                    asset_status="ACTIVE",
                    created_from="MAINTENANCE_OPEN",
                )
            )
            _db.session.commit()

        # 2. 呼出单 transition → 01
        serve_resp = client.get(f"/api/v1/sales/plans/{planno}/serve", headers=headers)
        serves = serve_resp.get_json()["data"]
        assert len(serves) >= 1
        _post(
            client,
            f"/api/v1/sales/plan-serve/{serves[0]['dtlid']}/transition",
            {"to_status": "01"},
            headers,
        )

        # 3. 预计划 transition 00→02
        _post(client, f"/api/v1/sales/plans/{planno}/transition", {"to_status": "02"}, headers)

        # 4. 实施确认 → 04，生成下游翻新单
        impl_resp = _post(client, f"/api/v1/sales/plans/{planno}/implement", {}, headers)
        assert impl_resp.status_code == 200, impl_resp.get_json()
        impl_data = impl_resp.get_json()["data"]
        assert impl_data["to_status"] == "04"
        downstream_id = impl_data["downstream_id"]
        assert downstream_id

        # 翻新单创建时只有 old_device_id，人工分配新机后更新 new_device_id
        with app.app_context():
            from app.extensions import db as _db
            from app.models.itsm import MaintenanceRenovate as _MR

            renovate = _db.session.get(_MR, downstream_id)
            assert renovate is not None
            renovate.new_device_id = "EIDNEW0000020"
            _db.session.commit()

        # 5. 翻新单状态机：1→2→5（关单）
        _post(
            client,
            f"/api/v1/itsm/maintenance-renovate/{downstream_id}/transition",
            {"to_status": "2"},
            headers,
        )
        close_resp = _post(
            client,
            f"/api/v1/itsm/maintenance-renovate/{downstream_id}/transition",
            {"to_status": "5"},
            headers,
        )
        assert close_resp.status_code == 200, close_resp.get_json()

        with app.app_context():
            from app.extensions import db as _db
            from app.models.master import CustPosRl as RlModel
            from app.models.master import EidTrack as EtModel
            from app.models.sales import PlanCust

            # 11c: 旧机写 type='R'，新机写 type='C'
            tracks = (
                _db.session.query(EtModel)
                .filter(EtModel.eid.in_(["EIDOLD0000020", "EIDNEW0000020"]))
                .all()
            )
            types_by_eid: dict[str, set[str]] = {}
            for t in tracks:
                types_by_eid.setdefault(t.eid, set()).add(t.type)
            assert "R" in types_by_eid.get(
                "EIDOLD0000020", set()
            ), f"11c: 旧机缺少 type='R'，实际: {types_by_eid}"
            assert "C" in types_by_eid.get(
                "EIDNEW0000020", set()
            ), f"11c: 新机缺少 type='C'，实际: {types_by_eid}"

            # 11c: 旧机 rl 失效
            old_rl = (
                _db.session.query(RlModel)
                .filter(
                    RlModel.eid == "EIDOLD0000020",
                    RlModel.useflg == "0",
                )
                .first()
            )
            assert old_rl is not None, "11c: 旧机 rl 未失效"
            assert old_rl.asset_status == "RETURNED"

            # 11c: 新机 rl 新建
            new_rl = (
                _db.session.query(RlModel)
                .filter(
                    RlModel.eid == "EIDNEW0000020",
                    RlModel.cust_cd == "T020",
                    RlModel.useflg == "1",
                )
                .first()
            )
            assert new_rl is not None, "11c: 新机 rl 未新建"
            assert new_rl.asset_status == "ACTIVE"

            # 11c: 回写 plan_status='01'
            plan = _db.session.query(PlanCust).filter(PlanCust.planno == planno).first()
            assert plan.plan_status == "01"

    @staticmethod
    def _seed_recycle_inventory(app: Flask) -> None:
        """插入 plantyp=30 回收链路测试数据：仓库、物料、EID、库存。"""
        from datetime import UTC
        from datetime import datetime as _dt

        from app.extensions import db as _db
        from app.models.itsm import RecycleTask as _RT
        from app.models.itsm import RecycleTaskDtl as _RTD
        from app.models.master import Customer as _CUST
        from app.models.master import CustPosRl as _RL
        from app.models.master import Eid as EidModel
        from app.models.master import EidTrack as _ET
        from app.models.master import Item as ItemModel
        from app.models.sales import PlanCust as _PC
        from app.models.sales import PlanServe as _PS
        from app.models.warehouse import StockDetail as SdModel
        from app.models.warehouse import Warehouse as WhModel

        with app.app_context():
            for tbl, flt in (
                (_ET, _ET.eid == "EIDRCY0000030"),
                (_RL, _RL.eid == "EIDRCY0000030"),
                (_RTD, _RTD.recycle_id.like("R%")),
                (_RT, _RT.cust_cd == "T030"),
                (_PS, _PS.planno.like("C30%")),
                (_PC, _PC.custcard == "HP030"),
                (_CUST, _CUST.cust_card == "HP030"),
                (SdModel, SdModel.whcd == "W30"),
                (EidModel, EidModel.eid == "EIDRCY0000030"),
                (ItemModel, ItemModel.item_cd == "IT0030"),
                (WhModel, WhModel.whcd == "W30"),
            ):
                _db.session.query(tbl).filter(flt).delete(synchronize_session=False)

            _db.session.add(WhModel(whcd="W30", whnm="回收测试仓库", useflg="1"))
            _db.session.add(ItemModel(item_cd="IT0030", item_nm="回收测试物料", useflg="1"))
            _db.session.add(
                EidModel(
                    itemcd="IT0030",
                    eid="EIDRCY0000030",
                    whcd="W30",
                    sflg="1",
                    useflg="1",
                    opercd="T00001",
                    gendate=_dt.now(UTC),
                )
            )
            _db.session.add(
                SdModel(
                    whcd="W30",
                    itemcd="IT0030",
                    itemqty=10,
                    opercd="T00001",
                    gendate=_dt.now(UTC),
                    useflg="1",
                )
            )
            _db.session.commit()

    def test_e2e_recycle_close_path(self, app: Flask, client: FlaskClient) -> None:
        """plantyp=30 E2E：预计划→实施→回收任务关单（11d：R track + rl 失效 + 回写）。"""
        self._seed_recycle_inventory(app)
        headers = _auth_header(app)

        # 1. 创建预计划 plantyp=30
        resp = _post(
            client,
            "/api/v1/sales/plans",
            {
                "plantyp": "30",
                "custnm": "回收E2E",
                "custcd": "T030",
                "custcard": "HP030",
            },
            headers,
        )
        assert resp.status_code == 201, resp.get_json()
        planno = resp.get_json()["data"]["planno"]

        # 预计划创建 TEMP 客户 T030 后，插入旧机 rl（模拟设备已绑定到门店）
        with app.app_context():
            from datetime import UTC
            from datetime import datetime as _dt

            from app.extensions import db as _db
            from app.models.master import CustPosRl as _RL

            _db.session.add(
                _RL(
                    cust_cd="T030",
                    eid="EIDRCY0000030",
                    item_cd="IT0030",
                    useflg="1",
                    posupddate=_dt.now(UTC),
                    asset_status="ACTIVE",
                    created_from="MAINTENANCE_OPEN",
                )
            )
            _db.session.commit()

        # 2. 呼出单 transition → 01
        serve_resp = client.get(f"/api/v1/sales/plans/{planno}/serve", headers=headers)
        serves = serve_resp.get_json()["data"]
        assert len(serves) >= 1
        _post(
            client,
            f"/api/v1/sales/plan-serve/{serves[0]['dtlid']}/transition",
            {"to_status": "01"},
            headers,
        )

        # 3. 预计划 transition 00→02
        _post(client, f"/api/v1/sales/plans/{planno}/transition", {"to_status": "02"}, headers)

        # 4. 实施确认 → 04，生成下游回收任务
        impl_resp = _post(client, f"/api/v1/sales/plans/{planno}/implement", {}, headers)
        assert impl_resp.status_code == 200, impl_resp.get_json()
        impl_data = impl_resp.get_json()["data"]
        downstream_id = impl_data["downstream_id"]
        assert downstream_id

        # 回收任务创建时无明细，人工添加回收明细（asset_id）
        with app.app_context():
            from app.extensions import db as _db
            from app.repositories.itsm_repository import RecycleTaskRepository

            RecycleTaskRepository.add_detail(
                downstream_id,
                {
                    "asset_id": "EIDRCY0000030",
                    "warehouse_cd": "W30",
                },
            )
            _db.session.commit()

        # 5. 回收任务状态机：1→2→5（关单）
        _post(
            client,
            f"/api/v1/itsm/recycle-task/{downstream_id}/transition",
            {"to_status": "2"},
            headers,
        )
        close_resp = _post(
            client,
            f"/api/v1/itsm/recycle-task/{downstream_id}/transition",
            {"to_status": "5"},
            headers,
        )
        assert close_resp.status_code == 200, close_resp.get_json()

        with app.app_context():
            from app.extensions import db as _db
            from app.models.master import CustPosRl as RlModel
            from app.models.master import EidTrack as EtModel
            from app.models.sales import PlanCust

            # 11d: 写 type='R'
            tracks = (
                _db.session.query(EtModel)
                .filter(EtModel.eid == "EIDRCY0000030", EtModel.type == "R")
                .all()
            )
            assert len(tracks) >= 1, "11d: 缺少 type='R' 记录"

            # 11d: rl 失效
            old_rl = (
                _db.session.query(RlModel)
                .filter(
                    RlModel.eid == "EIDRCY0000030",
                    RlModel.useflg == "0",
                )
                .first()
            )
            assert old_rl is not None, "11d: rl 未失效"
            assert old_rl.asset_status == "RETURNED"

            # 11d: 回写 plan_status='01'
            plan = _db.session.query(PlanCust).filter(PlanCust.planno == planno).first()
            assert plan.plan_status == "01"

    @staticmethod
    def _seed_store_close_inventory(app: Flask) -> None:
        """插入 plantyp=40 门店关闭链路测试数据：仓库、物料、EID、库存。"""
        from datetime import UTC
        from datetime import datetime as _dt

        from app.extensions import db as _db
        from app.models.itsm import StoreClose as _SC
        from app.models.master import Customer as _CUST
        from app.models.master import CustPosRl as _RL
        from app.models.master import Eid as EidModel
        from app.models.master import EidTrack as _ET
        from app.models.master import Item as ItemModel
        from app.models.sales import PlanCust as _PC
        from app.models.sales import PlanServe as _PS
        from app.models.warehouse import StockDetail as SdModel
        from app.models.warehouse import Warehouse as WhModel

        with app.app_context():
            for tbl, flt in (
                (_ET, _ET.eid == "EIDCL0000040"),
                (_RL, _RL.eid == "EIDCL0000040"),
                (_SC, _SC.store_id == "T040"),
                (_PS, _PS.planno.like("C40%")),
                (_PC, _PC.custcard == "HP040"),
                (_CUST, _CUST.cust_card == "HP040"),
                (SdModel, SdModel.whcd == "W40"),
                (EidModel, EidModel.eid == "EIDCL0000040"),
                (ItemModel, ItemModel.item_cd == "IT0040"),
                (WhModel, WhModel.whcd == "W40"),
            ):
                _db.session.query(tbl).filter(flt).delete(synchronize_session=False)

            _db.session.add(WhModel(whcd="W40", whnm="关店测试仓库", useflg="1"))
            _db.session.add(ItemModel(item_cd="IT0040", item_nm="关店测试物料", useflg="1"))
            _db.session.add(
                EidModel(
                    itemcd="IT0040",
                    eid="EIDCL0000040",
                    whcd="W40",
                    sflg="1",
                    useflg="1",
                    opercd="T00001",
                    gendate=_dt.now(UTC),
                )
            )
            _db.session.add(
                SdModel(
                    whcd="W40",
                    itemcd="IT0040",
                    itemqty=10,
                    opercd="T00001",
                    gendate=_dt.now(UTC),
                    useflg="1",
                )
            )
            _db.session.commit()

    def test_e2e_store_close_path(self, app: Flask, client: FlaskClient) -> None:
        """plantyp=40 E2E：预计划→实施→门店关闭关单（11e：R track 批量 + rl 全失效 + 回写）。"""
        self._seed_store_close_inventory(app)
        headers = _auth_header(app)

        # 1. 创建预计划 plantyp=40
        resp = _post(
            client,
            "/api/v1/sales/plans",
            {
                "plantyp": "40",
                "custnm": "关店E2E",
                "custcd": "T040",
                "custcard": "HP040",
            },
            headers,
        )
        assert resp.status_code == 201, resp.get_json()
        planno = resp.get_json()["data"]["planno"]

        # 预计划创建 TEMP 客户 T040 后，插入设备 rl（模拟设备已绑定到门店）
        with app.app_context():
            from datetime import UTC
            from datetime import datetime as _dt

            from app.extensions import db as _db
            from app.models.master import CustPosRl as _RL

            _db.session.add(
                _RL(
                    cust_cd="T040",
                    eid="EIDCL0000040",
                    item_cd="IT0040",
                    useflg="1",
                    posupddate=_dt.now(UTC),
                    asset_status="ACTIVE",
                    created_from="MAINTENANCE_OPEN",
                )
            )
            _db.session.commit()

        # 2. 呼出单 transition → 01
        serve_resp = client.get(f"/api/v1/sales/plans/{planno}/serve", headers=headers)
        serves = serve_resp.get_json()["data"]
        assert len(serves) >= 1
        _post(
            client,
            f"/api/v1/sales/plan-serve/{serves[0]['dtlid']}/transition",
            {"to_status": "01"},
            headers,
        )

        # 3. 预计划 transition 00→02
        _post(client, f"/api/v1/sales/plans/{planno}/transition", {"to_status": "02"}, headers)

        # 4. 实施确认 → 04，生成下游门店关闭单
        impl_resp = _post(client, f"/api/v1/sales/plans/{planno}/implement", {}, headers)
        assert impl_resp.status_code == 200, impl_resp.get_json()
        impl_data = impl_resp.get_json()["data"]
        downstream_id = impl_data["downstream_id"]
        assert downstream_id

        # 5. 门店关闭单状态机：1→2→5（关单）
        _post(
            client,
            f"/api/v1/itsm/store-close/{downstream_id}/transition",
            {"to_status": "2"},
            headers,
        )
        close_resp = _post(
            client,
            f"/api/v1/itsm/store-close/{downstream_id}/transition",
            {"to_status": "5"},
            headers,
        )
        assert close_resp.status_code == 200, close_resp.get_json()

        with app.app_context():
            from app.extensions import db as _db
            from app.models.master import CustPosRl as RlModel
            from app.models.master import EidTrack as EtModel
            from app.models.sales import PlanCust

            # 11e: 写 type='R'（批量，本例 1 个 EID）
            tracks = (
                _db.session.query(EtModel)
                .filter(EtModel.eid == "EIDCL0000040", EtModel.type == "R")
                .all()
            )
            assert len(tracks) >= 1, "11e: 缺少 type='R' 记录"

            # 11e: rl 全失效
            old_rl = (
                _db.session.query(RlModel)
                .filter(
                    RlModel.eid == "EIDCL0000040",
                    RlModel.useflg == "0",
                )
                .first()
            )
            assert old_rl is not None, "11e: rl 未失效"
            assert old_rl.asset_status == "RETURNED"

            # 11e: 回写 plan_status='01'
            plan = _db.session.query(PlanCust).filter(PlanCust.planno == planno).first()
            assert plan.plan_status == "01"
