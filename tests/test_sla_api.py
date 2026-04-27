"""SLA 服务级别管理 API 测试。"""

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


class TestSlaDefinition:
    """SLA定义测试。"""

    def test_create_and_get(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/sla/definitions",
            {
                "sla_name": "标准SLA",
                "priority": "2",
                "response_minutes": 60,
                "resolve_minutes": 480,
                "escalation_minutes": 120,
                "description": "标准优先级SLA协议",
            },
            headers,
        )
        assert resp.status_code == 201
        sla_id = resp.get_json()["data"]["sla_id"]

        resp2 = client.get(f"/api/v1/sla/definitions/{sla_id}", headers=headers)
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["sla_name"] == "标准SLA"

    def test_update(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/sla/definitions",
            {
                "sla_name": "高优先级SLA",
                "priority": "1",
                "response_minutes": 15,
                "resolve_minutes": 120,
            },
            headers,
        )
        sla_id = resp.get_json()["data"]["sla_id"]

        resp2 = client.put(
            f"/api/v1/sla/definitions/{sla_id}",
            data=json.dumps({"response_minutes": 10, "description": "紧急响应"}),
            content_type="application/json",
            headers=headers,
        )
        assert resp2.status_code == 200

    def test_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get("/api/v1/sla/definitions", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.get_json()["data"], list)


class TestSlaTicket:
    """SLA工单监控测试。"""

    def test_attach_and_respond(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        # 先创建SLA定义
        _post(
            client,
            "/api/v1/sla/definitions",
            {
                "sla_name": "测试SLA",
                "priority": "3",
                "response_minutes": 120,
                "resolve_minutes": 960,
            },
            headers,
        )

        # 绑定SLA到工单
        resp = _post(
            client,
            "/api/v1/sla/tickets/attach",
            {
                "maintenance_id": "MD000010",
                "maintenance_type": "DAILY",
                "priority": "3",
            },
            headers,
        )
        assert resp.status_code == 201
        assert resp.get_json()["data"]["success"] is True

        # 记录首次响应
        resp2 = _post(
            client,
            "/api/v1/sla/tickets/response",
            {"maintenance_id": "MD000010", "maintenance_type": "DAILY"},
            headers,
        )
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["success"] is True

        # 记录解决
        resp3 = _post(
            client,
            "/api/v1/sla/tickets/resolve",
            {"maintenance_id": "MD000010", "maintenance_type": "DAILY"},
            headers,
        )
        assert resp3.status_code == 200
        assert resp3.get_json()["data"]["success"] is True

    def test_list_tickets(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get("/api/v1/sla/tickets?page=1", headers=headers)
        assert resp.status_code == 200
        assert "items" in resp.get_json()["data"]

    def test_compliance_stats(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get("/api/v1/sla/stats", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "total_closed" in data
        assert "response_rate" in data
        assert "resolve_rate" in data
