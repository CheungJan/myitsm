"""仓储管理 API 测试。"""

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


class TestWarehouse:
    """仓库主数据测试。"""

    def test_create_and_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/warehouse/warehouses",
            {"whcd": "01", "whnm": "主仓库", "whtyp": "01"},
            headers,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["data"]["whcd"] == "01"

        resp2 = client.get("/api/v1/warehouse/warehouses", headers=headers)
        assert resp2.status_code == 200
        assert len(resp2.get_json()["data"]) >= 1

    def test_get_warehouse(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get("/api/v1/warehouse/warehouses/01", headers=headers)
        assert resp.status_code == 200


class TestStockIn:
    """入库单测试。"""

    def test_create_and_audit(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        # 确保仓库存在
        _post(
            client,
            "/api/v1/warehouse/warehouses",
            {"whcd": "02", "whnm": "入库测试仓"},
            headers,
        )
        resp = _post(
            client,
            "/api/v1/warehouse/stock-in",
            {
                "whcd": "02",
                "invtyp": "1",
                "details": [{"itemcd": "IT0001", "inqty": 10}],
            },
            headers,
        )
        assert resp.status_code == 201
        inbillid = resp.get_json()["data"]["inbillid"]

        resp2 = _post(
            client,
            f"/api/v1/warehouse/stock-in/{inbillid}/audit",
            {},
            headers,
        )
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["success"] is True

    def test_list_stock_in(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get("/api/v1/warehouse/stock-in?page=1&per_page=10", headers=headers)
        assert resp.status_code == 200
        assert "items" in resp.get_json()["data"]


class TestStockOut:
    """出库单测试。"""

    def test_create_and_audit(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        _post(
            client,
            "/api/v1/warehouse/warehouses",
            {"whcd": "03", "whnm": "出库测试仓"},
            headers,
        )
        resp = _post(
            client,
            "/api/v1/warehouse/stock-out",
            {
                "whcd": "03",
                "invtyp": "1",
                "details_eid": [{"itemcd": "IT0002", "outqty": 5}],
            },
            headers,
        )
        assert resp.status_code == 201
        outbillid = resp.get_json()["data"]["outbillid"]

        resp2 = _post(
            client,
            f"/api/v1/warehouse/stock-out/{outbillid}/audit",
            {},
            headers,
        )
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["success"] is True


class TestStockBalance:
    """库存查询测试。"""

    def test_query_stock(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get("/api/v1/warehouse/stock?whcd=02", headers=headers)
        assert resp.status_code == 200
