# -*- coding: utf-8 -*-
"""
日常保养单仓储
文件说明：对接TIT17_MAINTENANCE表（日常保养单主表）
作者：Cascade
创建时间：2026-04-08

关联表：
- TIT17_MAINTENANCE：日常保养单主表
- TIT17_CUST_POS_DAILY：保养设备明细（子表后续扩展）
- TIT23_MAINTENANCE_D2D：上门服务记录（公用附表）
- TIT24_MAINTENANCE_RV：客户回访记录
- TIT27_CLOSE_BILLS：关单记录

单据类型码：BY（日常保养）
"""

import logging
from typing import Dict, List, Optional, Any

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class MaintenanceDailyRepository:
    """日常保养单仓储类"""

    def __init__(self):
        self.table = "TIT17_MAINTENANCE"
        self.pk_field = "DAILY_MAINTENANCE_ID"

    def get_by_id(self, daily_maintenance_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取日常保养单详情
        
        Args:
            daily_maintenance_id: 保养单ID
            
        Returns:
            保养单详情字典
        """
        sql = f"""
            SELECT 
                DAILY_MAINTENANCE_ID,
                STORE_ID,
                MAINTENANCE_PLAN_ID,
                HAS_VIDEO_DEVICE,
                VIDEO_DEVICE_STATUS,
                MAINTENANCE_TYPE,
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
            WHERE {self.pk_field} = :daily_maintenance_id
              AND USEFLG = '1'
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"daily_maintenance_id": daily_maintenance_id})
                    row = cursor.fetchone()
                    if not row:
                        return None
                    columns = [col[0].lower() for col in cursor.description]
                    return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"获取日常保养单详情失败: {e}")
            raise

    def list_maintenance_dailies(
        self,
        store_id: Optional[str] = None,
        status: Optional[str] = None,
        maintenance_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        获取日常保养单列表
        
        Args:
            store_id: 门店ID过滤
            status: 状态过滤
            maintenance_type: 保养类型过滤
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
        if maintenance_type:
            where_clauses.append("MAINTENANCE_TYPE = :maintenance_type")
            params["maintenance_type"] = maintenance_type

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*) FROM {self.table}
            WHERE {where_sql}
        """

        list_sql = f"""
            SELECT 
                DAILY_MAINTENANCE_ID,
                STORE_ID,
                MAINTENANCE_PLAN_ID,
                HAS_VIDEO_DEVICE,
                VIDEO_DEVICE_STATUS,
                MAINTENANCE_TYPE,
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
            logger.error(f"获取日常保养单列表失败: {e}")
            raise

    def create_maintenance_daily(
        self,
        daily_maintenance_id: str,
        store_id: str,
        maintenance_plan_id: Optional[str] = None,
        has_video_device: str = "N",
        video_device_status: Optional[str] = None,
        maintenance_type: Optional[str] = None,
        current_status: str = "00",
        oper_cd: Optional[str] = None,
        remark: Optional[str] = None,
    ) -> bool:
        """
        创建日常保养单
        
        Args:
            daily_maintenance_id: 保养单ID
            store_id: 门店ID
            maintenance_plan_id: 保养计划ID
            has_video_device: 是否有视频设备（Y/N）
            video_device_status: 视频设备状态
            maintenance_type: 保养类型
            current_status: 当前状态
            oper_cd: 操作人
            remark: 备注
            
        Returns:
            是否创建成功
        """
        sql = f"""
            INSERT INTO {self.table} (
                DAILY_MAINTENANCE_ID, STORE_ID, MAINTENANCE_PLAN_ID,
                HAS_VIDEO_DEVICE, VIDEO_DEVICE_STATUS, MAINTENANCE_TYPE,
                CURRENT_STATUS, CREATE_TIME, UPDATE_TIME, CREATE_BY,
                UPDATE_BY, FIRSTOR, USEFLG, REMARK
            ) VALUES (
                :daily_maintenance_id, :store_id, :maintenance_plan_id,
                :has_video_device, :video_device_status, :maintenance_type,
                :current_status, SYSDATE, SYSDATE, :oper_cd,
                :oper_cd, :oper_cd, '1', :remark
            )
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "daily_maintenance_id": daily_maintenance_id,
                            "store_id": store_id,
                            "maintenance_plan_id": maintenance_plan_id,
                            "has_video_device": has_video_device,
                            "video_device_status": video_device_status,
                            "maintenance_type": maintenance_type,
                            "current_status": current_status,
                            "oper_cd": oper_cd,
                            "remark": remark,
                        },
                    )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"创建日常保养单失败: {e}")
            raise

    def update_status(
        self,
        daily_maintenance_id: str,
        old_status: str,
        new_status: str,
        oper_cd: Optional[str] = None,
    ) -> bool:
        """
        更新保养单状态（带乐观锁）
        
        Args:
            daily_maintenance_id: 保养单ID
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
            WHERE {self.pk_field} = :daily_maintenance_id
              AND CURRENT_STATUS = :old_status
              AND USEFLG = '1'
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "daily_maintenance_id": daily_maintenance_id,
                            "old_status": old_status,
                            "new_status": new_status,
                            "oper_cd": oper_cd,
                        },
                    )
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新保养单状态失败: {e}")
            raise

    def list_cust_pos_daily(self, daily_maintenance_id: str) -> List[Dict[str, Any]]:
        """
        查询保养设备明细（TIT17_CUST_POS_DAILY）。

        Args:
            daily_maintenance_id: 日常保养单ID

        Returns:
            保养设备明细列表
        """
        sql = """
            SELECT
                DAILY_MAINTENANCE_ID,
                BUSINESS_OPERATION_ID,
                CUSTCD,
                EID,
                ITEMCD,
                STARTDATE,
                SYSINFO,
                SOFTINFO,
                POSUPDDATE,
                POSINFO,
                AREA,
                STATUS,
                TYPFLG,
                MAINTENANCEDATE,
                MAINTENANCETYP,
                REQUEST_ENGINNER_ID,
                REQUEST_TIME,
                SHORT_DESCRIPTION,
                DETAIL_DESCRIPTION,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                USEFLG
            FROM TIT17_CUST_POS_DAILY
            WHERE DAILY_MAINTENANCE_ID = :daily_maintenance_id
              AND NVL(USEFLG, '1') = '1'
            ORDER BY BUSINESS_OPERATION_ID DESC, CREATE_TIME DESC
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"daily_maintenance_id": daily_maintenance_id})
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"查询保养设备明细失败: {e}")
            raise

    def create_cust_pos_daily(
        self,
        daily_maintenance_id: str,
        business_operation_id: int,
        cust_cd: str,
        eid: str,
        item_cd: str,
        typflg: str,
        creator: str,
        status: str = "1",
        start_date: Optional[str] = None,
        sys_info: Optional[str] = None,
        soft_info: Optional[str] = None,
        pos_upd_date: Optional[str] = None,
        pos_info: Optional[str] = None,
        area: Optional[str] = None,
        maintenance_date: Optional[str] = None,
        maintenance_typ: Optional[str] = None,
        request_enginner_id: Optional[str] = None,
        request_time: Optional[str] = None,
        short_description: Optional[str] = None,
        detail_description: Optional[str] = None,
    ) -> bool:
        """
        新增保养设备明细（TIT17_CUST_POS_DAILY）。

        Args:
            daily_maintenance_id: 日常保养单ID
            business_operation_id: 业务流水操作ID
            cust_cd: 客户编码
            eid: 设备ID
            item_cd: 设备类型
            typflg: 设备类型标识
            creator: 创建人
            status: 状态
            start_date: 启用日期
            sys_info: 系统信息
            soft_info: 软件信息
            pos_upd_date: 设备更新时间
            pos_info: 设备信息
            area: 区域
            maintenance_date: 保养日期
            maintenance_typ: 保养类型
            request_enginner_id: 请求工程师
            request_time: 请求时间
            short_description: 简述
            detail_description: 详情

        Returns:
            是否新增成功
        """
        sql = """
            INSERT INTO TIT17_CUST_POS_DAILY (
                DAILY_MAINTENANCE_ID,
                BUSINESS_OPERATION_ID,
                CUSTCD,
                EID,
                ITEMCD,
                STARTDATE,
                SYSINFO,
                SOFTINFO,
                POSUPDDATE,
                POSINFO,
                AREA,
                STATUS,
                TYPFLG,
                MAINTENANCEDATE,
                MAINTENANCETYP,
                REQUEST_ENGINNER_ID,
                REQUEST_TIME,
                SHORT_DESCRIPTION,
                DETAIL_DESCRIPTION,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                USEFLG
            ) VALUES (
                :daily_maintenance_id,
                :business_operation_id,
                :cust_cd,
                :eid,
                :item_cd,
                TO_DATE(:start_date, 'YYYY-MM-DD HH24:MI:SS'),
                :sys_info,
                :soft_info,
                TO_DATE(:pos_upd_date, 'YYYY-MM-DD HH24:MI:SS'),
                :pos_info,
                :area,
                :status,
                :typflg,
                TO_DATE(:maintenance_date, 'YYYY-MM-DD HH24:MI:SS'),
                :maintenance_typ,
                :request_enginner_id,
                TO_DATE(:request_time, 'YYYY-MM-DD HH24:MI:SS'),
                :short_description,
                :detail_description,
                SYSDATE,
                :creator,
                SYSDATE,
                :creator,
                '1'
            )
        """
        params = {
            "daily_maintenance_id": daily_maintenance_id,
            "business_operation_id": business_operation_id,
            "cust_cd": cust_cd,
            "eid": eid,
            "item_cd": item_cd,
            "start_date": start_date,
            "sys_info": sys_info,
            "soft_info": soft_info,
            "pos_upd_date": pos_upd_date,
            "pos_info": pos_info,
            "area": area,
            "status": status,
            "typflg": typflg,
            "maintenance_date": maintenance_date,
            "maintenance_typ": maintenance_typ,
            "request_enginner_id": request_enginner_id,
            "request_time": request_time,
            "short_description": short_description,
            "detail_description": detail_description,
            "creator": creator,
        }

        for key in ["start_date", "pos_upd_date", "maintenance_date", "request_time"]:
            if not params[key]:
                params[key] = None

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"新增保养设备明细失败: {e}")
            raise
