"""合同与发票管理 API 测试。"""

from __future__ import annotations

from typing import Any

from flask.testing import FlaskClient


class TestContractAPI:
    """合同管理测试。"""

    def test_create_contract(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/contract/contracts",
            json={
                "years": "2026",
                "classcd": "A01",
                "busityp": "01",
                "feetyp": "01",
                "qdis": "1",
                "htbgr": "张三",
                "htamount": 50000,
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["years"] == "2026"

    def test_list_contracts(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/contract/contracts",
            json={"years": "2026", "classcd": "B01"},
            headers=auth_header,
        )
        resp = client.get("/api/v1/contract/contracts", headers=auth_header)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["total"] >= 1

    def test_update_contract(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/contract/contracts",
            json={"years": "2026", "classcd": "C01"},
            headers=auth_header,
        )
        htbh = resp.get_json()["data"]["htbh"]
        resp2 = client.put(
            f"/api/v1/contract/contracts/{htbh}",
            json={"remark": "更新测试"},
            headers=auth_header,
        )
        assert resp2.status_code == 200

    def test_get_contract_not_found(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.get("/api/v1/contract/contracts/NOTEXIST", headers=auth_header)
        assert resp.status_code == 404


class TestInvoiceAPI:
    """发票管理测试。"""

    def test_create_invoice(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/contract/invoices",
            json={
                "years": "2026",
                "classcd": "A01",
                "kpamount": 10000,
            },
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_invoices(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/contract/invoices",
            json={"years": "2026"},
            headers=auth_header,
        )
        resp = client.get("/api/v1/contract/invoices", headers=auth_header)
        assert resp.status_code == 200

    def test_update_invoice(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/contract/invoices",
            json={"years": "2026", "classcd": "D01"},
            headers=auth_header,
        )
        fpbh = resp.get_json()["data"]["fpbh"]
        resp2 = client.put(
            f"/api/v1/contract/invoices/{fpbh}",
            json={"remark": "发票备注"},
            headers=auth_header,
        )
        assert resp2.status_code == 200
