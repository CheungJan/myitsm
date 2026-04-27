# -*- coding: utf-8 -*-
"""
门店关闭单 API
处理 TIT18_STORE_CLOSE 的 HTTP 请求
"""

import logging
from flask import Blueprint, request

from app.services.store_close_service import StoreCloseService
from app.utils.response import success_response, error_response

logger = logging.getLogger(__name__)

# 创建 Blueprint
store_close_bp = Blueprint("store_close", __name__, url_prefix="/api/v1/store-closes")

# 端点列表
# - GET /api/v1/store-closes - 查询门店关闭单列表
# - GET /api/v1/store-closes/<store_close_id> - 查询单个门店关闭单详情
# - POST /api/v1/store-closes - 新增门店关闭单

store_close_service = StoreCloseService()


@store_close_bp.route("", methods=["GET"])
def list_store_closes():
    """
    查询门店关闭单列表

    Query Parameters:
        store_id: 门店编码
        close_type: 关闭类型
        current_status: 当前状态
        page: 页码（默认1）
        page_size: 每页大小（默认20）
    """
    try:
        store_id = request.args.get("store_id")
        close_type = request.args.get("close_type")
        current_status = request.args.get("current_status")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))

        result = store_close_service.list_store_closes(
            store_id=store_id,
            close_type=close_type,
            current_status=current_status,
            page=page,
            page_size=page_size,
        )

        return success_response(data=result)
    except Exception as e:
        logger.error(f"查询门店关闭单列表失败: {e}")
        return error_response(message="查询门店关闭单列表失败")


@store_close_bp.route("/<store_close_id>", methods=["GET"])
def get_store_close(store_close_id: str):
    """
    查询单个门店关闭单详情

    Path Parameters:
        store_close_id: 门店关闭单ID
    """
    try:
        result = store_close_service.get_store_close(store_close_id)

        if result:
            return success_response(data=result)
        else:
            return error_response(message="门店关闭单不存在", code=404)
    except Exception as e:
        logger.error(f"查询门店关闭单详情失败: {e}")
        return error_response(message="查询门店关闭单详情失败")


@store_close_bp.route("", methods=["POST"])
def create_store_close():
    """
    新增门店关闭单

    Request Body:
        store_id: 门店编码（必填）
        creator: 创建人（必填）
        request_time: 请求时间
        request_paper_id: 申请单ID
        close_type: 关闭类型
        temp_close_date_begin: 临时关闭开始日期
        temp_close_date_end: 临时关闭结束日期
        expected_completion_time: 预计完成时间
        short_description: 简述
        detail_description: 详情
        current_status: 当前状态（默认1）
        is_old: 是否补单（默认0）
        is_success: 是否成功
    """
    try:
        data = request.get_json()

        # 必填参数校验
        if not data.get("store_id"):
            return error_response(message="门店编码不能为空")
        if not data.get("creator"):
            return error_response(message="创建人不能为空")

        result = store_close_service.create_store_close(
            store_id=data.get("store_id"),
            creator=data.get("creator"),
            request_time=data.get("request_time"),
            request_paper_id=data.get("request_paper_id"),
            close_type=data.get("close_type"),
            temp_close_date_begin=data.get("temp_close_date_begin"),
            temp_close_date_end=data.get("temp_close_date_end"),
            expected_completion_time=data.get("expected_completion_time"),
            short_description=data.get("short_description"),
            detail_description=data.get("detail_description"),
            current_status=data.get("current_status", "1"),
            is_old=data.get("is_old", "0"),
            is_success=data.get("is_success"),
        )

        if result["success"]:
            return success_response(data=result, message=result["message"])
        else:
            return error_response(message=result["message"])
    except Exception as e:
        logger.error(f"新增门店关闭单失败: {e}")
        return error_response(message="新增门店关闭单失败")
