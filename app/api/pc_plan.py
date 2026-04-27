# -*- coding: utf-8 -*-
"""
采购计划 API。
文件说明：提供采购计划相关接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/pc-plans
- GET /api/v1/pc-plans/<pcplanid>
- POST /api/v1/pc-plans
- PUT /api/v1/pc-plans/<pcplanid>
- DELETE /api/v1/pc-plans/<pcplanid>
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.pc_plan_service import PcPlanService
from app.utils.response import error_response, success_response

pc_plan_bp = Blueprint("pc_plan", __name__)
service = PcPlanService()


@pc_plan_bp.route("/pc-plans", methods=["GET"])
def list_pc_plans() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询采购计划列表。"""
    try:
        result = service.list_pc_plans(
            pcplanid=request.args.get("pcplanid"),
            slbillid=request.args.get("slbillid"),
            pctyp=request.args.get("pctyp"),
            auditflg=request.args.get("auditflg"),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 20)),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@pc_plan_bp.route("/pc-plans/<pcplanid>", methods=["GET"])
def get_pc_plan(pcplanid: str) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询采购计划详情。"""
    try:
        result = service.get_pc_plan(pcplanid=pcplanid)
        if not result.get("success"):
            return error_response(message=result.get("error")), 404
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@pc_plan_bp.route("/pc-plans", methods=["POST"])
def create_pc_plan() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """创建采购计划。"""
    try:
        data = request.get_json() or {}
        required = ["pcplanid", "slbillid", "pctyp", "ptimes"]
        for field in required:
            if field not in data:
                return error_response(message=f"Missing required field: {field}"), 400

        opercd = str(data.get("opercd") or getattr(g, "user_cd", "")).strip()
        if not opercd:
            return error_response(message="opercd is required"), 400

        result = service.create_pc_plan(
            pcplanid=str(data.get("pcplanid")).strip(),
            slbillid=str(data.get("slbillid")).strip(),
            pctyp=str(data.get("pctyp")).strip(),
            ptimes=int(data.get("ptimes")),
            opercd=opercd,
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@pc_plan_bp.route("/pc-plans/<pcplanid>", methods=["PUT"])
def update_pc_plan(pcplanid: str) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """更新采购计划。"""
    try:
        data = request.get_json() or {}
        result = service.update_pc_plan(
            pcplanid=pcplanid,
            pctyp=data.get("pctyp"),
            ptimes=data.get("ptimes"),
            auditflg=data.get("auditflg"),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@pc_plan_bp.route("/pc-plans/<pcplanid>", methods=["DELETE"])
def delete_pc_plan(pcplanid: str) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """删除采购计划。"""
    try:
        result = service.delete_pc_plan(pcplanid=pcplanid)
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
