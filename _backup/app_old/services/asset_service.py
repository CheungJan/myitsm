"""
门店资产管理服务。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 基于 TMM35_CUST_POS_RL 扩展资产属性管理
    - 对应优化4：资产属性与回收任务
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from app.repositories.asset_repository import AssetRepository

logger = logging.getLogger(__name__)

__all__ = ["AssetService", "AssetType", "RecycleStatus"]


class AssetType(Enum):
    """资产类型。"""

    NEW = "NEW"  # 新机
    OLD = "OLD"  # 旧机
    RENOVATED = "RENOVATED"  # 翻新机
    SCRAP = "SCRAP"  # 报废机


class RecycleStatus(Enum):
    """回收状态。"""

    NONE = "NONE"  # 无需回收
    PENDING = "PENDING"  # 待回收
    ASSIGNED = "ASSIGNED"  # 已分配
    IN_PROGRESS = "IN_PROGRESS"  # 回收中
    COMPLETED = "COMPLETED"  # 已完成
    CANCELLED = "CANCELLED"  # 已取消


class AssetService:
    """
    门店资产管理服务。

    功能概述：
        - 门店资产查询与管理
        - 可回收资产判定
        - 资产回收状态流转
    """

    def __init__(self, asset_repository: AssetRepository | None = None) -> None:
        """
        初始化服务。

        参数：
            asset_repository: 资产仓储实例，默认自动创建
        """
        self._repo = asset_repository or AssetRepository()

    def list_assets(
        self,
        cust_cd: str | None = None,
        eid: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        获取门店资产列表。

        参数：
            cust_cd: 门店代码
            eid: 设备编码

        返回值：
            list[dict[str, Any]]: 资产列表
        """
        return self._repo.list_assets(cust_cd=cust_cd, eid=eid)

    def get_recyclable_assets(self, cust_cd: str) -> list[dict[str, Any]]:
        """
        获取门店可回收资产列表。

        可回收条件：
            - ASSET_TYPE IN ('OLD', 'RENOVATED')
            - RECYCLABLE_FLAG = '1'
            - RECYCLE_STATUS = 'NONE'
            - ASSET_STATUS = 'ACTIVE'

        参数：
            cust_cd: 门店代码

        返回值：
            list[dict[str, Any]]: 可回收资产列表
        """
        return self._repo.get_recyclable_assets(cust_cd)

    def mark_recyclable(self, cust_cd: str, plan_type: str) -> int:
        """
        标记门店可回收资产。

        判定规则：
            - 关门(plan_type='02')：全部 ACTIVE 资产标记为可回收
            - 旧机翻新(plan_type='01')：只标记 POS机、主机等关键设备

        参数：
            cust_cd: 门店代码
            plan_type: 计划类型（01旧机翻新/02关门）

        返回值：
            int: 标记的可回收资产数量
        """
        return self._repo.mark_recyclable(cust_cd, plan_type)

    def update_recycle_status(
        self,
        cust_cd: str,
        eid: str,
        recycle_status: RecycleStatus,
    ) -> bool:
        """
        更新资产回收状态。

        参数：
            cust_cd: 门店代码
            eid: 设备编码
            recycle_status: 回收状态

        返回值：
            bool: 是否成功
        """
        return self._repo.update_recycle_status(
            cust_cd,
            eid,
            recycle_status.value,
        )

    def batch_update_recycle_status(
        self,
        cust_cd: str,
        eids: list[str],
        recycle_status: RecycleStatus,
    ) -> bool:
        """
        批量更新资产回收状态。

        参数：
            cust_cd: 门店代码
            eids: 设备编码列表
            recycle_status: 回收状态

        返回值：
            bool: 是否成功
        """
        return self._repo.batch_update_recycle_status(
            cust_cd,
            eids,
            recycle_status.value,
        )

    def create_from_plan(
        self,
        cust_cd: str,
        eid: str,
        item_cd: str,
        plan_no: str,
        asset_info: dict[str, Any],
        oper_cd: str,
    ) -> bool:
        """
        从预计划创建新资产。

        参数：
            cust_cd: 门店代码
            eid: 设备编码
            item_cd: 物料代码
            plan_no: 预计划单号
            asset_info: 资产信息
            oper_cd: 操作员代码

        返回值：
            bool: 是否成功
        """
        return self._repo.create_from_plan(
            cust_cd,
            eid,
            item_cd,
            plan_no,
            asset_info,
            oper_cd,
        )

    def should_create_recycle_task(
        self,
        cust_cd: str,
        plan_type: str,
    ) -> tuple[bool, int]:
        """
        判断是否应创建回收任务。

        判定规则：
            - PLAN_TYPE in ('01', '02') → 需要回收
            - 且门店有可回收资产（RECYCLABLE_FLAG='1'）

        参数：
            cust_cd: 门店代码
            plan_type: 计划类型

        返回值：
            tuple[bool, int]: (是否应创建, 可回收资产数量)
        """
        if plan_type not in ("01", "02"):
            return False, 0

        assets = self.get_recyclable_assets(cust_cd)
        return len(assets) > 0, len(assets)
