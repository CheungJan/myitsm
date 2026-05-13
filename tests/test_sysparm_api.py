"""系统参数更新 API 测试。"""
import json
from typing import Any

import jwt
import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.extensions import db as _db
from app.models.system import SysParm  # noqa: F401 — 触发表注册


@pytest.fixture
def app() -> Flask:
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        # 插入单例种子数据
        if not _db.session.get(SysParm, "SYSPARM"):
            _db.session.add(SysParm(
                parm_cd="SYSPARM", parm_nm="SYSPARM", costtype="1",
                poinvaliddays=1, soinvaliddays=1, allowmultilogon="1",
                shopbilltype="1", centralwarehouse="",
            ))
            _db.session.commit()
    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


def _auth_header(app: Flask) -> dict[str, str]:
    payload = {"sub": "T00001", "exp": 9999999999}
    token: str = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}", "X-User-Cd": "T00001"}


def _put(client: FlaskClient, url: str, data: dict[str, Any], headers: dict[str, str]) -> Any:
    return client.put(url, data=json.dumps(data), content_type="application/json", headers=headers)


def test_update_sysparm_success(app: Flask, client: FlaskClient):
    """PUT /sysparms/SYSPARM 应正确更新参数值。"""
    headers = _auth_header(app)
    resp = _put(client, "/api/v1/sysparms/SYSPARM", {"costtype": "2", "poinvaliddays": 30}, headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == 200
    assert data["data"]["costtype"] == "2"
    assert data["data"]["poinvaliddays"] == 30


def test_update_sysparm_not_found(app: Flask, client: FlaskClient):
    """PUT /sysparms/NOEXIST 应返回 404。"""
    headers = _auth_header(app)
    resp = _put(client, "/api/v1/sysparms/NOEXIST", {"costtype": "2"}, headers)
    assert resp.status_code == 404


def test_sysparm_requires_auth(client: FlaskClient):
    """未登录调用应返回 401。"""
    resp = client.put("/api/v1/sysparms/SYSPARM", data=json.dumps({"costtype": "2"}), content_type="application/json")
    assert resp.status_code == 401
