"""
应用工厂。

Flask 应用创建入口，注册扩展、蓝图、错误处理和中间件。
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from flask import Flask, g, jsonify

from app.config import config_map
from app.extensions import cors, db, migrate

__all__ = ["create_app"]

logger = logging.getLogger(__name__)


def create_app(config_name: str | None = None) -> Flask:
    """创建 Flask 应用实例。"""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map["development"]))

    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_before_request(app)

    return app


def _init_extensions(app: Flask) -> None:
    """初始化扩展。"""
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})


def _register_blueprints(app: Flask) -> None:
    """注册蓝图。"""
    from app.api.auth import auth_bp
    from app.api.health import health_bp
    from app.api.system import system_bp

    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(system_bp, url_prefix="/api/v1")


def _register_error_handlers(app: Flask) -> None:
    """注册全局错误处理。"""

    @app.errorhandler(400)
    def bad_request(exc: Exception) -> tuple[Any, int]:
        return (
            jsonify(
                {
                    "code": 400,
                    "message": str(exc),
                    "data": {"request_id": getattr(g, "request_id", "")},
                }
            ),
            400,
        )

    @app.errorhandler(401)
    def unauthorized(exc: Exception) -> tuple[Any, int]:
        return (
            jsonify(
                {
                    "code": 401,
                    "message": "未授权",
                    "data": {"request_id": getattr(g, "request_id", "")},
                }
            ),
            401,
        )

    @app.errorhandler(403)
    def forbidden(exc: Exception) -> tuple[Any, int]:
        return (
            jsonify(
                {
                    "code": 403,
                    "message": "无权限",
                    "data": {"request_id": getattr(g, "request_id", "")},
                }
            ),
            403,
        )

    @app.errorhandler(404)
    def not_found(exc: Exception) -> tuple[Any, int]:
        return (
            jsonify(
                {
                    "code": 404,
                    "message": "资源不存在",
                    "data": {"request_id": getattr(g, "request_id", "")},
                }
            ),
            404,
        )

    @app.errorhandler(Exception)
    def handle_exception(exc: Exception) -> tuple[Any, int]:
        request_id = getattr(g, "request_id", "")
        logger.exception("请求处理异常，request_id=%s", request_id)
        return (
            jsonify(
                {
                    "code": 500,
                    "message": "服务器内部错误",
                    "data": {"request_id": request_id},
                }
            ),
            500,
        )


def _register_before_request(app: Flask) -> None:
    """注册请求前钩子。"""

    @app.before_request
    def bind_request_id() -> None:
        g.request_id = str(uuid.uuid4())
