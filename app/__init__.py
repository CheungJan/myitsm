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
    from app.api.attendance import attendance_bp
    from app.api.auth import auth_bp
    from app.api.billing import billing_bp
    from app.api.contract import contract_bp
    from app.api.deposit import deposit_bp
    from app.api.finance import finance_bp
    from app.api.health import health_bp
    from app.api.inventory import inventory_bp
    from app.api.iot import iot_bp
    from app.api.itsm import itsm_bp
    from app.api.mes import mes_bp
    from app.api.notification import notification_bp
    from app.api.portal import portal_bp
    from app.api.procurement import procurement_bp
    from app.api.reports import report_bp
    from app.api.sales import sales_bp
    from app.api.sla import sla_bp
    from app.api.system import system_bp
    from app.api.transactions import transaction_bp
    from app.api.warehouse import warehouse_bp

    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(system_bp, url_prefix="/api/v1")
    app.register_blueprint(itsm_bp, url_prefix="/api/v1/itsm")
    app.register_blueprint(warehouse_bp, url_prefix="/api/v1/warehouse")
    app.register_blueprint(procurement_bp, url_prefix="/api/v1/procurement")
    app.register_blueprint(sales_bp, url_prefix="/api/v1/sales")
    app.register_blueprint(sla_bp, url_prefix="/api/v1/sla")
    app.register_blueprint(attendance_bp, url_prefix="/api/v1/attendance")
    app.register_blueprint(inventory_bp, url_prefix="/api/v1/inventory")
    app.register_blueprint(deposit_bp, url_prefix="/api/v1/deposit")
    app.register_blueprint(contract_bp, url_prefix="/api/v1/contract")
    app.register_blueprint(notification_bp, url_prefix="/api/v1/notification")
    # Tier-2 扩展
    app.register_blueprint(billing_bp, url_prefix="/api/v1/billing")
    app.register_blueprint(finance_bp, url_prefix="/api/v1/finance")
    app.register_blueprint(portal_bp, url_prefix="/api/v1/portal")
    # Tier-3 扩展
    app.register_blueprint(mes_bp, url_prefix="/api/v1/mes")
    app.register_blueprint(iot_bp, url_prefix="/api/v1/iot")
    # 事务查询与报表
    app.register_blueprint(transaction_bp, url_prefix="/api/v1/transactions")
    app.register_blueprint(report_bp, url_prefix="/api/v1/reports")


def _make_error_body(code: int, message: str) -> dict[str, Any]:
    """构造统一错误响应体：{ code, message, data, request_id }。"""
    return {
        "code": code,
        "message": message,
        "data": None,
        "request_id": getattr(g, "request_id", ""),
    }


def _register_error_handlers(app: Flask) -> None:
    """注册全局错误处理。"""

    @app.errorhandler(400)
    def bad_request(exc: Exception) -> tuple[Any, int]:
        return jsonify(_make_error_body(400, str(exc))), 400

    @app.errorhandler(401)
    def unauthorized(exc: Exception) -> tuple[Any, int]:
        return jsonify(_make_error_body(401, "未授权")), 401

    @app.errorhandler(403)
    def forbidden(exc: Exception) -> tuple[Any, int]:
        return jsonify(_make_error_body(403, "无权限")), 403

    @app.errorhandler(404)
    def not_found(exc: Exception) -> tuple[Any, int]:
        return jsonify(_make_error_body(404, "资源不存在")), 404

    @app.errorhandler(Exception)
    def handle_exception(exc: Exception) -> tuple[Any, int]:
        request_id = getattr(g, "request_id", "")
        logger.exception("请求处理异常，request_id=%s", request_id)
        return jsonify(_make_error_body(500, "服务器内部错误")), 500


def _register_before_request(app: Flask) -> None:
    """注册请求前钩子。"""

    @app.before_request
    def bind_request_id() -> None:
        g.request_id = str(uuid.uuid4())
