"""租金/费用结算 API 测试（Tier-2 G4）。"""

from __future__ import annotations

from typing import Any

from flask.testing import FlaskClient


class TestBillingRuleAPI:
    """结算规则测试。"""

    def test_create_rule(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/billing/rules",
            json={
                "rule_id": "R001",
                "rule_name": "月租金规则",
                "billing_type": "RENT",
                "cycle_type": "MONTHLY",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["rule_name"] == "月租金规则"

    def test_list_rules(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/billing/rules",
            json={"rule_id": "R002", "rule_name": "季度结算", "billing_type": "RENT"},
            headers=auth_header,
        )
        resp = client.get("/api/v1/billing/rules", headers=auth_header)
        assert resp.status_code == 200

    def test_update_rule(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/billing/rules",
            json={"rule_id": "R003", "rule_name": "服务费", "billing_type": "SERVICE"},
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/billing/rules/R003",
            json={"remark": "更新测试"},
            headers=auth_header,
        )
        assert resp.status_code == 200

    def test_get_rule_not_found(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.get("/api/v1/billing/rules/NOTEXIST", headers=auth_header)
        assert resp.status_code == 404


class TestBillAPI:
    """账单测试。"""

    def test_create_bill(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/billing/bills",
            json={
                "bill_id": "B20260401",
                "custcd": "C001",
                "billing_type": "RENT",
                "bill_date": "2026-04-01",
                "total_amount": 5000,
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["custcd"] == "C001"

    def test_list_bills(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/billing/bills",
            json={
                "bill_id": "B20260402",
                "custcd": "C002",
                "billing_type": "RENT",
                "bill_date": "2026-04-01",
            },
            headers=auth_header,
        )
        resp = client.get("/api/v1/billing/bills", headers=auth_header)
        assert resp.status_code == 200

    def test_update_bill(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/billing/bills",
            json={
                "bill_id": "B20260403",
                "custcd": "C003",
                "billing_type": "SALE",
                "bill_date": "2026-04-01",
            },
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/billing/bills/B20260403",
            json={"status": "SENT"},
            headers=auth_header,
        )
        assert resp.status_code == 200

    def test_get_bill_not_found(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.get("/api/v1/billing/bills/NOTEXIST", headers=auth_header)
        assert resp.status_code == 404


class TestBillingBatchAPI:
    """结算批次测试。"""

    def test_create_batch(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/billing/batches",
            json={
                "batch_id": "BAT20260401",
                "batch_date": "2026-04-01",
                "billing_type": "RENT",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_batches(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/billing/batches",
            json={"batch_id": "BAT20260402", "batch_date": "2026-04-02"},
            headers=auth_header,
        )
        resp = client.get("/api/v1/billing/batches", headers=auth_header)
        assert resp.status_code == 200

    def test_update_batch(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/billing/batches",
            json={"batch_id": "BAT20260403", "batch_date": "2026-04-03"},
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/billing/batches/BAT20260403",
            json={"status": "COMPLETED"},
            headers=auth_header,
        )
        assert resp.status_code == 200
