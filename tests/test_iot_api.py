"""IoT 数据监控 API 测试（Tier-3 G8）。"""

from __future__ import annotations

from typing import Any

from flask.testing import FlaskClient


class TestDeviceConnAPI:
    """设备接入测试。"""

    def test_create_connection(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/iot/connections",
            json={
                "conn_id": "CONN001",
                "eid": "DEV001",
                "protocol": "MQTT",
                "topic": "device/DEV001/data",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["protocol"] == "MQTT"

    def test_list_connections(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/iot/connections",
            json={"conn_id": "CONN002", "eid": "DEV002"},
            headers=auth_header,
        )
        resp = client.get("/api/v1/iot/connections", headers=auth_header)
        assert resp.status_code == 200

    def test_update_connection(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/iot/connections",
            json={"conn_id": "CONN003", "eid": "DEV003"},
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/iot/connections/CONN003",
            json={"online_status": "ONLINE"},
            headers=auth_header,
        )
        assert resp.status_code == 200

    def test_get_connection_not_found(
        self, client: FlaskClient, auth_header: dict[str, str]
    ) -> None:
        resp = client.get("/api/v1/iot/connections/NOTEXIST", headers=auth_header)
        assert resp.status_code == 404


class TestDeviceDataAPI:
    """设备数据测试。"""

    def test_report_data(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/iot/data",
            json={
                "eid": "DEV001",
                "data_type": "TEMPERATURE",
                "data_value": "25.5",
                "data_unit": "℃",
                "report_time": "2026-04-27T10:00:00",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_device_data(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.get("/api/v1/iot/data/DEV001", headers=auth_header)
        assert resp.status_code == 200


class TestAlertRuleAPI:
    """报警规则测试。"""

    def test_create_alert_rule(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/iot/alert-rules",
            json={
                "rule_id": "ALR001",
                "rule_name": "温度过高",
                "data_type": "TEMPERATURE",
                "condition_type": "GT",
                "threshold_max": 80,
                "severity": "CRITICAL",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_alert_rules(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/iot/alert-rules",
            json={
                "rule_id": "ALR002",
                "rule_name": "离线检测",
                "data_type": "STATUS",
                "condition_type": "OFFLINE",
            },
            headers=auth_header,
        )
        resp = client.get("/api/v1/iot/alert-rules", headers=auth_header)
        assert resp.status_code == 200

    def test_update_alert_rule(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/iot/alert-rules",
            json={
                "rule_id": "ALR003",
                "rule_name": "压力过低",
                "data_type": "PRESSURE",
                "condition_type": "LT",
            },
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/iot/alert-rules/ALR003",
            json={"threshold_min": 10},
            headers=auth_header,
        )
        assert resp.status_code == 200


class TestAlertLogAPI:
    """报警记录测试。"""

    def test_list_alerts(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.get("/api/v1/iot/alerts", headers=auth_header)
        assert resp.status_code == 200
