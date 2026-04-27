# -*- coding: utf-8 -*-
"""
上门服务记录仓储层（TIT23_MAINTENANCE_D2D）。

文件说明：提供上门服务记录的查询与新增能力，作为公用附表被多单据复用。
作者：Cascade
创建时间：2026-04-14

关联单据：
- TIT10_MAINTENANCEDAY（日常维护单）
- TIT15_MAINTENANCE_RENOVATE（旧机翻新单）
- TIT17_MAINTENANCE（日常保养单）
"""

import logging
from typing import Any, Dict, List, Optional

from app.extensions.oracle import get_oracle_connection

logger = logging.getLogger(__name__)


class MaintenanceD2DRepository:
    """上门服务记录仓储（TIT23_MAINTENANCE_D2D）。"""

    def list_d2d_records(
        self,
        maintenance_id: str,
        d2d_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        查询上门服务记录列表。

        Args:
            maintenance_id: 维护单ID（关联主表）
            d2d_type: 上门类型过滤（可选，'1'=维护，'2'=翻新，'3'=保养）

        Returns:
            上门服务记录列表
        """
        sql = """
            SELECT
                MAINTENANCE_ID,
                BUSINESS_OPERATION_ID,
                D2D_ENGINEER,
                ARRIVE_TIME,
                LEAVE_TIME,
                JJBZ,
                D2D_DESCRIPITON,
                D2D_PHONE,
                OLD_BUSINESS_ID,
                D2D_GROUP,
                D2D_TYPE,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                USEFLG,
                POSSTATUS,
                POSSTATUS1
            FROM TIT23_MAINTENANCE_D2D
            WHERE MAINTENANCE_ID = :maintenance_id
              AND NVL(USEFLG, '1') = '1'
        """
        params: Dict[str, Any] = {"maintenance_id": maintenance_id}

        if d2d_type:
            sql += " AND D2D_TYPE = :d2d_type"
            params["d2d_type"] = d2d_type

        sql += " ORDER BY BUSINESS_OPERATION_ID DESC, CREATE_TIME DESC"

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"查询上门服务记录失败: {e}")
            raise

    def create_d2d_record(
        self,
        maintenance_id: str,
        business_operation_id: int,
        creator: str,
        d2d_engineer: Optional[str] = None,
        arrive_time: Optional[str] = None,
        leave_time: Optional[str] = None,
        jjbz: Optional[str] = None,
        d2d_description: Optional[str] = None,
        d2d_phone: Optional[str] = None,
        old_business_id: Optional[int] = None,
        d2d_group: Optional[int] = None,
        d2d_type: Optional[str] = None,
        pos_status: Optional[str] = None,
        pos_status1: Optional[str] = None,
    ) -> bool:
        """
        新增上门服务记录。

        Args:
            maintenance_id: 维护单ID（关联主表）
            business_operation_id: 业务流水操作ID
            creator: 创建人
            d2d_engineer: 上门工程师
            arrive_time: 到达时间（YYYY-MM-DD HH24:MI:SS）
            leave_time: 离开时间（YYYY-MM-DD HH24:MI:SS）
            jjbz: 计价标志
            d2d_description: 上门服务描述
            d2d_phone: 上门联系电话
            old_business_id: 原业务ID
            d2d_group: 上门组
            d2d_type: 上门类型（'1'=维护，'2'=翻新，'3'=保养）
            pos_status: POS状态
            pos_status1: POS状态1

        Returns:
            是否新增成功
        """
        sql = """
            INSERT INTO TIT23_MAINTENANCE_D2D (
                MAINTENANCE_ID,
                BUSINESS_OPERATION_ID,
                D2D_ENGINEER,
                ARRIVE_TIME,
                LEAVE_TIME,
                JJBZ,
                D2D_DESCRIPITON,
                D2D_PHONE,
                OLD_BUSINESS_ID,
                D2D_GROUP,
                D2D_TYPE,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                USEFLG,
                POSSTATUS,
                POSSTATUS1
            ) VALUES (
                :maintenance_id,
                :business_operation_id,
                :d2d_engineer,
                TO_DATE(:arrive_time, 'YYYY-MM-DD HH24:MI:SS'),
                TO_DATE(:leave_time, 'YYYY-MM-DD HH24:MI:SS'),
                :jjbz,
                :d2d_description,
                :d2d_phone,
                :old_business_id,
                :d2d_group,
                :d2d_type,
                SYSDATE,
                :creator,
                SYSDATE,
                :creator,
                '1',
                :pos_status,
                :pos_status1
            )
        """
        params = {
            "maintenance_id": maintenance_id,
            "business_operation_id": business_operation_id,
            "d2d_engineer": d2d_engineer,
            "arrive_time": arrive_time,
            "leave_time": leave_time,
            "jjbz": jjbz,
            "d2d_description": d2d_description,
            "d2d_phone": d2d_phone,
            "old_business_id": old_business_id,
            "d2d_group": d2d_group,
            "d2d_type": d2d_type,
            "creator": creator,
            "pos_status": pos_status,
            "pos_status1": pos_status1,
        }

        for key in ["arrive_time", "leave_time"]:
            if not params[key]:
                params[key] = None

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"新增上门服务记录失败: {e}")
            raise
