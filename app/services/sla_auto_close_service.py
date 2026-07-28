"""SLA 超时自动关单服务。

扫描 status=5（已解决）且 close_time 超过 sla_close_days 天未回访的日常维护单，
自动 transition(3) 关单（只改状态，不触发联动）。

配置项（sysparm）：
  sla_close_days: 回访超时天数（默认 3 天）

行业对齐 ServiceNow/Jira SM 的 SLA 自动关单机制。
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from app.extensions import db
from app.models.itsm import MaintenanceDaily
from app.repositories.system_repository import SystemRepository
from app.services.itsm_service import MaintenanceDailyService

logger = logging.getLogger(__name__)

# sysparm 配置编码
SLA_CLOSE_DAYS_PARM = "sla_close_days"
# 默认超时天数
DEFAULT_SLA_CLOSE_DAYS = 3
# 自动关单操作人
AUTO_CLOSE_OPERATOR = "SYSTEM_SLA"


class SlaAutoCloseService:
    """SLA 超时自动关单服务。"""

    @staticmethod
    def _get_sla_close_days() -> int:
        """从 sysparm 读取回访超时天数，默认 3 天。"""
        parm = SystemRepository.get_sysparm_by_cd(SLA_CLOSE_DAYS_PARM)
        if parm is None or not parm.parm_val:
            return DEFAULT_SLA_CLOSE_DAYS
        try:
            return int(parm.parm_val)
        except (ValueError, TypeError):
            logger.warning("sysparm %s 值无效: %s，使用默认 %d 天",
                           SLA_CLOSE_DAYS_PARM, parm.parm_val, DEFAULT_SLA_CLOSE_DAYS)
            return DEFAULT_SLA_CLOSE_DAYS

    @staticmethod
    def scan_and_close() -> dict[str, Any]:
        """扫描超时未回访的已解决单据，自动关单。

        Returns:
            扫描结果统计
        """
        sla_days = SlaAutoCloseService._get_sla_close_days()
        cutoff_time = datetime.now(UTC) - timedelta(days=sla_days)

        # 查询 status=5 且 close_time 早于 cutoff 的单据
        overdue_records = (
            db.session.query(MaintenanceDaily)
            .filter(
                MaintenanceDaily.current_status == "5",
                MaintenanceDaily.close_time.isnot(None),
                MaintenanceDaily.close_time < cutoff_time,
            )
            .all()
        )

        closed_count = 0
        failed_count = 0
        failed_ids: list[str] = []

        for record in overdue_records:
            result = MaintenanceDailyService().transition(
                record.maintenance_id,
                "3",  # 回访确认关单（不触发联动）
                AUTO_CLOSE_OPERATOR,
                remark=f"SLA 超时自动关单（超过 {sla_days} 天未回访）",
            )
            if result.get("success"):
                closed_count += 1
                logger.info("SLA 自动关单: %s", record.maintenance_id)
            else:
                failed_count += 1
                failed_ids.append(record.maintenance_id)
                logger.warning("SLA 自动关单失败: %s, 原因: %s",
                               record.maintenance_id, result.get("error"))

        return {
            "sla_close_days": sla_days,
            "scanned": len(overdue_records),
            "closed": closed_count,
            "failed": failed_count,
            "failed_ids": failed_ids,
        }

    @staticmethod
    def preview_overdue() -> list[dict[str, Any]]:
        """预览超时未回访单据（不执行关单，供前端展示）。

        Returns:
            超时单据列表
        """
        sla_days = SlaAutoCloseService._get_sla_close_days()
        cutoff_time = datetime.now(UTC) - timedelta(days=sla_days)

        records = (
            db.session.query(MaintenanceDaily)
            .filter(
                MaintenanceDaily.current_status == "5",
                MaintenanceDaily.close_time.isnot(None),
                MaintenanceDaily.close_time < cutoff_time,
            )
            .all()
        )

        now = datetime.now(UTC)
        result: list[dict[str, Any]] = []
        for r in records:
            close_time = r.close_time
            if close_time and close_time.tzinfo is None:
                close_time = close_time.replace(tzinfo=UTC)
            overdue_days = int((now - close_time).total_seconds() / 86400) if close_time else 0
            result.append({
                "maintenance_id": r.maintenance_id,
                "store_id": r.store_id,
                "close_time": close_time.isoformat() if close_time else None,
                "overdue_days": overdue_days,
                "sla_close_days": sla_days,
            })
        return result
