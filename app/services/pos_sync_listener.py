"""POS 状态同步监听器（审核意见 13 采纳）。

监听 d2d_leave_store / maintenance_close 等事件，同步 TMM22_CUSTOMERS.posstatus/posstatus1。

对齐 PB of_set_posstatus(custid, posstatus, posstatus1) 功能：
- d2d 离店登记：posstatus='01'、posstatus1='11'（设备正常）
- 维护单关单：posstatus='99'、posstatus1='99'（设备停用）
- 新建维护单：posstatus='01'、posstatus1='11'（设备恢复正常）
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.extensions import db
from app.models.master import Customer
from app.services.event_bus import EventBus

logger = logging.getLogger(__name__)


class PosSyncService:
    """POS 状态同步服务（更新 TMM22_CUSTOMERS.posstatus/posstatus1）。"""

    @staticmethod
    def sync(custcd: str, posstatus: str, posstatus1: str) -> None:
        """同步 POS 状态到客户表。

        Args:
            custcd: 客户编码
            posstatus: POS 主状态（01=正常 / 99=停用）
            posstatus1: POS 子状态（11=正常使用 / 99=停用）
        """
        if not custcd:
            logger.warning("PosSyncService.sync: custcd 为空，跳过")
            return
        customer = (
            db.session.query(Customer).filter(Customer.custcd == custcd).first()
        )
        if customer is None:
            logger.warning("PosSyncService.sync: 客户不存在 custcd=%s", custcd)
            return
        customer.posstatus = posstatus
        customer.posstatus1 = posstatus1
        customer.update_time = datetime.now(timezone.utc)
        logger.info(
            "POS 状态同步: custcd=%s posstatus=%s posstatus1=%s",
            custcd,
            posstatus,
            posstatus1,
        )


# ---------------------------------------------------------------------------
# 事件监听器注册
# ---------------------------------------------------------------------------


@EventBus.on("d2d_leave_store")
def _on_d2d_leave_sync_pos(payload: dict[str, object]) -> None:
    """d2d 离店登记 → 同步 POS 状态为正常（01/11）。

    payload 需包含: custcd, posstatus(可选默认01), posstatus1(可选默认11)
    """
    custcd = str(payload.get("custcd") or "")
    posstatus = str(payload.get("posstatus") or "01")
    posstatus1 = str(payload.get("posstatus1") or "11")
    PosSyncService.sync(custcd, posstatus, posstatus1)


@EventBus.on("maintenance_close")
def _on_maintenance_close_sync_pos(payload: dict[str, object]) -> None:
    """维护单关单 → 同步 POS 状态为停用（99/99）。

    payload 需包含: custcd
    """
    custcd = str(payload.get("custcd") or "")
    PosSyncService.sync(custcd, "99", "99")


@EventBus.on("maintenance_create")
def _on_maintenance_create_sync_pos(payload: dict[str, object]) -> None:
    """新建维护单 → 同步 POS 状态为正常（01/11，设备恢复）。

    payload 需包含: custcd
    """
    custcd = str(payload.get("custcd") or "")
    PosSyncService.sync(custcd, "01", "11")
