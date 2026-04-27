# -*- coding: utf-8 -*-
"""
采购计划 Service。
文件说明：提供采购计划业务逻辑。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.repositories.pc_plan_repository import PcPlanRepository


class PcPlanService:
    """采购计划业务逻辑类。"""

    def __init__(self) -> None:
        self.repository = PcPlanRepository()

    def list_pc_plans(
        self,
        pcplanid: Optional[str] = None,
        slbillid: Optional[str] = None,
        pctyp: Optional[str] = None,
        auditflg: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        查询采购计划列表。

        Args:
            pcplanid: 采购计划ID
            slbillid: 销售单据ID
            pctyp: 采购类型
            auditflg: 审核标志
            page: 页码
            page_size: 每页数量

        Returns:
            采购计划列表
        """
        return self.repository.list_pc_plans(
            pcplanid=pcplanid,
            slbillid=slbillid,
            pctyp=pctyp,
            auditflg=auditflg,
            page=page,
            page_size=page_size,
        )

    def get_pc_plan(self, pcplanid: str) -> Dict[str, Any]:
        """
        查询采购计划详情。

        Args:
            pcplanid: 采购计划ID

        Returns:
            采购计划详情
        """
        return self.repository.get_pc_plan(pcplanid=pcplanid)

    def create_pc_plan(
        self,
        pcplanid: str,
        slbillid: str,
        pctyp: str,
        ptimes: int,
        opercd: str,
    ) -> Dict[str, Any]:
        """
        创建采购计划。

        Args:
            pcplanid: 采购计划ID
            slbillid: 销售单据ID
            pctyp: 采购类型
            ptimes: 采购次数
            opercd: 操作员代码

        Returns:
            创建结果
        """
        # 检查采购计划ID是否已存在
        existing = self.repository.get_pc_plan(pcplanid=pcplanid)
        if existing.get("success"):
            return {"success": False, "error": f"采购计划ID已存在: {pcplanid}"}

        return self.repository.create_pc_plan(
            pcplanid=pcplanid,
            slbillid=slbillid,
            pctyp=pctyp,
            ptimes=ptimes,
            opercd=opercd,
        )

    def update_pc_plan(
        self,
        pcplanid: str,
        pctyp: Optional[str] = None,
        ptimes: Optional[int] = None,
        auditflg: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        更新采购计划。

        Args:
            pcplanid: 采购计划ID
            pctyp: 采购类型
            ptimes: 采购次数
            auditflg: 审核标志

        Returns:
            更新结果
        """
        # 检查采购计划是否存在
        existing = self.repository.get_pc_plan(pcplanid=pcplanid)
        if not existing.get("success"):
            return {"success": False, "error": f"采购计划不存在: {pcplanid}"}

        return self.repository.update_pc_plan(
            pcplanid=pcplanid,
            pctyp=pctyp,
            ptimes=ptimes,
            auditflg=auditflg,
        )

    def delete_pc_plan(self, pcplanid: str) -> Dict[str, Any]:
        """
        删除采购计划。

        Args:
            pcplanid: 采购计划ID

        Returns:
            删除结果
        """
        # 检查采购计划是否存在
        existing = self.repository.get_pc_plan(pcplanid=pcplanid)
        if not existing.get("success"):
            return {"success": False, "error": f"采购计划不存在: {pcplanid}"}

        return self.repository.delete_pc_plan(pcplanid=pcplanid)
