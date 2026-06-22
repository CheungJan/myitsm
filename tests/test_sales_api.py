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

    def test_transition_00_to_01(self, app: Flask, client: FlaskClient) -> None:
        """状态流转 00→01。"""
        headers = _auth_header(app)
        resp = _post(client, "/api/v1/sales/plans", {"plantyp": "10", "custnm": "流转测试"}, headers)
        planno = resp.get_json()["data"]["planno"]

        resp2 = _post(client, f"/api/v1/sales/plans/{planno}/transition", {"to_status": "01"}, headers)
        assert resp2.status_code == 200
        data = resp2.get_json()["data"]
        assert data["to_status"] == "01"

    def test_implement_without_serve_blocks(self, app: Flask, client: FlaskClient) -> None:
        """无已呼出记录时实施被拒绝。"""
        headers = _auth_header(app)
        resp = _post(client, "/api/v1/sales/plans", {"plantyp": "10", "custnm": "无呼出测试", "custcd": "T002"}, headers)
        planno = resp.get_json()["data"]["planno"]
        _post(client, f"/api/v1/sales/plans/{planno}/transition", {"to_status": "01"}, headers)

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
