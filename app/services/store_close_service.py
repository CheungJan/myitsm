# -*- coding: utf-8 -*-
"""
门店关闭单服务层
处理 TIT18_STORE_CLOSE 的业务逻辑
"""

import logging
from typing import Dict, Any, Optional

from app.repositories.store_close_repository import StoreCloseRepository
from app.utils.id_generator import generate_business_id

logger = logging.getLogger(__name__)


class StoreCloseService:
    """门店关闭单服务类"""

    def __init__(self):
        self.repository = StoreCloseRepository()

    def list_store_closes(
        self,
        store_id: Optional[str] = None,
        close_type: Optional[str] = None,
        current_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        查询门店关闭单列表。

        Args:
            store_id: 门店编码
            close_type: 关闭类型
            current_status: 当前状态
            page: 页码
            page_size: 每页大小

        Returns:
            包含列表和分页信息的字典
        """
        return self.repository.list_store_closes(
            store_id=store_id,
            close_type=close_type,
            current_status=current_status,
            page=page,
            page_size=page_size,
        )

    def get_store_close(self, store_close_id: str) -> Optional[Dict[str, Any]]:
        """
        查询单个门店关闭单详情。

        Args:
            store_close_id: 门店关闭单ID

        Returns:
            门店关闭单详情字典，如果不存在则返回 None
        """
        return self.repository.get_store_close(store_close_id)

    def create_store_close(
        self,
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
    ) -> Dict[str, Any]:
        """
        新增门店关闭单。

        Args:
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
            包含新增结果的字典
        """
        # 生成门店关闭单ID
        store_close_id = generate_business_id()

        # 新增门店关闭单
        success = self.repository.create_store_close(
            store_close_id=store_close_id,
            store_id=store_id,
            creator=creator,
            request_time=request_time,
            request_paper_id=request_paper_id,
            close_type=close_type,
            temp_close_date_begin=temp_close_date_begin,
            temp_close_date_end=temp_close_date_end,
            expected_completion_time=expected_completion_time,
            short_description=short_description,
            detail_description=detail_description,
            current_status=current_status,
            is_old=is_old,
            is_success=is_success,
        )

        if success:
            return {
                "success": True,
                "store_close_id": store_close_id,
                "message": "门店关闭单新增成功",
            }
        else:
            return {"success": False, "message": "门店关闭单新增失败"}
