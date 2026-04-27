"""ITSM 核心 API 测试。"""

from __future__ import annotations

import json
from typing import Any

from flask import Flask
from flask.testing import FlaskClient


def _auth_header(app: Flask) -> dict[str, str]:
    """生成 JWT 认证头。"""
    import jwt  # type: ignore[import-untyped]

    payload = {"sub": "T00001", "exp": 9999999999}
    token: str = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}", "X-User-Cd": "T00001"}


def _post(client: FlaskClient, url: str, data: dict[str, Any], headers: dict[str, str]) -> Any:
    return client.post(url, data=json.dumps(data), content_type="application/json", headers=headers)


# ---------------------------------------------------------------------------
# 日常维护单
# ---------------------------------------------------------------------------


class TestMaintenanceDaily:
    """日常维护单 CRUD + 状态流转测试。"""

    def test_create_and_get(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/maintenance-daily",
            {
                "store_id": "S0000001",
                "fault_type": "01",
                "short_description": "POS机无法开机",
            },
            headers,
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["code"] == 201
        mid = body["data"]["maintenance_id"]

        resp2 = client.get(f"/api/v1/itsm/maintenance-daily/{mid}", headers=headers)
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["store_id"] == "S0000001"

    def test_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get("/api/v1/itsm/maintenance-daily?page=1&per_page=10", headers=headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "items" in body["data"]
        assert "total" in body["data"]

    def test_transition_valid(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/maintenance-daily",
            {"store_id": "S0000002", "short_description": "测试状态流转"},
            headers,
        )
        mid = resp.get_json()["data"]["maintenance_id"]

        resp2 = _post(
            client,
            f"/api/v1/itsm/maintenance-daily/{mid}/transition",
            {"to_status": "01"},
            headers,
        )
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["success"] is True

    def test_transition_invalid(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/maintenance-daily",
            {"store_id": "S0000003"},
            headers,
        )
        mid = resp.get_json()["data"]["maintenance_id"]

        resp2 = _post(
            client,
            f"/api/v1/itsm/maintenance-daily/{mid}/transition",
            {"to_status": "05"},
            headers,
        )
        assert resp2.status_code == 400

    def test_update(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/maintenance-daily",
            {"store_id": "S0000004"},
            headers,
        )
        mid = resp.get_json()["data"]["maintenance_id"]

        resp2 = client.put(
            f"/api/v1/itsm/maintenance-daily/{mid}",
            data=json.dumps({"memo": "更新测试"}),
            content_type="application/json",
            headers=headers,
        )
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["memo"] == "更新测试"


# ---------------------------------------------------------------------------
# 公用附表
# ---------------------------------------------------------------------------


class TestD2D:
    """上门服务记录测试。"""

    def test_create_and_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/d2d",
            {
                "maintenance_id": "MD000001",
                "d2d_engineer": "E00001",
                "d2d_type": "1",
                "d2d_descripiton": "到店检修",
            },
            headers,
        )
        assert resp.status_code == 200

        resp2 = client.get("/api/v1/itsm/d2d/MD000001", headers=headers)
        assert resp2.status_code == 200
        items = resp2.get_json()["data"]
        assert len(items) >= 1


class TestCloseBill:
    """关单记录测试。"""

    def test_create_and_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/close-bill",
            {"maintenance_id": "MD000002", "close_type": "01", "description": "正常关单"},
            headers,
        )
        assert resp.status_code == 200

        resp2 = client.get("/api/v1/itsm/close-bill/MD000002", headers=headers)
        assert resp2.status_code == 200
        items = resp2.get_json()["data"]
        assert len(items) >= 1


class TestDispatch:
    """分派记录测试。"""

    def test_create_and_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/dispatch",
            {
                "maintenance_id": "MD000003",
                "maintenance_type": "MD",
                "accpectder": "E00002",
            },
            headers,
        )
        assert resp.status_code == 200

        resp2 = client.get("/api/v1/itsm/dispatch/MD000003", headers=headers)
        assert resp2.status_code == 200


# ---------------------------------------------------------------------------
# 设备变更单
# ---------------------------------------------------------------------------


class TestDeviceChange:
    """设备变更单 CRUD + CK 磁卡号历史优化测试。"""

    def test_create_ck(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/device-change",
            {
                "store_id": "S0000010",
                "change_type": "CK",
                "new_store_card": "NEWCARD001",
                "short_description": "磁卡号变更",
            },
            headers,
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["change_type"] == "CK"

    def test_list_with_type_filter(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get(
            "/api/v1/itsm/device-change?change_type=CK",
            headers=headers,
        )
        assert resp.status_code == 200
