"""采购管理 API 测试。"""

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


class TestPurchasePlan:
    """采购计划测试。"""

    def test_create_and_get(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/procurement/plans",
            {
                "pctyp": "1",
                "memo": "采购计划测试",
                "details": [{"itemcd": "IT0001", "rgstqty": 50, "units": "台"}],
            },
            headers,
        )
        assert resp.status_code == 201
        pcplanid = resp.get_json()["data"]["pcplanid"]

        resp2 = client.get(f"/api/v1/procurement/plans/{pcplanid}", headers=headers)
        assert resp2.status_code == 200

    def test_audit(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/procurement/plans",
            {"pctyp": "1", "details": [{"itemcd": "IT0002", "rgstqty": 20}]},
            headers,
        )
        pcplanid = resp.get_json()["data"]["pcplanid"]

        resp2 = _post(client, f"/api/v1/procurement/plans/{pcplanid}/audit", {}, headers)
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["success"] is True

    def test_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get("/api/v1/procurement/plans?page=1&per_page=10", headers=headers)
        assert resp.status_code == 200
        assert "items" in resp.get_json()["data"]


class TestPurchaseRegister:
    """采购登记测试。"""

    def test_create(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/procurement/registers",
            {
                "suppliercd": "SUP00001",
                "details": [{"itemcd": "IT0001", "rgsqty": 30}],
            },
            headers,
        )
        assert resp.status_code == 201


class TestPurchaseBill:
    """采购单据测试。"""

    def test_create(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/procurement/bills",
            {"pctyp": "01", "whcd": "01"},
            headers,
        )
        assert resp.status_code == 201


class TestSupplierAppraisal:
    """供应商评价测试。"""

    def test_create_and_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/procurement/supplier-appraisals",
            {
                "sdate": "2026-01-01",
                "edate": "2026-03-31",
                "details": [{"supplierid": "SUP00001", "appscore": 85}],
            },
            headers,
        )
        assert resp.status_code == 201

        resp2 = client.get("/api/v1/procurement/supplier-appraisals", headers=headers)
        assert resp2.status_code == 200
