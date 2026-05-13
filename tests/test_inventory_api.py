"""库存预警与价格管理 API 测试。"""

from __future__ import annotations

from typing import Any

from flask.testing import FlaskClient


class TestInventoryLimitAPI:
    """库存预警测试。"""

    def test_create_limit(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/inventory/inventory-limits",
            json={"itemcd": "IT001", "invlow": 10, "invhigh": 100},
            headers=auth_header,
        )
        assert resp.status_code == 201
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["itemcd"] == "IT001"

    def test_list_limits(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/inventory/inventory-limits",
            json={"itemcd": "IT002", "invlow": 5},
            headers=auth_header,
        )
        resp = client.get("/api/v1/inventory/inventory-limits", headers=auth_header)
        assert resp.status_code == 200

    def test_update_limit(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/inventory/inventory-limits",
            json={"itemcd": "IT003", "invlow": 20},
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/inventory/inventory-limits/IT003",
            json={"invhigh": 200},
            headers=auth_header,
        )
        assert resp.status_code == 200


class TestPriceAPI:
    """价格规则测试。"""

    def test_create_price(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/inventory/prices",
            json={"itemcd": "IT001", "busityp": "01", "itemprice": 99.99},
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_prices(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/inventory/prices",
            json={"itemcd": "IT002", "busityp": "02"},
            headers=auth_header,
        )
        resp = client.get("/api/v1/inventory/prices", headers=auth_header)
        assert resp.status_code == 200

    def test_update_price(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/inventory/prices",
            json={"itemcd": "IT004", "busityp": "01"},
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/inventory/prices/IT004/01",
            json={"itemprice": 150},
            headers=auth_header,
        )
        assert resp.status_code == 200


class TestAdjustPriceAPI:
    """调价记录测试。"""

    def test_create_adjust_price(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/inventory/adjust-prices",
            json={"lineno": 1, "itemcd": "IT001", "oldprice": 100, "newprice": 120},
            headers=auth_header,
        )
        assert resp.status_code == 201
