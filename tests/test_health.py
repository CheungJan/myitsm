"""健康检查接口测试。"""

from __future__ import annotations

from flask.testing import FlaskClient


def test_health_check(client: FlaskClient) -> None:
    """测试健康检查接口。"""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data is not None
    assert data["code"] == 200
    assert data["data"]["status"] == "ok"
