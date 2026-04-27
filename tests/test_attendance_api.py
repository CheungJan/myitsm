"""考勤管理 API 测试。"""

from __future__ import annotations

from typing import Any

from flask.testing import FlaskClient


class TestAttendanceAPI:
    """考勤记录测试。"""

    def test_create_attendance(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/attendance/attendance",
            json={
                "amonth": "202604",
                "adate": "2026-04-01",
                "operid": "U001",
                "opernm": "张三",
                "latecount": 0,
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["operid"] == "U001"

    def test_list_attendance(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/attendance/attendance",
            json={"amonth": "202604", "adate": "2026-04-02", "operid": "U002"},
            headers=auth_header,
        )
        resp = client.get("/api/v1/attendance/attendance?amonth=202604", headers=auth_header)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["total"] >= 1

    def test_list_attendance_missing_amonth(
        self, client: FlaskClient, auth_header: dict[str, str]
    ) -> None:
        resp = client.get("/api/v1/attendance/attendance", headers=auth_header)
        assert resp.status_code == 400

    def test_list_attendance_summary(
        self, client: FlaskClient, auth_header: dict[str, str]
    ) -> None:
        resp = client.get(
            "/api/v1/attendance/attendance/summary?amonth=202604",
            headers=auth_header,
        )
        assert resp.status_code == 200
