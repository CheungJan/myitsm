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
def _rollback(app: Flask) -> Generator[None, None, None]:
    """每个测试结束后回滚，保证隔离。"""
    with app.app_context():
        yield
        _db.session.rollback()


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """创建测试客户端。"""
    return app.test_client()
