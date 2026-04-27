"""押金管理 API 测试。"""

from __future__ import annotations

from typing import Any

from flask.testing import FlaskClient


class TestDepositAPI:
    """押金主记录测试。"""

    def test_create_deposit(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/deposit/deposits",
            json={"custcd": "C0001", "amount_money": 5000},
            headers=auth_header,
        )
        assert resp.status_code == 201
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["custcd"] == "C0001"

    def test_list_deposits(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/deposit/deposits",
            json={"custcd": "C0002", "amount_money": 3000},
            headers=auth_header,
        )
        resp = client.get("/api/v1/deposit/deposits", headers=auth_header)
        assert resp.status_code == 200

    def test_update_deposit(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/deposit/deposits",
            json={"custcd": "C0003", "amount_money": 2000},
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/deposit/deposits/C0003",
            json={"amount_money": 2500},
            headers=auth_header,
        )
        assert resp.status_code == 200


class TestDepositDetailAPI:
    """押金变更明细测试。"""

    def test_create_deposit_detail(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/deposit/deposits",
            json={"custcd": "C0010"},
            headers=auth_header,
        )
        resp = client.post(
            "/api/v1/deposit/deposits/details",
            json={"custcd": "C0010", "c_type": "IN", "change_a": 1000},
            headers=auth_header,
        )
        assert resp.status_code == 201


class TestDepositPosModelAPI:
    """设备型号押金标准测试。"""

    def test_create_pos_model(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/deposit/deposit-models",
            json={"model_cd": "POS001", "model_nm": "标准POS", "rent_money": 100},
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_pos_models(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/deposit/deposit-models",
            json={"model_cd": "POS002", "model_nm": "高级POS"},
            headers=auth_header,
        )
        resp = client.get("/api/v1/deposit/deposit-models", headers=auth_header)
        assert resp.status_code == 200
