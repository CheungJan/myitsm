# -*- coding: utf-8 -*-
"""
门店关闭单仓储层
处理 TIT18_STORE_CLOSE 表的数据访问操作
"""

import logging
from typing import Dict, Any, Optional

from app.extensions.oracle import get_oracle_connection

logger = logging.getLogger(__name__)


class StoreCloseRepository:
    """门店关闭单仓储类"""

    def list_store_closes(
        self,
        store_id: Optional[str] = None,
        close_type: Optional[str] = None,
        current_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        查询门店关闭单列表（TIT18_STORE_CLOSE）。

        Args:
            store_id: 门店编码
            close_type: 关闭类型
            current_status: 当前状态
            page: 页码
            page_size: 每页大小

        Returns:
            包含列表和分页信息的字典
        """
        offset = (page - 1) * page_size

        sql_count = """
            SELECT COUNT(*)
            FROM TIT18_STORE_CLOSE
            WHERE NVL(USEFLG, '1') = '1'
        """

        sql_list = """
            SELECT
                STORE_CLOSE_ID,
                STORE_ID,
                REQUEST_TIME,
                REQUSET_PAPER_ID,
                CLOSE_TYPE,
                TEMP_CLOSE_DATE_BEGIN,
                TEMP_CLOSE_DATE_END,
                EXPECTED_COMPLETION_TIME,
                SHORT_DESCRIPTION,
                DETAIL_DESCRIPTION,
                CURRENT_STATUS,
                IS_SUCCESS,
                IS_OLD,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                FIRSTOR,
                FIRST_TIME,
                LEAVE_TIME,
                CLOSE_TIME,
                REVISIT_TIME
            FROM TIT18_STORE_CLOSE
            WHERE NVL(USEFLG, '1') = '1'
        """

        params = {}

        if store_id:
            sql_count += " AND STORE_ID = :store_id"
            sql_list += " AND STORE_ID = :store_id"
            params["store_id"] = store_id

        if close_type:
            sql_count += " AND CLOSE_TYPE = :close_type"
            sql_list += " AND CLOSE_TYPE = :close_type"
            params["close_type"] = close_type

        if current_status:
            sql_count += " AND CURRENT_STATUS = :current_status"
            sql_list += " AND CURRENT_STATUS = :current_status"
            params["current_status"] = current_status

        sql_list += " ORDER BY CREATE_TIME DESC"

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    # 查询总数
                    cursor.execute(sql_count, params)
                    total = cursor.fetchone()[0]

                    # 查询列表
                    sql_list += " OFFSET :offset ROWS FETCH NEXT :page_size ROWS ONLY"
                    params["offset"] = offset
                    params["page_size"] = page_size

                    cursor.execute(sql_list, params)
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    items = [dict(zip(columns, row)) for row in rows]

                    return {
                        "items": items,
                        "total": total,
                        "page": page,
                        "page_size": page_size,
                        "total_pages": (total + page_size - 1) // page_size,
                    }
        except Exception as e:
            logger.error(f"查询门店关闭单列表失败: {e}")
            raise

    def get_store_close(self, store_close_id: str) -> Optional[Dict[str, Any]]:
        """
        查询单个门店关闭单详情（TIT18_STORE_CLOSE）。

        Args:
            store_close_id: 门店关闭单ID

        Returns:
            门店关闭单详情字典，如果不存在则返回 None
        """
        sql = """
            SELECT
                STORE_CLOSE_ID,
                STORE_ID,
                REQUEST_TIME,
                REQUSET_PAPER_ID,
                CLOSE_TYPE,
                TEMP_CLOSE_DATE_BEGIN,
                TEMP_CLOSE_DATE_END,
                EXPECTED_COMPLETION_TIME,
                SHORT_DESCRIPTION,
                DETAIL_DESCRIPTION,
                CURRENT_STATUS,
                IS_SUCCESS,
                IS_OLD,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                FIRSTOR,
                FIRST_TIME,
                LEAVE_TIME,
                CLOSE_TIME,
                REVISIT_TIME
            FROM TIT18_STORE_CLOSE
            WHERE STORE_CLOSE_ID = :store_close_id
              AND NVL(USEFLG, '1') = '1'
        """

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"store_close_id": store_close_id})
                    row = cursor.fetchone()
                    if row:
                        columns = [col[0].lower() for col in cursor.description]
                        return dict(zip(columns, row))
                    return None
        except Exception as e:
            logger.error(f"查询门店关闭单详情失败: {e}")
            raise

    def create_store_close(
        self,
        store_close_id: str,
        store_id: str,
        creator: str,
        request_time: Optional[str] = None,
        request_paper_id: Optional[str] = None,
        close_type: Optional[str] = None,
        temp_close_date_begin: Optional[str] = None,
        temp_close_date_end: Optional[str] = None,
        expected_completion_time: Optional[str] = None,
        short_description: Optional[str] = None,
        detail_description: Optional[str] = None,
        current_status: str = "1",
        is_old: str = "0",
        is_success: Optional[str] = None,
    ) -> bool:
        """
        新增门店关闭单（TIT18_STORE_CLOSE）。

        Args:
            store_close_id: 门店关闭单ID
            store_id: 门店编码
            creator: 创建人
            request_time: 请求时间
            request_paper_id: 申请单ID
            close_type: 关闭类型
            temp_close_date_begin: 临时关闭开始日期
            temp_close_date_end: 临时关闭结束日期
            expected_completion_time: 预计完成时间
            short_description: 简述
            detail_description: 详情
            current_status: 当前状态
            is_old: 是否补单
            is_success: 是否成功

        Returns:
            是否新增成功
        """
        sql = """
            INSERT INTO TIT18_STORE_CLOSE (
                STORE_CLOSE_ID,
                STORE_ID,
                REQUEST_TIME,
                REQUSET_PAPER_ID,
                CLOSE_TYPE,
                TEMP_CLOSE_DATE_BEGIN,
                TEMP_CLOSE_DATE_END,
                EXPECTED_COMPLETION_TIME,
                SHORT_DESCRIPTION,
                DETAIL_DESCRIPTION,
                CURRENT_STATUS,
                IS_OLD,
                IS_SUCCESS,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                USEFLG
            ) VALUES (
                :store_close_id,
                :store_id,
                TO_DATE(:request_time, 'YYYY-MM-DD HH24:MI:SS'),
                :request_paper_id,
                :close_type,
                TO_DATE(:temp_close_date_begin, 'YYYY-MM-DD HH24:MI:SS'),
                TO_DATE(:temp_close_date_end, 'YYYY-MM-DD HH24:MI:SS'),
                TO_DATE(:expected_completion_time, 'YYYY-MM-DD HH24:MI:SS'),
                :short_description,
                :detail_description,
                :current_status,
                :is_old,
                :is_success,
                SYSDATE,
                :creator,
                SYSDATE,
                :creator,
                '1'
            )
        """

        params = {
            "store_close_id": store_close_id,
            "store_id": store_id,
            "request_time": request_time,
            "request_paper_id": request_paper_id,
            "close_type": close_type,
            "temp_close_date_begin": temp_close_date_begin,
            "temp_close_date_end": temp_close_date_end,
            "expected_completion_time": expected_completion_time,
            "short_description": short_description,
            "detail_description": detail_description,
            "current_status": current_status,
            "is_old": is_old,
            "is_success": is_success,
            "creator": creator,
        }

        for key in [
            "request_time",
            "temp_close_date_begin",
            "temp_close_date_end",
            "expected_completion_time",
        ]:
            if not params[key]:
                params[key] = None

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"新增门店关闭单失败: {e}")
            raise
