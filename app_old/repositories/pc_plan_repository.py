# -*- coding: utf-8 -*-
"""
采购计划 Repository。
文件说明：提供采购计划（TPC01_PCPLAN）的数据访问能力。
作者：Cascade
创建时间：2026-04-20

表结构：
- TPC01_PCPLAN: 采购计划主表
- TPC02_PCPLANDT: 采购计划明细表
- TPC03_PCPLANSTATUS: 采购计划状态表
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.extensions import db


class PcPlanRepository:
    """采购计划数据访问类。"""

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
            采购计划列表及分页信息
        """
        try:
            query = "SELECT * FROM TPC01_PCPLAN WHERE 1=1"
            params: Dict[str, Any] = {}

            if pcplanid:
                query += " AND PCPLANID = :pcplanid"
                params["pcplanid"] = pcplanid
            if slbillid:
                query += " AND SLBILLID = :slbillid"
                params["slbillid"] = slbillid
            if pctyp:
                query += " AND PCTYP = :pctyp"
                params["pctyp"] = pctyp
            if auditflg:
                query += " AND AUDITFLG = :auditflg"
                params["auditflg"] = auditflg

            # 分页
            offset = (page - 1) * page_size
            query += " ORDER BY PCPLANID DESC OFFSET :offset ROWS FETCH NEXT :page_size ROWS ONLY"
            params["offset"] = offset
            params["page_size"] = page_size

            result = db.session.execute(query, params)
            rows = result.fetchall()
            columns = result.keys()

            data = [dict(zip(columns, row)) for row in rows]

            return {
                "success": True,
                "data": data,
                "page": page,
                "page_size": page_size,
                "total": len(data),
            }
        except Exception as exc:
            return {
                "success": False,
                "error": f"查询采购计划列表失败: {str(exc)}",
                "data": [],
            }

    def get_pc_plan(self, pcplanid: str) -> Dict[str, Any]:
        """
        查询采购计划详情。

        Args:
            pcplanid: 采购计划ID

        Returns:
            采购计划详情
        """
        try:
            query = "SELECT * FROM TPC01_PCPLAN WHERE PCPLANID = :pcplanid"
            params = {"pcplanid": pcplanid}

            result = db.session.execute(query, params)
            row = result.fetchone()

            if not row:
                return {
                    "success": False,
                    "error": f"采购计划不存在: {pcplanid}",
                    "data": None,
                }

            columns = result.keys()
            data = dict(zip(columns, row))

            return {"success": True, "data": data}
        except Exception as exc:
            return {
                "success": False,
                "error": f"查询采购计划详情失败: {str(exc)}",
                "data": None,
            }

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
        try:
            query = """
                INSERT INTO TPC01_PCPLAN (
                    PCPLANID, SLBILLID, PCTYP, PTIMES, OPERCD, AUDITFLG
                ) VALUES (
                    :pcplanid, :slbillid, :pctyp, :ptimes, :opercd, '0'
                )
            """
            params = {
                "pcplanid": pcplanid,
                "slbillid": slbillid,
                "pctyp": pctyp,
                "ptimes": ptimes,
                "opercd": opercd,
            }

            db.session.execute(query, params)
            db.session.commit()

            return {"success": True, "pcplanid": pcplanid}
        except Exception as exc:
            db.session.rollback()
            return {
                "success": False,
                "error": f"创建采购计划失败: {str(exc)}",
            }

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
        try:
            updates = []
            params: Dict[str, Any] = {"pcplanid": pcplanid}

            if pctyp is not None:
                updates.append("PCTYP = :pctyp")
                params["pctyp"] = pctyp
            if ptimes is not None:
                updates.append("PTIMES = :ptimes")
                params["ptimes"] = ptimes
            if auditflg is not None:
                updates.append("AUDITFLG = :auditflg")
                params["auditflg"] = auditflg

            if not updates:
                return {"success": False, "error": "无更新字段"}

            query = f"UPDATE TPC01_PCPLAN SET {', '.join(updates)} WHERE PCPLANID = :pcplanid"
            db.session.execute(query, params)
            db.session.commit()

            return {"success": True}
        except Exception as exc:
            db.session.rollback()
            return {
                "success": False,
                "error": f"更新采购计划失败: {str(exc)}",
            }

    def delete_pc_plan(self, pcplanid: str) -> Dict[str, Any]:
        """
        删除采购计划。

        Args:
            pcplanid: 采购计划ID

        Returns:
            删除结果
        """
        try:
            query = "DELETE FROM TPC01_PCPLAN WHERE PCPLANID = :pcplanid"
            params = {"pcplanid": pcplanid}

            db.session.execute(query, params)
            db.session.commit()

            return {"success": True}
        except Exception as exc:
            db.session.rollback()
            return {
                "success": False,
                "error": f"删除采购计划失败: {str(exc)}",
            }
