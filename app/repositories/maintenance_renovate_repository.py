# -*- coding: utf-8 -*-
"""
旧机翻新单仓储
文件说明：对接TIT15_MAINTENANCE_RENOVATE表（旧机翻新单主表）
作者：Cascade
创建时间：2026-04-08

关联表：
- TIT15_MAINTENANCE_RENOVATE：旧机翻新单主表
- TIT15_EQUIPMENT_RENOVATE：翻新设备映射表（旧机→新机，子表后续扩展）
- TIT23_MAINTENANCE_D2D：上门服务记录（公用附表）

单据类型码：MR（旧机翻新）
"""

import logging
from typing import Dict, List, Optional, Any

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class MaintenanceRenovateRepository:
    """旧机翻新单仓储类"""

    def __init__(self):
        self.table = "TIT15_MAINTENANCE_RENOVATE"
        self.pk_field = "RENOVATE_ID"

    def get_by_id(self, renovate_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取旧机翻新单详情
        
        Args:
            renovate_id: 翻新单ID
            
        Returns:
            翻新单详情字典
        """
        sql = f"""
            SELECT 
                RENOVATE_ID,
                STORE_ID,
                OLD_DEVICE_ID,
                NEW_DEVICE_ID,
                RENOVATE_TYPE,
                CURRENT_STATUS,
                CREATE_TIME,
                UPDATE_TIME,
                CREATE_BY,
                UPDATE_BY,
                FIRSTOR,
                ARRIVE_TIME,
                LEAVE_TIME,
                CLOSE_TIME,
                REMARK
            FROM {self.table}
            WHERE {self.pk_field} = :renovate_id
              AND USEFLG = '1'
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"renovate_id": renovate_id})
                    row = cursor.fetchone()
                    if not row:
                        return None
                    columns = [col[0].lower() for col in cursor.description]
                    return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"获取旧机翻新单详情失败: {e}")
            raise

    def list_maintenance_renovates(
        self,
        store_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        获取旧机翻新单列表
        
        Args:
            store_id: 门店ID过滤
            status: 状态过滤
            page: 页码
            page_size: 每页数量
            
        Returns:
            分页结果字典
        """
        where_clauses = ["USEFLG = '1'"]
        params = {}

        if store_id:
            where_clauses.append("STORE_ID = :store_id")
            params["store_id"] = store_id
        if status:
            where_clauses.append("CURRENT_STATUS = :status")
            params["status"] = status

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*) FROM {self.table}
            WHERE {where_sql}
        """

        list_sql = f"""
            SELECT 
                RENOVATE_ID,
                STORE_ID,
                OLD_DEVICE_ID,
                NEW_DEVICE_ID,
                RENOVATE_TYPE,
                CURRENT_STATUS,
                CREATE_TIME,
                CREATE_BY,
                FIRSTOR
            FROM {self.table}
            WHERE {where_sql}
            ORDER BY CREATE_TIME DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(count_sql, params)
                    total = cursor.fetchone()[0]

                    query_params = {**params, "offset": (page - 1) * page_size, "limit": page_size}
                    cursor.execute(list_sql, query_params)
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    items = [dict(zip(columns, row)) for row in rows]

                    return {
                        "items": items,
                        "total": total,
                        "page": page,
                        "page_size": page_size,
                    }
        except Exception as e:
            logger.error(f"获取旧机翻新单列表失败: {e}")
            raise

    def create_maintenance_renovate(
        self,
        renovate_id: str,
        store_id: str,
        old_device_id: Optional[str] = None,
        new_device_id: Optional[str] = None,
        renovate_type: Optional[str] = None,
        current_status: str = "00",
        oper_cd: Optional[str] = None,
        remark: Optional[str] = None,
    ) -> bool:
        """
        创建旧机翻新单
        
        Args:
            renovate_id: 翻新单ID
            store_id: 门店ID
            old_device_id: 旧整机ID
            new_device_id: 新整机ID
            renovate_type: 翻新类型
            current_status: 当前状态
            oper_cd: 操作人
            remark: 备注
            
        Returns:
            是否创建成功
        """
        sql = f"""
            INSERT INTO {self.table} (
                RENOVATE_ID, STORE_ID, OLD_DEVICE_ID,
                NEW_DEVICE_ID, RENOVATE_TYPE, CURRENT_STATUS,
                CREATE_TIME, UPDATE_TIME, CREATE_BY, UPDATE_BY,
                FIRSTOR, USEFLG, REMARK
            ) VALUES (
                :renovate_id, :store_id, :old_device_id,
                :new_device_id, :renovate_type, :current_status,
                SYSDATE, SYSDATE, :oper_cd, :oper_cd,
                :oper_cd, '1', :remark
            )
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "renovate_id": renovate_id,
                            "store_id": store_id,
                            "old_device_id": old_device_id,
                            "new_device_id": new_device_id,
                            "renovate_type": renovate_type,
                            "current_status": current_status,
                            "oper_cd": oper_cd,
                            "remark": remark,
                        },
                    )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"创建旧机翻新单失败: {e}")
            raise

    def update_status(
        self,
        renovate_id: str,
        old_status: str,
        new_status: str,
        oper_cd: Optional[str] = None,
    ) -> bool:
        """
        更新翻新单状态（带乐观锁）
        
        Args:
            renovate_id: 翻新单ID
            old_status: 当前状态
            new_status: 新状态
            oper_cd: 操作人
            
        Returns:
            是否更新成功
        """
        sql = f"""
            UPDATE {self.table}
            SET CURRENT_STATUS = :new_status,
                UPDATE_TIME = SYSDATE,
                UPDATE_BY = :oper_cd
            WHERE {self.pk_field} = :renovate_id
              AND CURRENT_STATUS = :old_status
              AND USEFLG = '1'
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "renovate_id": renovate_id,
                            "old_status": old_status,
                            "new_status": new_status,
                            "oper_cd": oper_cd,
                        },
                    )
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新翻新单状态失败: {e}")
            raise

    def list_equipment_renovates(self, renovate_id: str) -> List[Dict[str, Any]]:
        """
        查询翻新设备明细（TIT15_EQUIPMENT_RENOVATE）。

        Args:
            renovate_id: 旧机翻新单ID

        Returns:
            翻新设备明细列表
        """
        sql = """
            SELECT
                RENOVATE_ID,
                BUSINESS_OPERATION_ID,
                DEVICE_ID,
                NEW_DEVICE_ID,
                PRICE,
                DELIVERYID,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                IS_FINISH,
                IS_CHANGE,
                CHANGE_EID
            FROM TIT15_EQUIPMENT_RENOVATE
            WHERE RENOVATE_ID = :renovate_id
            ORDER BY BUSINESS_OPERATION_ID DESC, CREATE_TIME DESC
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"renovate_id": renovate_id})
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"查询翻新设备明细失败: {e}")
            raise

    def create_equipment_renovate(
        self,
        renovate_id: str,
        business_operation_id: int,
        device_id: str,
        creator: str,
        new_device_id: Optional[str] = None,
        price: Optional[float] = None,
        delivery_id: Optional[str] = None,
        is_finish: str = "0",
        is_change: Optional[str] = None,
        change_eid: Optional[str] = None,
    ) -> bool:
        """
        新增翻新设备明细（TIT15_EQUIPMENT_RENOVATE）。

        Args:
            renovate_id: 旧机翻新单ID
            business_operation_id: 业务流水操作ID
            device_id: 旧整机ID
            creator: 创建人
            new_device_id: 新整机ID
            price: 价格
            delivery_id: 送货单号
            is_finish: 是否提交（0未提交，1已提交）
            is_change: 是否变更
            change_eid: 变更设备ID

        Returns:
            是否新增成功
        """
        sql = """
            INSERT INTO TIT15_EQUIPMENT_RENOVATE (
                RENOVATE_ID,
                BUSINESS_OPERATION_ID,
                DEVICE_ID,
                NEW_DEVICE_ID,
                PRICE,
                DELIVERYID,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                IS_FINISH,
                IS_CHANGE,
                CHANGE_EID
            ) VALUES (
                :renovate_id,
                :business_operation_id,
                :device_id,
                :new_device_id,
                :price,
                :delivery_id,
                SYSDATE,
                :creator,
                SYSDATE,
                :creator,
                :is_finish,
                :is_change,
                :change_eid
            )
        """
        params = {
            "renovate_id": renovate_id,
            "business_operation_id": business_operation_id,
            "device_id": device_id,
            "new_device_id": new_device_id,
            "price": price,
            "delivery_id": delivery_id,
            "creator": creator,
            "is_finish": is_finish,
            "is_change": is_change,
            "change_eid": change_eid,
        }
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"新增翻新设备明细失败: {e}")
            raise
