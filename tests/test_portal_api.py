"""客户自助服务门户 API 测试（Tier-2 G9）。"""

from __future__ import annotations

from typing import Any

from flask.testing import FlaskClient


class TestPortalUserAPI:
    """门户用户测试。"""

    def test_create_user(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/portal/users",
            json={
                "portal_uid": "PU001",
                "custcd": "C001",
                "login_name": "customer1",
                "password": "Test@12345",
                "contact_name": "张三",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["login_name"] == "customer1"

    def test_list_users(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/portal/users",
            json={
                "portal_uid": "PU002",
                "custcd": "C002",
                "login_name": "customer2",
                "password": "Test@12345",
            },
            headers=auth_header,
        )
        resp = client.get("/api/v1/portal/users", headers=auth_header)
        assert resp.status_code == 200

    def test_update_user(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/portal/users",
            json={
                "portal_uid": "PU003",
                "custcd": "C003",
                "login_name": "customer3",
                "password": "Test@12345",
            },
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/portal/users/PU003",
            json={"phone": "13800138000"},
            headers=auth_header,
        )
        assert resp.status_code == 200

    def test_get_user_not_found(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.get("/api/v1/portal/users/NOTEXIST", headers=auth_header)
        assert resp.status_code == 404


class TestRepairRequestAPI:
    """自助报修测试。"""

    def test_create_repair(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/portal/repairs",
            json={
                "request_id": "REQ001",
                "portal_uid": "PU001",
                "custcd": "C001",
                "fault_desc": "设备无法启动",
                "urgency": "HIGH",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["urgency"] == "HIGH"

    def test_list_repairs(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/portal/repairs",
            json={
                "request_id": "REQ002",
                "portal_uid": "PU001",
                "custcd": "C001",
                "fault_desc": "显示异常",
            },
            headers=auth_header,
        )
        resp = client.get("/api/v1/portal/repairs", headers=auth_header)
        assert resp.status_code == 200

    def test_update_repair(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/portal/repairs",
            json={
                "request_id": "REQ003",
                "portal_uid": "PU001",
                "custcd": "C001",
                "fault_desc": "网络故障",
            },
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/portal/repairs/REQ003",
            json={"status": "ACCEPTED"},
            headers=auth_header,
        )
        assert resp.status_code == 200

    def test_get_repair_not_found(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.get("/api/v1/portal/repairs/NOTEXIST", headers=auth_header)
        assert resp.status_code == 404


class TestServiceRatingAPI:
    """服务评价测试。"""

    def test_create_rating(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/portal/ratings",
            json={
                "request_id": "REQ001",
                "portal_uid": "PU001",
                "custcd": "C001",
                "rating": 5,
                "quality_rating": 4,
                "comment": "服务很好",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_ratings(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.get("/api/v1/portal/ratings?custcd=C001", headers=auth_header)
        assert resp.status_code == 200
