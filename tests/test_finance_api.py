"""财务应收应付 API 测试（Tier-2 G5）。"""

from __future__ import annotations

from typing import Any

from flask.testing import FlaskClient


class TestAccountAPI:
    """会计科目测试。"""

    def test_create_account(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/finance/accounts",
            json={
                "account_cd": "1001",
                "account_nm": "应收账款",
                "account_type": "AR",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["account_nm"] == "应收账款"

    def test_list_accounts(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/finance/accounts",
            json={"account_cd": "2001", "account_nm": "应付账款", "account_type": "AP"},
            headers=auth_header,
        )
        resp = client.get("/api/v1/finance/accounts", headers=auth_header)
        assert resp.status_code == 200

    def test_update_account(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/finance/accounts",
            json={"account_cd": "3001", "account_nm": "收入", "account_type": "INCOME"},
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/finance/accounts/3001",
            json={"remark": "更新"},
            headers=auth_header,
        )
        assert resp.status_code == 200


class TestReceivableAPI:
    """应收测试。"""

    def test_create_receivable(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/finance/receivables",
            json={
                "ar_id": "AR001",
                "custcd": "C001",
                "ar_date": "2026-04-01",
                "amount": 10000,
            },
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_receivables(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/finance/receivables",
            json={"ar_id": "AR002", "custcd": "C002", "ar_date": "2026-04-01", "amount": 5000},
            headers=auth_header,
        )
        resp = client.get("/api/v1/finance/receivables", headers=auth_header)
        assert resp.status_code == 200

    def test_update_receivable(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/finance/receivables",
            json={"ar_id": "AR003", "custcd": "C003", "ar_date": "2026-04-01", "amount": 8000},
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/finance/receivables/AR003",
            json={"status": "PAID", "paid_amount": 8000},
            headers=auth_header,
        )
        assert resp.status_code == 200


class TestPayableAPI:
    """应付测试。"""

    def test_create_payable(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/finance/payables",
            json={
                "ap_id": "AP001",
                "supp_cd": "S001",
                "ap_date": "2026-04-01",
                "amount": 20000,
            },
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_payables(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/finance/payables",
            json={"ap_id": "AP002", "supp_cd": "S002", "ap_date": "2026-04-01", "amount": 15000},
            headers=auth_header,
        )
        resp = client.get("/api/v1/finance/payables", headers=auth_header)
        assert resp.status_code == 200


class TestPaymentAPI:
    """收付款测试。"""

    def test_create_payment(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/finance/payments",
            json={
                "pay_id": "PAY001",
                "pay_type": "RECEIVE",
                "pay_date": "2026-04-01",
                "amount": 10000,
            },
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_payments(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/finance/payments",
            json={"pay_id": "PAY002", "pay_type": "PAY", "pay_date": "2026-04-01", "amount": 5000},
            headers=auth_header,
        )
        resp = client.get("/api/v1/finance/payments", headers=auth_header)
        assert resp.status_code == 200


class TestDepreciationAPI:
    """折旧测试。"""

    def test_create_depreciation(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/finance/depreciations",
            json={
                "eid": "EID001",
                "original_value": 50000,
                "salvage_value": 5000,
                "useful_life_months": 60,
            },
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_depreciations(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.get("/api/v1/finance/depreciations", headers=auth_header)
        assert resp.status_code == 200
