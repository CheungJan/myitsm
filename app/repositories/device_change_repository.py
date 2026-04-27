# -*- coding: utf-8 -*-
"""
设备变更单仓储
文件说明：对接TIT16_DEVICE_CHANGE和TMM22_CUSTOMERS_HISTORY表，实现磁卡号变更历史记录优化
作者：Cascade
创建时间：2026-04-08

关联表：
- TIT16_DEVICE_CHANGE：设备变更单主表
- TMM22_CUSTOMERS_HISTORY：门店客户历史记录表（优化新增）
- TMM22_CUSTOMERS：客户主表
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class DeviceChangeRepository:
    """设备变更单仓储类"""

    def __init__(self):
        self.table = "TIT16_DEVICE_CHANGE"
        self.history_table = "TMM22_CUSTOMERS_HISTORY"
        self.customer_table = "TMM22_CUSTOMERS"

    def get_by_id(self, device_change_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取设备变更单详情
        
        Args:
            device_change_id: 变更单ID
            
        Returns:
            变更单详情字典，不存在返回None
        """
        sql = f"""
            SELECT 
                DEVICE_CHANGE_ID,
                STORE_ID,
                REQUSET_PAPER_ID,
                CHANGE_TYPE,
                DEVICE_ID,
                NEW_CONTACTOR,
                NEW_TEL,
                NEW_ADDRESS,
                NEW_STORE_CARD,
                NEW_STORE_ID,
                IS_STORE_INSIDE_CHANGE,
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
            WHERE DEVICE_CHANGE_ID = :device_change_id
              AND USEFLG = '1'
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"device_change_id": device_change_id})
                    row = cursor.fetchone()
                    if not row:
                        return None
                    columns = [col[0].lower() for col in cursor.description]
                    return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"获取设备变更单详情失败: {e}")
            raise

    def list_device_changes(
        self,
        store_id: Optional[str] = None,
        custcard: Optional[str] = None,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        device_change_id: Optional[str] = None,
        new_store_card: Optional[str] = None,
        new_tel: Optional[str] = None,
        change_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        获取设备变更单列表
        
        Args:
            store_id: 门店ID过滤
            change_type: 变更类型过滤（CK/BQ/BG）
            status: 状态过滤
            page: 页码
            page_size: 每页数量
            
        Returns:
            包含列表和总数的字典
        """
        where_clauses = ["NVL(D.USEFLG, '1') = '1'", "D.STORE_ID = C.CUSTCD(+)"]
        params: Dict[str, Any] = {}

        if store_id:
            where_clauses.append("D.STORE_ID = :store_id")
            params["store_id"] = store_id
        if custcard:
            where_clauses.append("C.CUSTCARD LIKE :custcard")
            params["custcard"] = f"%{custcard}%"
        if begin_date:
            where_clauses.append("TO_CHAR(D.CREATE_TIME, 'YYYY-MM-DD') >= :begin_date")
            params["begin_date"] = begin_date
        if end_date:
            where_clauses.append("TO_CHAR(D.CREATE_TIME, 'YYYY-MM-DD') <= :end_date")
            params["end_date"] = end_date
        if device_change_id:
            where_clauses.append("D.DEVICE_CHANGE_ID LIKE :device_change_id")
            params["device_change_id"] = f"%{device_change_id}%"
        if new_store_card:
            where_clauses.append("D.NEW_STORE_CARD LIKE :new_store_card")
            params["new_store_card"] = f"%{new_store_card}%"
        if new_tel:
            where_clauses.append("D.NEW_TEL LIKE :new_tel")
            params["new_tel"] = f"%{new_tel}%"
        if change_type:
            where_clauses.append("D.CHANGE_TYPE = :change_type")
            params["change_type"] = change_type
        if status:
            where_clauses.append("D.CURRENT_STATUS = :status")
            params["status"] = status

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*)
            FROM {self.table} D, TMM22_CUSTOMERS C
            WHERE {where_sql}
        """

        list_sql = f"""
            SELECT 
                D.DEVICE_CHANGE_ID,
                D.STORE_ID,
                D.CHANGE_TYPE,
                D.DEVICE_ID,
                D.NEW_STORE_CARD,
                D.NEW_STORE_ID,
                D.NEW_TEL,
                D.CURRENT_STATUS,
                D.CREATE_TIME,
                D.CREATE_BY,
                D.FIRSTOR,
                D.REMARK,
                C.CUSTCARD,
                C.CUSTNM
            FROM {self.table} D, TMM22_CUSTOMERS C
            WHERE {where_sql}
            ORDER BY D.DEVICE_CHANGE_ID DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    # 查询总数
                    cursor.execute(count_sql, params)
                    total = cursor.fetchone()[0]

                    # 查询列表
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
            logger.error(f"获取设备变更单列表失败: {e}")
            raise

    def create_device_change(
        self,
        device_change_id: str,
        store_id: str,
        change_type: str,
        device_id: Optional[str] = None,
        new_contactor: Optional[str] = None,
        new_tel: Optional[str] = None,
        new_address: Optional[str] = None,
        new_store_card: Optional[str] = None,
        new_store_id: Optional[str] = None,
        is_store_inside_change: str = "N",
        current_status: str = "00",
        oper_cd: Optional[str] = None,
        remark: Optional[str] = None,
    ) -> bool:
        """
        创建设备变更单
        
        Args:
            device_change_id: 变更单ID
            store_id: 原门店ID
            change_type: 变更类型（CK/BQ/BG）
            device_id: 整机ID
            new_contactor: 变更后联系人
            new_tel: 变更后电话
            new_address: 变更后地址
            new_store_card: 变更后磁卡号（CK类型用）
            new_store_id: 变更后门店ID（BG类型用）
            is_store_inside_change: 是否店内移机
            current_status: 当前状态
            oper_cd: 操作人
            remark: 备注
            
        Returns:
            是否创建成功
        """
        sql = f"""
            INSERT INTO {self.table} (
                DEVICE_CHANGE_ID, STORE_ID, REQUSET_PAPER_ID,
                CHANGE_TYPE, DEVICE_ID, NEW_CONTACTOR,
                NEW_TEL, NEW_ADDRESS, NEW_STORE_CARD,
                NEW_STORE_ID, IS_STORE_INSIDE_CHANGE, CURRENT_STATUS,
                CREATE_TIME, UPDATE_TIME, CREATE_BY, UPDATE_BY,
                FIRSTOR, USEFLG, REMARK
            ) VALUES (
                :device_change_id, :store_id, NULL,
                :change_type, :device_id, :new_contactor,
                :new_tel, :new_address, :new_store_card,
                :new_store_id, :is_store_inside_change, :current_status,
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
                            "device_change_id": device_change_id,
                            "store_id": store_id,
                            "change_type": change_type,
                            "device_id": device_id,
                            "new_contactor": new_contactor,
                            "new_tel": new_tel,
                            "new_address": new_address,
                            "new_store_card": new_store_card,
                            "new_store_id": new_store_id,
                            "is_store_inside_change": is_store_inside_change,
                            "current_status": current_status,
                            "oper_cd": oper_cd,
                            "remark": remark,
                        },
                    )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"创建设备变更单失败: {e}")
            raise

    def update_status(
        self,
        device_change_id: str,
        old_status: str,
        new_status: str,
        oper_cd: Optional[str] = None,
    ) -> bool:
        """
        更新设备变更单状态（带乐观锁）
        
        Args:
            device_change_id: 变更单ID
            old_status: 当前状态（用于乐观锁）
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
            WHERE DEVICE_CHANGE_ID = :device_change_id
              AND CURRENT_STATUS = :old_status
              AND USEFLG = '1'
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "device_change_id": device_change_id,
                            "old_status": old_status,
                            "new_status": new_status,
                            "oper_cd": oper_cd,
                        },
                    )
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新设备变更单状态失败: {e}")
            raise

    def get_customer_info(self, store_id: str) -> Optional[Dict[str, Any]]:
        """
        获取门店当前信息（用于变更前保存历史）
        
        Args:
            store_id: 门店ID
            
        Returns:
            门店信息字典
        """
        sql = f"""
            SELECT CUSTCD, CUSTCARD, CUSTNM, ADDRESS, PHONENO
            FROM {self.customer_table}
            WHERE CUSTCD = :store_id
              AND USEFLG = '1'
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"store_id": store_id})
                    row = cursor.fetchone()
                    if not row:
                        return None
                    columns = [col[0].lower() for col in cursor.description]
                    return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"获取门店信息失败: {e}")
            raise

    def update_customer_card(
        self,
        store_id: str,
        new_card: str,
        oper_cd: Optional[str] = None,
    ) -> bool:
        """
        更新门店磁卡号
        
        Args:
            store_id: 门店ID
            new_card: 新磁卡号
            oper_cd: 操作人
            
        Returns:
            是否更新成功
        """
        sql = f"""
            UPDATE {self.customer_table}
            SET CUSTCARD = :new_card,
                UPDATE_TIME = SYSDATE
            WHERE CUSTCD = :store_id
              AND USEFLG = '1'
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {"store_id": store_id, "new_card": new_card},
                    )
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新门店磁卡号失败: {e}")
            raise

    def create_history_record(
        self,
        store_id: str,
        change_type: str,
        change_time: datetime,
        device_change_id: Optional[str] = None,
        oper_cd: Optional[str] = None,
        old_custcard: Optional[str] = None,
        new_custcard: Optional[str] = None,
        change_reason: Optional[str] = None,
    ) -> bool:
        """
        创建历史记录（核心优化方法）
        
        在磁卡号变更前调用，保存旧磁卡号信息到历史表
        
        Args:
            store_id: 门店ID
            change_type: 变更类型（CK/BQ/BG/INIT）
            change_time: 变更时间
            device_change_id: 关联变更单ID
            oper_cd: 操作人
            old_custcard: 原磁卡号
            new_custcard: 新磁卡号
            change_reason: 变更原因
            
        Returns:
            是否创建成功
        """
        # 获取当前门店信息
        customer = self.get_customer_info(store_id)
        if not customer:
            logger.warning(f"门店不存在: {store_id}")
            return False

        sql = f"""
            INSERT INTO {self.history_table} (
                CUSTCD, CUSTCARD, CUSTNM, STORE_ID,
                CHANGE_TYPE, CHANGE_REASON, OLD_CUSTCARD, NEW_CUSTCARD,
                CHANGE_TIME, DEVICE_CHANGE_ID, OPER_CD, USEFLG,
                CREATE_TIME, UPDATE_TIME
            ) VALUES (
                :custcd, :custcard, :custnm, :store_id,
                :change_type, :change_reason, :old_custcard, :new_custcard,
                :change_time, :device_change_id, :oper_cd, '1',
                SYSDATE, SYSDATE
            )
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "custcd": customer.get("custcd"),
                            "custcard": new_custcard or customer.get("custcard"),
                            "custnm": customer.get("custnm"),
                            "store_id": store_id,
                            "change_type": change_type,
                            "change_reason": change_reason,
                            "old_custcard": old_custcard,
                            "new_custcard": new_custcard,
                            "change_time": change_time,
                            "device_change_id": device_change_id,
                            "oper_cd": oper_cd,
                        },
                    )
                    conn.commit()
                    logger.info(f"历史记录创建成功: store_id={store_id}, type={change_type}")
                    return True
        except Exception as e:
            logger.error(f"创建历史记录失败: {e}")
            raise

    def get_history_by_store(
        self,
        store_id: str,
        change_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        查询门店变更历史
        
        Args:
            store_id: 门店ID
            change_type: 变更类型过滤
            page: 页码
            page_size: 每页数量
            
        Returns:
            历史记录列表
        """
        where_clauses = ["STORE_ID = :store_id", "USEFLG = '1'"]
        params = {"store_id": store_id}

        if change_type:
            where_clauses.append("CHANGE_TYPE = :change_type")
            params["change_type"] = change_type

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*) FROM {self.history_table}
            WHERE {where_sql}
        """

        list_sql = f"""
            SELECT 
                HISTORY_ID, CUSTCD, CUSTCARD, CUSTNM, STORE_ID,
                CHANGE_TYPE, CHANGE_REASON, OLD_CUSTCARD, NEW_CUSTCARD,
                CHANGE_TIME, DEVICE_CHANGE_ID, OPER_CD, CREATE_TIME
            FROM {self.history_table}
            WHERE {where_sql}
            ORDER BY CHANGE_TIME DESC
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
            logger.error(f"查询门店变更历史失败: {e}")
            raise

    def get_history_by_card(
        self,
        custcard: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        根据磁卡号查询变更历史（解决老系统无法查询的问题）
        
        Args:
            custcard: 磁卡号
            page: 页码
            page_size: 每页数量
            
        Returns:
            历史记录列表
        """
        where_sql = """
            (CUSTCARD = :custcard OR OLD_CUSTCARD = :custcard OR NEW_CUSTCARD = :custcard)
            AND USEFLG = '1'
        """
        params = {"custcard": custcard}

        count_sql = f"""
            SELECT COUNT(*) FROM {self.history_table}
            WHERE {where_sql}
        """

        list_sql = f"""
            SELECT 
                HISTORY_ID, CUSTCD, CUSTCARD, CUSTNM, STORE_ID,
                CHANGE_TYPE, CHANGE_REASON, OLD_CUSTCARD, NEW_CUSTCARD,
                CHANGE_TIME, DEVICE_CHANGE_ID, OPER_CD, CREATE_TIME
            FROM {self.history_table}
            WHERE {where_sql}
            ORDER BY CHANGE_TIME DESC
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
            logger.error(f"查询磁卡号变更历史失败: {e}")
            raise
