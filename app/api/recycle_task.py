"""
旧机回收任务 API。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 回收任务管理端点
    - 对应优化4：旧机回收任务独立化
"""

from __future__ import annotations

from flask import Blueprint, request

from app.services.recycle_task_service import (
    DispositionType,
    RecycleTaskService,
    TaskStatus,
)
from app.utils.response import error_response, success_response

__all__ = ["recycle_task_bp"]

recycle_task_bp = Blueprint("recycle_task", __name__)
_service = RecycleTaskService()




@recycle_task_bp.get("/recycle-tasks")
def list_tasks():
    """
    获取回收任务列表。

    查询参数：
        - cust_cd: 门店代码
        - plan_no: 预计划单号
        - task_status: 任务状态

    返回值：
        Response: 统一结构 JSON 响应
    """
    cust_cd = request.args.get("cust_cd")
    plan_no = request.args.get("plan_no")
    task_status = request.args.get("task_status")

    tasks = _service.get_task_list(cust_cd, plan_no, task_status)
    return success_response(data=tasks)


@recycle_task_bp.get("/recycle-tasks/<recycle_id>")
def get_task_detail(recycle_id: str):
    """
    获取回收任务详情。

    参数：
        recycle_id: 回收任务ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    task = _service.get_task_detail(recycle_id)
    if task is None:
        return error_response(message="回收任务不存在", code=404)

    return success_response(data=task)


@recycle_task_bp.post("/recycle-tasks/from-plan")
def create_from_plan():
    """
    从预计划创建回收任务。

    请求体：
        {
            "plan_no": "P001",
            "plan_type": "02",  // 01旧机翻新/02关门
            "cust_cd": "C0000001",
            "oper_cd": "U001"
        }

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    plan_no = data.get("plan_no", "").strip()
    plan_type = data.get("plan_type", "").strip()
    cust_cd = data.get("cust_cd", "").strip()
    oper_cd = data.get("oper_cd", "").strip()

    if not plan_no:
        return error_response(message="缺少参数 plan_no", code=400)
    if not plan_type:
        return error_response(message="缺少参数 plan_type", code=400)
    if not cust_cd:
        return error_response(message="缺少参数 cust_cd", code=400)
    if not oper_cd:
        return error_response(message="缺少参数 oper_cd", code=400)

    task = _service.create_from_plan(plan_no, plan_type, cust_cd, oper_cd)
    if task is None:
        return success_response(data={"plan_no": plan_no, "cust_cd": cust_cd}, message="门店无可回收资产，未创建回收任务")

    return success_response(data=task, message="回收任务创建成功")


@recycle_task_bp.post("/recycle-tasks/<recycle_id>/assign")
def assign_task(recycle_id: str):
    """
    分配回收任务。

    请求体：
        {
            "user_id": "U001"
        }

    参数：
        recycle_id: 回收任务ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    user_id = data.get("user_id", "").strip()

    if not user_id:
        return error_response(message="缺少参数 user_id", code=400)

    success = _service.assign_task(recycle_id, user_id)
    if not success:
        return error_response(message="任务分配失败，可能状态不符", code=400)

    return success_response(data={"recycle_id": recycle_id, "assigned_to": user_id}, message="任务已分配")


@recycle_task_bp.post("/recycle-tasks/<recycle_id>/start")
def start_recycle(recycle_id: str):
    """
    开始回收任务。

    参数：
        recycle_id: 回收任务ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    success = _service.start_recycle(recycle_id)
    if not success:
        return error_response(message="任务启动失败，可能状态不符", code=400)

    return success_response(data={"recycle_id": recycle_id, "task_status": TaskStatus.IN_PROGRESS.value}, message="回收任务已启动")


@recycle_task_bp.post("/recycle-tasks/<recycle_id>/complete")
def complete_recycle(recycle_id: str):
    """
    完成回收任务。

    请求体：
        {
            "actual_assets": ["E001", "E002"],
            "disposition": "01",  // 01翻新/02报废/03调拨
            "target_warehouse": "WH01"
        }

    参数：
        recycle_id: 回收任务ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    actual_assets = data.get("actual_assets", [])
    disposition = data.get("disposition", "").strip()
    target_warehouse = data.get("target_warehouse", "").strip()

    if not actual_assets:
        return error_response(message="缺少参数 actual_assets", code=400)
    if not disposition:
        return error_response(message="缺少参数 disposition", code=400)
    if not target_warehouse:
        return error_response(message="缺少参数 target_warehouse", code=400)

    try:
        disp = DispositionType(disposition)
    except ValueError:
        return error_response(message=f"无效的处置方式: {disposition}", code=400)

    success = _service.complete_recycle(
        recycle_id,
        actual_assets,
        disp,
        target_warehouse,
    )
    if not success:
        return error_response(message="任务完成处理失败", code=500)

    return success_response(data={
        "recycle_id": recycle_id,
        "actual_count": len(actual_assets),
        "disposition": disposition,
    }, message="回收任务已完成")


@recycle_task_bp.post("/recycle-tasks/<recycle_id>/cancel")
def cancel_task(recycle_id: str):
    """
    取消回收任务。

    请求体：
        {
            "reason": "取消原因"
        }

    参数：
        recycle_id: 回收任务ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    reason = data.get("reason", "").strip()

    if not reason:
        return error_response(message="缺少参数 reason", code=400)

    success = _service.cancel_task(recycle_id, reason)
    if not success:
        return error_response(message="任务取消失败，可能状态不符", code=400)

    return success_response(data={"recycle_id": recycle_id, "cancel_reason": reason}, message="回收任务已取消")


@recycle_task_bp.get("/recycle-stats")
def get_recycle_stats():
    """
    获取回收统计分析。

    查询参数：
        - start_date: 开始日期（YYYY-MM-DD）
        - end_date: 结束日期（YYYY-MM-DD）

    返回值：
        Response: 统一结构 JSON 响应
    """
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        return error_response(message="缺少参数 start_date 或 end_date", code=400)

    stats = _service.get_recycle_stats(start_date, end_date)
    return success_response(data=stats)
