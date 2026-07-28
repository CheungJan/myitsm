"""APScheduler 定时任务扩展。

在 Flask 应用工厂中初始化，提供后台定时任务调度。
SLA 超时自动关单等定时任务在此注册。
"""

from __future__ import annotations

import logging
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore[import-untyped]

from app.services.sla_auto_close_service import SlaAutoCloseService

logger = logging.getLogger(__name__)

# 全局调度器实例（单例）
_scheduler: BackgroundScheduler | None = None


def init_scheduler(app: Any) -> None:
    """初始化定时任务调度器。

    在应用工厂中调用：
        from app.extensions.scheduler import init_scheduler
        init_scheduler(app)
    """
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    # SLA 超时自动关单：每小时扫描一次
    # 扫描 status=5 且 close_time 超过 sla_close_days 天的单据，自动 transition(3)
    interval_minutes = int(app.config.get("SLA_AUTO_CLOSE_INTERVAL_MINUTES", 60))
    _scheduler.add_job(
        func=_run_sla_auto_close,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="sla_auto_close",
        name="SLA 超时自动关单",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("定时任务调度器已启动，SLA 自动关单间隔=%d 分钟", interval_minutes)


def shutdown_scheduler() -> None:
    """关闭调度器（应用退出时调用）。"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def _run_sla_auto_close() -> None:
    """执行 SLA 超时自动关单扫描。

    在调度器线程中运行，需手动创建应用上下文。
    """
    from app import create_app

    app = create_app()
    with app.app_context():
        try:
            result = SlaAutoCloseService.scan_and_close()
            logger.info("SLA 自动关单完成: %s", result)
        except Exception as e:
            logger.exception("SLA 自动关单异常: %s", e)
