"""
预计划管理 API。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 实现与M006客户/资产联动
    - 对应 sale.pbl 的预计划管理功能
"""

from __future__ import annotations

from flask import Blueprint, request

from app.services.preplan_service import PreplanService
from app.utils.response import error_response, success_response

__all__ = ["preplan_bp"]

preplan_bp = Blueprint("preplan", __name__)
_service = PreplanService()




@preplan_bp.get("/preplans")
def list_preplans():
    """获取预计划列表。"""
    plan_status = request.args.get("plan_status")
    imple_status = request.args.get("imple_status")
    cust_cd = request.args.get("cust_cd")

    preplans = _service.list_preplans(plan_status, imple_status, cust_cd)
    return success_response(data=preplans)


@preplan_bp.get("/preplans/<plan_no>")
def get_preplan(plan_no: str):
    """获取预计划详情。"""
    preplan = _service.get_preplan_detail(plan_no)
    if preplan is None:
        return error_response(message="预计划不存在", code=404)

    return success_response(data=preplan)


@preplan_bp.post("/preplans/<plan_no>/submit")
def submit_preplan(plan_no: str):
    """提交预计划（审批通过，触发客户/资产联动）。"""
    data = request.get_json() or {}
    oper_cd = data.get("oper_cd", "").strip()

    if not oper_cd:
        return error_response(message="缺少参数 oper_cd", code=400)

    result = _service.submit_preplan(plan_no, oper_cd)
    if not result.get("success"):
        return error_response(message=result.get("message", "提交失败"), code=500, data={"errors": result.get("errors", [])})

    return success_response(data=result, message=result.get("message"))


@preplan_bp.post("/preplans/<plan_no>/complete")
def complete_implementation(plan_no: str):
    """完成实施（临时客户转正）。"""
    data = request.get_json() or {}
    oper_cd = data.get("oper_cd", "").strip()

    if not oper_cd:
        return error_response(message="缺少参数 oper_cd", code=400)

    result = _service.complete_implementation(plan_no, oper_cd)
    if not result.get("success"):
        return error_response(message=result.get("message"), code=400)

    return success_response(data=result, message=result.get("message"))


@preplan_bp.post("/preplans/<plan_no>/cancel")
def cancel_preplan(plan_no: str):
    """取消预计划（标记客户无效）。"""
    data = request.get_json() or {}
    reason = data.get("reason", "").strip()
    oper_cd = data.get("oper_cd", "").strip()

    if not reason:
        return error_response(message="缺少参数 reason", code=400)
    if not oper_cd:
        return error_response(message="缺少参数 oper_cd", code=400)

    result = _service.cancel_preplan(plan_no, reason, oper_cd)
    if not result.get("success"):
        return error_response(message=result.get("message"), code=400)

    return success_response(data=result, message=result.get("message"))
