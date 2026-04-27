# -*- coding: utf-8 -*-
"""
保养计划 API。
文件说明：提供 TIT17_MAINTENANCE_PLAN 列表、详情、新增、修改、删除、按年生成接口。
作者：Cascade
创建时间：2026-04-20

端点列表：
- GET /api/v1/maintenance-plans
- GET /api/v1/maintenance-plans/<plan_yymm>/<area_id>
- POST /api/v1/maintenance-plans
- PUT /api/v1/maintenance-plans/<plan_yymm>/<area_id>
- DELETE /api/v1/maintenance-plans/<plan_yymm>/<area_id>
- POST /api/v1/maintenance-plans/generate-year
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.maintenance_plan_service import MaintenancePlanService
from app.utils.response import error_response, success_response

maintenance_plan_bp = Blueprint("maintenance_plan", __name__)
service = MaintenancePlanService()


@maintenance_plan_bp.route("/maintenance-plans", methods=["GET"])
def list_maintenance_plans() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询保养计划列表。"""
    try:
        result = service.list_plans(
            plan_yymm=request.args.get("plan_yymm"),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 200)),
        )
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@maintenance_plan_bp.route(
    "/maintenance-plans/<plan_yymm>/<int:area_id>", methods=["GET"]
)
def get_maintenance_plan(
    plan_yymm: str, area_id: int
) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询保养计划详情。"""
    try:
        result = service.get_plan(plan_yymm=plan_yymm, area_id=area_id)
        if not result:
            return error_response(message="maintenance plan not found"), 404
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@maintenance_plan_bp.route("/maintenance-plans", methods=["POST"])
def create_maintenance_plan() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """新增保养计划。"""
    try:
        data = request.get_json() or {}
        required = ["plan_yymm", "area_id", "plan_qty"]
        for field in required:
            if field not in data:
                return make_response(
                    False, error=f"Missing required field: {field}"
                ), 400

        creator = str(data.get("creator") or getattr(g, "user_cd", "")).strip()
        if not creator:
            return error_response(message="creator is required"), 400

        try:
            area_id = int(data.get("area_id"))
            plan_qty = int(data.get("plan_qty"))
        except (TypeError, ValueError):
            return error_response(message="area_id/plan_qty must be integer"), 400

        result = service.create_plan(
            plan_yymm=str(data.get("plan_yymm")).strip(),
            area_id=area_id,
            plan_qty=plan_qty,
            creator=creator,
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result), 201
    except Exception as exc:
        return error_response(message=str(exc)), 500


@maintenance_plan_bp.route(
    "/maintenance-plans/<plan_yymm>/<int:area_id>", methods=["PUT"]
)
def update_maintenance_plan(
    plan_yymm: str, area_id: int
) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """修改保养计划数量。"""
    try:
        data = request.get_json() or {}
        if "plan_qty" not in data:
            return error_response(message="Missing required field: plan_qty"), 400

        try:
            plan_qty = int(data.get("plan_qty"))
        except (TypeError, ValueError):
            return error_response(message="plan_qty must be integer"), 400

        result = service.update_plan_qty(
            plan_yymm=plan_yymm, area_id=area_id, plan_qty=plan_qty
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@maintenance_plan_bp.route(
    "/maintenance-plans/<plan_yymm>/<int:area_id>", methods=["DELETE"]
)
def delete_maintenance_plan(
    plan_yymm: str, area_id: int
) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """删除保养计划。"""
    try:
        result = service.delete_plan(plan_yymm=plan_yymm, area_id=area_id)
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@maintenance_plan_bp.route("/maintenance-plans/generate-year", methods=["POST"])
def generate_maintenance_plan_year() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """按年生成保养计划。"""
    try:
        data = request.get_json() or {}
        plan_y = str(data.get("plan_y") or "").strip()
        if not plan_y:
            return error_response(message="plan_y is required"), 400

        creator = str(data.get("creator") or getattr(g, "user_cd", "")).strip()
        if not creator:
            return error_response(message="creator is required"), 400

        result = service.generate_year(plan_y=plan_y, creator=creator)
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
