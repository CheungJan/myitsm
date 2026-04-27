"""
客户主数据 API。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 客户生命周期管理端点
    - 对应 base_cust.pbl 的客户管理功能
"""

from __future__ import annotations

from flask import Blueprint, request

from app.services.customer_service import CustomerService
from app.utils.response import error_response, success_response

__all__ = ["customer_bp"]

customer_bp = Blueprint("customer", __name__)
_service = CustomerService()




@customer_bp.get("/customers")
def list_customers():
    """
    获取客户列表，支持状态过滤。

    查询参数：
        - status: 生命周期状态（TEMP/PENDING/ACTIVE/INVALID）
        - use_flg: 有效标志（'1'有效/'0'无效）

    返回值：
        Response: 统一结构 JSON 响应

    示例：
        GET /api/v1/customers?status=TEMP
        GET /api/v1/customers?use_flg=1
    """
    status = request.args.get("status")
    use_flg = request.args.get("use_flg")

    customers = _service.list_customers(status=status, use_flg=use_flg)
    return success_response(data=customers)


@customer_bp.get("/customers/<cust_cd>")
def get_customer(cust_cd: str):
    """
    获取客户详情。

    参数：
        cust_cd: 客户代码

    返回值：
        Response: 统一结构 JSON 响应

    示例：
        GET /api/v1/customers/C0000001
    """
    customer = _service.get_customer_detail(cust_cd)
    if customer is None:
        return error_response(message="客户不存在", code=404)

    return success_response(data=customer)


@customer_bp.get("/customers/check-card/<cust_card>")
def check_card(cust_card: str):
    """
    检查磁卡号是否已存在。

    参数：
        cust_card: 磁卡号

    返回值：
        Response: 统一结构 JSON 响应

    示例：
        GET /api/v1/customers/check-card/12345678
    """
    existing = _service.check_card_exists(cust_card)
    return success_response(data={
        "exists": existing is not None,
        "customer": existing,
    })


@customer_bp.post("/customers/from-preplan")
def create_from_preplan():
    """
    从预计划创建临时客户。

    请求体：
        {
            "preplan_id": "P001",
            "cust_info": {
                "cust_nm": "客户名称",
                "cust_card": "磁卡号",
                "address": "地址",
                "phone_no": "电话",
                "contactor": "联系人",
                "class_cd": "类别",
                "busi_typ": "业务类型"
            },
            "oper_cd": "操作员"
        }

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    preplan_id = data.get("preplan_id", "").strip()
    cust_info = data.get("cust_info", {})
    oper_cd = data.get("oper_cd", "").strip()

    if not preplan_id:
        return error_response(message="缺少参数 preplan_id", code=400)
    if not cust_info.get("cust_card"):
        return error_response(message="缺少 cust_info.cust_card", code=400)
    if not oper_cd:
        return error_response(message="缺少参数 oper_cd", code=400)

    customer = _service.create_temp_from_preplan(preplan_id, cust_info, oper_cd)
    if customer is None:
        return error_response(message="磁卡号已存在或创建失败", code=409)

    return success_response(data=customer, message="临时客户创建成功")


@customer_bp.post("/customers/<cust_cd>/promote")
def promote_customer(cust_cd: str):
    """
    临时客户转正（预计划执行完成时调用）。

    请求体：
        {
            "oper_cd": "操作员"
        }

    参数：
        cust_cd: 客户代码

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    oper_cd = data.get("oper_cd", "").strip()

    if not oper_cd:
        return error_response(message="缺少参数 oper_cd", code=400)

    success = _service.promote_to_active(cust_cd, oper_cd)
    if not success:
        return error_response(message="客户状态流转失败，可能状态不符", code=400)

    return success_response(data={"cust_cd": cust_cd, "new_status": "ACTIVE"}, message="客户已转正")


@customer_bp.post("/customers/<cust_cd>/invalidate")
def invalidate_customer(cust_cd: str):
    """
    标记客户为无效（预计划取消时调用）。

    请求体：
        {
            "oper_cd": "操作员"
        }

    参数：
        cust_cd: 客户代码

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    oper_cd = data.get("oper_cd", "").strip()

    if not oper_cd:
        return error_response(message="缺少参数 oper_cd", code=400)

    success = _service.mark_invalid(cust_cd, oper_cd)
    if not success:
        return error_response(message="客户状态更新失败", code=400)

    return success_response(data={"cust_cd": cust_cd, "new_status": "INVALID"}, message="客户已标记为无效")


@customer_bp.put("/customers/<cust_cd>")
def update_customer(cust_cd: str):
    """
    更新客户信息。

    请求体：
        {
            "cust_info": {
                "cust_nm": "客户名称",
                "address": "地址",
                "phone_no": "电话",
                "contactor": "联系人"
            },
            "oper_cd": "操作员"
        }

    参数：
        cust_cd: 客户代码

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    cust_info = data.get("cust_info", {})
    oper_cd = data.get("oper_cd", "").strip()

    if not oper_cd:
        return error_response(message="缺少参数 oper_cd", code=400)

    success = _service.update_customer_info(cust_cd, cust_info, oper_cd)
    if not success:
        return error_response(message="客户信息更新失败", code=500)

    return success_response(data={"cust_cd": cust_cd}, message="客户信息更新成功")
