"""测试配置。"""

from __future__ import annotations

from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app() -> Generator[Flask, None, None]:
    """创建测试应用。"""
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(autouse=True)
def _clean_db(app: Flask) -> Generator[None, None, None]:
    """每个测试开始前清空所有表数据，保证隔离。

    简单可靠：测试内可自由 commit，下一测试开始时全表清空。
    """
    with app.app_context():
        # 测试前清空所有表
        _db.session.remove()
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()
        yield
        # 测试后也清理，避免污染 session 级状态
        _db.session.remove()


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """创建测试客户端。"""
    return app.test_client()


@pytest.fixture()
def auth_header(app: Flask) -> dict[str, str]:
    """生成 JWT 认证头。"""
    import jwt

    payload = {"sub": "T00001", "exp": 9999999999}
    token: str = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}", "X-User-Cd": "T00001"}
