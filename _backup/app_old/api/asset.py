"""
门店资产管理 API。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 资产查询与回收管理端点
    - 对应优化4：资产属性与回收任务
"""

from __future__ import annotations

from flask import Blueprint, request

from app.services.asset_service import AssetService, RecycleStatus
from app.utils.response import error_response, success_response

__all__ = ["asset_bp"]

asset_bp = Blueprint("asset", __name__)
_service = AssetService()




@asset_bp.get("/assets")
def list_assets():
    """
    获取门店资产列表。

    查询参数：
        - cust_cd: 门店代码
        - eid: 设备编码

    返回值：
        Response: 统一结构 JSON 响应
    """
    cust_cd = request.args.get("cust_cd")
    eid = request.args.get("eid")

    assets = _service.list_assets(cust_cd=cust_cd, eid=eid)
    return success_response(data=assets)


@asset_bp.get("/assets/recyclable/<cust_cd>")
def get_recyclable_assets(cust_cd: str):
    """
    获取门店可回收资产列表。

    参数：
        cust_cd: 门店代码

    返回值：
        Response: 统一结构 JSON 响应
    """
    assets = _service.get_recyclable_assets(cust_cd)
    return success_response(data={
        "cust_cd": cust_cd,
        "recyclable_count": len(assets),
        "assets": assets,
    })


@asset_bp.post("/assets/<cust_cd>/mark-recyclable")
def mark_recyclable(cust_cd: str):
    """
    标记门店可回收资产。

    请求体：
        {
            "plan_type": "02"  // 01旧机翻新/02关门
        }

    参数：
        cust_cd: 门店代码

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    plan_type = data.get("plan_type", "02")

    count = _service.mark_recyclable(cust_cd, plan_type)
    return success_response(data={
        "cust_cd": cust_cd,
        "marked_count": count,
        "plan_type": plan_type,
    }, message=f"已标记 {count} 个可回收资产")


@asset_bp.post("/assets/<cust_cd>/update-recycle-status")
def update_recycle_status(cust_cd: str):
    """
    更新资产回收状态。

    请求体：
        {
            "eid": "设备编码",
            "recycle_status": "COMPLETED"
        }

    参数：
        cust_cd: 门店代码

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    eid = data.get("eid", "").strip()
    recycle_status = data.get("recycle_status", "").strip()

    if not eid:
        return error_response(message="缺少参数 eid", code=400)
    if not recycle_status:
        return error_response(message="缺少参数 recycle_status", code=400)

    try:
        status = RecycleStatus(recycle_status)
    except ValueError:
        return error_response(message=f"无效的回收状态: {recycle_status}", code=400)

    success = _service.update_recycle_status(cust_cd, eid, status)
    if not success:
        return error_response(message="更新失败", code=500)

    return success_response(data={
        "cust_cd": cust_cd,
        "eid": eid,
        "recycle_status": recycle_status,
    }, message="状态更新成功")
