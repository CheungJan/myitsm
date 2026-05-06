"""
应用工厂与全局中间件。
作者：Cascade
创建时间：2026-03-24
变更时间：2026-04-08（注册客户/资产/回收任务/预计划/维修单/设备变更单/新机开通/旧机翻新/日常保养蓝图）
注意事项：统一注入 request_id，并提供统一 JSON 错误响应结构。
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from flask import Flask, g, jsonify

from app.api.asset import asset_bp
from app.api.accessories_update_report import accessories_update_report_bp
from app.api.asset_audit import asset_audit_bp
from app.api.auth import auth_bp
from app.api.codetable import codetable_bp
from app.api.customer import customer_bp
from app.api.device_change import device_change_bp
from app.api.dispatch_report import dispatch_report_bp
from app.api.ex_gh import ex_gh_bp
from app.api.free_replace import free_replace_bp
from app.api.liability import liability_bp
from app.api.liability_group import liability_group_bp
from app.api.liability_sum import liability_sum_bp
from app.api.maintenance import maintenance_bp
from app.api.maintenance_daily import maintenance_daily_bp
from app.api.maintenance_open import maintenance_open_bp
from app.api.maintenance_plan import maintenance_plan_bp
from app.api.maintenance_renovate import maintenance_renovate_bp
from app.api.paper_average_report import paper_average_report_bp
from app.api.pos_r_eid_update import pos_r_eid_update_bp
from app.api.preplan import preplan_bp
from app.api.recycle_task import recycle_task_bp
from app.api.rep_cust_info import rep_cust_info_bp
from app.api.rep_liability_report import rep_liability_report_bp
from app.api.rep_maintenance_daily import rep_maintenance_daily_bp
from app.api.rep_maintenance_daily_m import rep_maintenance_daily_m_bp
from app.api.rep_maintenance_daily_ym import rep_maintenance_daily_ym_bp
from app.api.shell import shell_bp
from app.api.store_close import store_close_bp
from app.api.timepoint_levels import timepoint_levels_bp
from app.api.user_group import user_group_bp

__all__ = ["create_app"]

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """
    创建 Flask 应用实例并注册基础组件。

    返回值：
        Flask: 应用实例。

    异常：
        RuntimeError: 初始化关键组件失败时抛出。
    """
    app = Flask(__name__)

    @app.before_request
    def _bind_request_id() -> None:
        """
        为当前请求注入 request_id。

        返回值：
            None
        """
        g.request_id = str(uuid.uuid4())

    @app.errorhandler(Exception)
    def _handle_exception(exc: Exception) -> tuple[Any, int]:
        """
        处理未捕获异常并返回统一错误结构。

        参数：
            exc: 未捕获异常对象。

        返回值：
            tuple[Any, int]: JSON 响应与 HTTP 状态码。
        """
        request_id = getattr(g, "request_id", "")
        logger.exception("请求处理异常，request_id=%s", request_id)
        payload = {
            "code": 500,
            "message": "服务器内部错误",
            "data": {"request_id": request_id},
        }
        return jsonify(payload), 500

    app.register_blueprint(asset_bp, url_prefix="/api/v1")
    app.register_blueprint(accessories_update_report_bp, url_prefix="/api/v1")
    app.register_blueprint(asset_audit_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(codetable_bp, url_prefix="/api/v1")
    app.register_blueprint(customer_bp, url_prefix="/api/v1")
    app.register_blueprint(device_change_bp, url_prefix="/api/v1")
    app.register_blueprint(dispatch_report_bp, url_prefix="/api/v1")
    app.register_blueprint(ex_gh_bp, url_prefix="/api/v1")
    app.register_blueprint(free_replace_bp, url_prefix="/api/v1")
    app.register_blueprint(liability_bp, url_prefix="/api/v1")
    app.register_blueprint(liability_group_bp, url_prefix="/api/v1")
    app.register_blueprint(liability_sum_bp, url_prefix="/api/v1")
    app.register_blueprint(maintenance_bp, url_prefix="/api/v1")
    app.register_blueprint(maintenance_daily_bp, url_prefix="/api/v1")
    app.register_blueprint(maintenance_open_bp, url_prefix="/api/v1")
    app.register_blueprint(maintenance_plan_bp, url_prefix="/api/v1")
    app.register_blueprint(maintenance_renovate_bp, url_prefix="/api/v1")
    app.register_blueprint(paper_average_report_bp, url_prefix="/api/v1")
    app.register_blueprint(pc_plan_bp, url_prefix="/api/v1")
    app.register_blueprint(pos_r_eid_update_bp, url_prefix="/api/v1")
    app.register_blueprint(preplan_bp, url_prefix="/api/v1")
    app.register_blueprint(recycle_task_bp, url_prefix="/api/v1")
    app.register_blueprint(rep_cust_info_bp, url_prefix="/api/v1")
    app.register_blueprint(rep_liability_report_bp, url_prefix="/api/v1")
    app.register_blueprint(rep_maintenance_daily_bp, url_prefix="/api/v1")
    app.register_blueprint(rep_maintenance_daily_m_bp, url_prefix="/api/v1")
    app.register_blueprint(rep_maintenance_daily_ym_bp, url_prefix="/api/v1")
    app.register_blueprint(shell_bp, url_prefix="/api/v1")
    app.register_blueprint(store_close_bp, url_prefix="/api/v1")
    app.register_blueprint(timepoint_levels_bp, url_prefix="/api/v1")
    app.register_blueprint(user_group_bp, url_prefix="/api/v1")
    return app
