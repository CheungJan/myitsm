"""通知/消息系统 API 测试。"""

from __future__ import annotations

from typing import Any

from flask.testing import FlaskClient


class TestNotificationTemplateAPI:
    """通知模板测试。"""

    def test_create_template(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/notification/notification-templates",
            json={
                "template_name": "工单通知",
                "channel": "sms",
                "subject": "工单状态变更",
                "body": "您的工单 {ticket_id} 已变更为 {status}",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["template_name"] == "工单通知"

    def test_list_templates(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/notification/notification-templates",
            json={"template_name": "邮件通知", "channel": "email"},
            headers=auth_header,
        )
        resp = client.get("/api/v1/notification/notification-templates", headers=auth_header)
        assert resp.status_code == 200

    def test_update_template(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/notification/notification-templates",
            json={"template_name": "站内通知", "channel": "internal"},
            headers=auth_header,
        )
        tid = resp.get_json()["data"]["template_id"]
        resp2 = client.put(
            f"/api/v1/notification/notification-templates/{tid}",
            json={"subject": "新标题"},
            headers=auth_header,
        )
        assert resp2.status_code == 200


class TestNotificationAPI:
    """通知记录测试。"""

    def test_create_notification(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/notification/notifications",
            json={
                "channel": "sms",
                "recipient": "13800138000",
                "subject": "测试通知",
                "body": "这是一条测试通知",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_notifications(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/notification/notifications",
            json={"channel": "email", "recipient": "test@test.com"},
            headers=auth_header,
        )
        resp = client.get("/api/v1/notification/notifications", headers=auth_header)
        assert resp.status_code == 200

    def test_send_notification(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/notification/notifications",
            json={"channel": "internal", "recipient": "user01", "body": "hello"},
            headers=auth_header,
        )
        nid = resp.get_json()["data"]["id"]
        resp2 = client.post(
            f"/api/v1/notification/notifications/{nid}/send",
            headers=auth_header,
        )
        assert resp2.status_code == 200
        data: dict[str, Any] = resp2.get_json()
        assert data["data"]["send_status"] == "sent"
