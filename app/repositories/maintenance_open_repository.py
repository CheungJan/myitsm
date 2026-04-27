# -*- coding: utf-8 -*-
"""
新机开通单仓储
文件说明：对接TIT13_MAINTENANCE_OPEN表（新机开通单主表）
作者：Cascade
创建时间：2026-04-08

关联表：
- TIT13_MAINTENANCE_OPEN：新机开通单主表
- TIT14_EQUIPMENT_OPEN：开通设备明细（子表，后续扩展）
- TIT23_MAINTENANCE_D2D：上门服务记录（公用附表）

单据类型码：MO（新机开通）
"""

import logging
from typing import Dict, List, Optional, Any

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class MaintenanceOpenRepository:
    """新机开通单仓储类"""

    def __init__(self):
        self.table = "TIT13_MAINTENANCE_OPEN"
        self.pk_field = "NEW_OPENING_ID"

    def get_by_id(self, new_opening_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取新机开通单详情
        
        Args:
            new_opening_id: 开通单ID
            
        Returns:
            开通单详情字典
        """
        sql = f"""
            SELECT 
                NEW_OPENING_ID,
                STORE_ID,
                REQUEST_TIME,
                DEVICE_ID,
                OPEN_TYPE,
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
            WHERE {self.pk_field} = :new_opening_id
              AND USEFLG = '1'
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"new_opening_id": new_opening_id})
                    row = cursor.fetchone()
                    if not row:
                        return None
                    columns = [col[0].lower() for col in cursor.description]
                    return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"获取新机开通单详情失败: {e}")
            raise

    def list_maintenance_opens(
        self,
        store_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        获取新机开通单列表
        
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
                NEW_OPENING_ID,
                STORE_ID,
                REQUEST_TIME,
                DEVICE_ID,
                OPEN_TYPE,
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
            logger.error(f"获取新机开通单列表失败: {e}")
            raise

    def create_maintenance_open(
        self,
        new_opening_id: str,
        store_id: str,
        device_id: Optional[str] = None,
        open_type: Optional[str] = None,
        current_status: str = "00",
        oper_cd: Optional[str] = None,
        remark: Optional[str] = None,
    ) -> bool:
        """
        创建新机开通单
        
        Args:
            new_opening_id: 开通单ID
            store_id: 门店ID
            device_id: 整机ID
            open_type: 开通类型
            current_status: 当前状态
            oper_cd: 操作人
            remark: 备注
            
        Returns:
            是否创建成功
        """
        sql = f"""
            INSERT INTO {self.table} (
                NEW_OPENING_ID, STORE_ID, REQUEST_TIME,
                DEVICE_ID, OPEN_TYPE, CURRENT_STATUS,
                CREATE_TIME, UPDATE_TIME, CREATE_BY, UPDATE_BY,
                FIRSTOR, USEFLG, REMARK
            ) VALUES (
                :new_opening_id, :store_id, SYSDATE,
                :device_id, :open_type, :current_status,
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
                            "new_opening_id": new_opening_id,
                            "store_id": store_id,
                            "device_id": device_id,
                            "open_type": open_type,
                            "current_status": current_status,
                            "oper_cd": oper_cd,
                            "remark": remark,
                        },
                    )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"创建新机开通单失败: {e}")
            raise

    def update_status(
        self,
        new_opening_id: str,
        old_status: str,
        new_status: str,
        oper_cd: Optional[str] = None,
    ) -> bool:
        """
        更新开通单状态（带乐观锁）
        
        Args:
            new_opening_id: 开通单ID
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
            WHERE {self.pk_field} = :new_opening_id
              AND CURRENT_STATUS = :old_status
              AND USEFLG = '1'
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "new_opening_id": new_opening_id,
                            "old_status": old_status,
                            "new_status": new_status,
                            "oper_cd": oper_cd,
                        },
                    )
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新开通单状态失败: {e}")
            raise

    def list_equipment_opens(self, new_opening_id: str) -> List[Dict[str, Any]]:
        """
        查询开通设备明细（TIT14_EQUIPMENT_OPEN）。

        Args:
            new_opening_id: 新机开通单ID

        Returns:
            开通设备明细列表
        """
        sql = """
            SELECT
                NEW_OPENING_ID,
                BUSINESS_OPERATION_ID,
                DEVICE_ID,
                PRICE,
                DELIVERYID,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                IS_FINISH,
                IS_CHANGE,
                CHANGE_EID,
                FROM_CUSTCARD,
                TO_CUSTCARD,
                MOBILE_NO,
                OPER_MEMO,
                CARDTYPE,
                CUST_ID
            FROM TIT14_EQUIPMENT_OPEN
            WHERE NEW_OPENING_ID = :new_opening_id
            ORDER BY BUSINESS_OPERATION_ID DESC, CREATE_TIME DESC
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"new_opening_id": new_opening_id})
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"查询开通设备明细失败: {e}")
            raise

    def create_equipment_open(
        self,
        new_opening_id: str,
        business_operation_id: int,
        device_id: str,
        creator: str,
        price: float | None = None,
        delivery_id: str | None = None,
        is_finish: str = "0",
        is_change: str | None = None,
        change_eid: str | None = None,
        from_custcard: str | None = None,
        to_custcard: str | None = None,
        mobile_no: str | None = None,
        oper_memo: str | None = None,
        card_type: str | None = None,
        cust_id: str | None = None,
    ) -> bool:
        """
        新增开通设备明细（TIT14_EQUIPMENT_OPEN）。

        Args:
            new_opening_id: 新机开通单ID
            business_operation_id: 业务流水操作ID
            device_id: 整机ID
            creator: 创建人
            price: 价格
            delivery_id: 送货单号
            is_finish: 是否提交（0未提交，1已提交）
            is_change: 是否变更
            change_eid: 变更设备ID
            from_custcard: 迁出磁卡号
            to_custcard: 迁入磁卡号
            mobile_no: 联系电话
            oper_memo: 操作备注
            card_type: 卡类型
            cust_id: 客户ID

        Returns:
            是否新增成功
        """
        sql = """
            INSERT INTO TIT14_EQUIPMENT_OPEN (
                NEW_OPENING_ID,
                BUSINESS_OPERATION_ID,
                DEVICE_ID,
                PRICE,
                DELIVERYID,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                IS_FINISH,
                IS_CHANGE,
                CHANGE_EID,
                FROM_CUSTCARD,
                TO_CUSTCARD,
                MOBILE_NO,
                OPER_MEMO,
                CARDTYPE,
                CUST_ID
            ) VALUES (
                :new_opening_id,
                :business_operation_id,
                :device_id,
                :price,
                :delivery_id,
                SYSDATE,
                :creator,
                SYSDATE,
                :creator,
                :is_finish,
                :is_change,
                :change_eid,
                :from_custcard,
                :to_custcard,
                :mobile_no,
                :oper_memo,
                :card_type,
                :cust_id
            )
        """
        params = {
            "new_opening_id": new_opening_id,
            "business_operation_id": business_operation_id,
            "device_id": device_id,
            "price": price,
            "delivery_id": delivery_id,
            "creator": creator,
            "is_finish": is_finish,
            "is_change": is_change,
            "change_eid": change_eid,
            "from_custcard": from_custcard,
            "to_custcard": to_custcard,
            "mobile_no": mobile_no,
            "oper_memo": oper_memo,
            "card_type": card_type,
            "cust_id": cust_id,
        }
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"新增开通设备明细失败: {e}")
            raise

    def count_equipment_opens_by_finish(self, new_opening_id: str, is_finish: str) -> int:
        """
        按提交状态统计开通设备明细数量。

        Args:
            new_opening_id: 新机开通单ID
            is_finish: 提交状态（0未提交，1已提交）

        Returns:
            记录数量
        """
        sql = """
            SELECT COUNT(1)
            FROM TIT14_EQUIPMENT_OPEN
            WHERE NEW_OPENING_ID = :new_opening_id
              AND IS_FINISH = :is_finish
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "new_opening_id": new_opening_id,
                            "is_finish": is_finish,
                        },
                    )
                    row = cursor.fetchone()
                    if row is None:
                        return 0
                    return int(row[0])
        except Exception as e:
            logger.error(f"统计开通设备明细失败: {e}")
            raise
