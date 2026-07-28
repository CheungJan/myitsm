"""采购管理 API 测试。"""

from __future__ import annotations

import json
from typing import Any

from flask import Flask
from flask.testing import FlaskClient

from app.extensions import db as _db


def _ensure_execution_view(app: Flask) -> None:
    """确保 v_requisition_execution 视图存在（SQLite 兼容）。"""
    with app.app_context():
        _db.session.execute(_db.text("DROP VIEW IF EXISTS v_requisition_execution"))
        _db.session.execute(_db.text("""
            CREATE VIEW v_requisition_execution AS
            SELECT
                p.pcplanid, p.plandate, p.auditflg, p.auditman, p.auditdate, p.useflg,
                dt.lineno, dt.itemcd, i.item_nm AS itemnm, i.spec, i.wunit,
                dt.rgstqty AS plan_qty,
                dt.auditqty AS audit_qty,
                COALESCE(link_stats.ordered_qty, 0) AS ordered_qty,
                COALESCE(link_stats.received_qty, 0) AS received_qty,
                dt.auditqty - COALESCE(link_stats.ordered_qty, 0) AS available_qty,
                CASE
                    WHEN COALESCE(link_stats.ordered_qty, 0) = 0 THEN '未开始'
                    WHEN COALESCE(link_stats.received_qty, 0) >= dt.rgstqty THEN '已完成'
                    WHEN COALESCE(link_stats.received_qty, 0) > 0 THEN '执行中'
                    ELSE '已下单'
                END AS execution_status,
                CASE WHEN dt.rgstqty > 0
                    THEN ROUND(CAST(COALESCE(link_stats.received_qty, 0) AS REAL) / dt.rgstqty * 100, 2)
                    ELSE 0
                END AS execution_rate
            FROM tpc01_pcplan p
            JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
            LEFT JOIN tmm12_items i ON dt.itemcd = i.item_cd
            LEFT JOIN (
                SELECT l.pcplanid, l.pclineno,
                    SUM(l.linkqty) AS ordered_qty,
                    SUM(CASE WHEN rd.inqty >= rd.rgsqty THEN l.linkqty ELSE 0 END) AS received_qty
                FROM tpc20_requisition_order_link l
                JOIN tpc13_registerdt rd ON l.rgstbillid = rd.rgstbillid AND l.rgstlineno = rd.lineno
                JOIN tpc12_register r ON rd.rgstbillid = r.rgstbillid
                WHERE r.useflg <> '9'
                GROUP BY l.pcplanid, l.pclineno
            ) link_stats ON dt.pcplanid = link_stats.pcplanid AND dt.lineno = link_stats.pclineno
            WHERE p.useflg = '1'
        """))
        _db.session.commit()


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
        _ensure_execution_view(app)
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/procurement/requisitions",
            {
                "pctyp": "1",
                "memo": "采购计划测试",
                "details": [{"itemcd": "IT0001", "rgstqty": 50, "units": "台"}],
            },
            headers,
        )
        assert resp.status_code == 201
        pcplanid = resp.get_json()["data"]["pcplanid"]

        resp2 = client.get(f"/api/v1/procurement/requisitions/{pcplanid}", headers=headers)
        assert resp2.status_code == 200

    def test_audit(self, app: Flask, client: FlaskClient) -> None:
        _ensure_execution_view(app)
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/procurement/requisitions",
            {"pctyp": "1", "details": [{"itemcd": "IT0002", "rgstqty": 20}]},
            headers,
        )
        pcplanid = resp.get_json()["data"]["pcplanid"]

        resp2 = _post(client, f"/api/v1/procurement/requisitions/{pcplanid}/audit", {}, headers)
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["success"] is True

    def test_list(self, app: Flask, client: FlaskClient) -> None:
        _ensure_execution_view(app)
        headers = _auth_header(app)
        resp = client.get("/api/v1/procurement/requisitions?page=1&per_page=10", headers=headers)
        assert resp.status_code == 200
        assert "items" in resp.get_json()["data"]


class TestPurchaseRegister:
    """采购登记测试。"""

    def test_create(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/procurement/orders",
            {
                "suppliercd": "SUP00001",
                "details": [{"itemcd": "IT0001", "rgsqty": 30}],
            },
            headers,
        )
        assert resp.status_code == 201


class TestPurchaseBill:
    """采购结算单测试。"""

    def test_list(self, app: Flask, client: FlaskClient) -> None:
        """结算单列表可正常访问。"""
        headers = _auth_header(app)
        resp = client.get("/api/v1/procurement/settlements?page=1&per_page=10", headers=headers)
        assert resp.status_code == 200
        assert "items" in resp.get_json()["data"]


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
