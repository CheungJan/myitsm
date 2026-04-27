# -*- coding: utf-8 -*-
"""
旧机翻新计划（ex_gh）API。
文件说明：提供 TSL01_EXTEND / TSL02_EXTENDDT 列表、详情、新增、明细新增、送审、作废接口。
作者：Cascade
创建时间：2026-04-20

端点列表：
- GET /api/v1/ex-ghs：旧机翻新计划列表
- GET /api/v1/ex-ghs/<opbillid>：旧机翻新计划详情（含明细）
- POST /api/v1/ex-ghs：新增旧机翻新计划主表
- POST /api/v1/ex-ghs/<opbillid>/details：新增旧机翻新计划明细
- POST /api/v1/ex-ghs/audit：批量送审
- POST /api/v1/ex-ghs/<opbillid>/invalidate：作废
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.ex_gh_service import ExGhService
from app.utils.response import error_response, success_response

ex_gh_bp = Blueprint("ex_gh", __name__)
service = ExGhService()


@ex_gh_bp.route("/ex-ghs", methods=["GET"])
def list_ex_ghs() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """获取旧机翻新计划列表。"""
    try:
        result = service.list_ex_ghs(
            begin_date=request.args.get("begin_date"),
            end_date=request.args.get("end_date"),
            custcd=request.args.get("custcd"),
            auditflg=request.args.get("auditflg"),
            useflg=request.args.get("useflg"),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 20)),
        )
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@ex_gh_bp.route("/ex-ghs/<opbillid>", methods=["GET"])
def get_ex_gh(opbillid: str) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """获取旧机翻新计划详情。"""
    try:
        result = service.get_ex_gh(opbillid)
        if not result:
            return error_response(message="ex_gh not found"), 404
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@ex_gh_bp.route("/ex-ghs", methods=["POST"])
def create_ex_gh() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """新增旧机翻新计划主表。"""
    try:
        data = request.get_json() or {}
        required = ["opbillid", "slbillid", "custcd"]
        for field in required:
            if not str(data.get(field) or "").strip():
                return error_response(
                    message=f"Missing required field: {field}"
                ), 400

        opercd = str(data.get("opercd") or getattr(g, "user_cd", "")).strip()
        if not opercd:
            return error_response(message="opercd is required"), 400

        result = service.create_ex_gh(
            opbillid=str(data.get("opbillid")).strip(),
            slbillid=str(data.get("slbillid")).strip(),
            custcd=str(data.get("custcd")).strip(),
            opercd=opercd,
            busityp=data.get("busityp"),
            itemcd=data.get("itemcd"),
            impdate=data.get("impdate"),
            traindate=data.get("traindate"),
            backup=data.get("backup"),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400

        return success_response(data=result), 201
    except Exception as exc:
        return error_response(message=str(exc)), 500


@ex_gh_bp.route("/ex-ghs/<opbillid>/details", methods=["POST"])
def create_ex_gh_detail(opbillid: str) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """新增旧机翻新计划明细。"""
    try:
        data = request.get_json() or {}
        custcd = str(data.get("custcd") or "").strip()
        if not custcd:
            return error_response(message="custcd is required"), 400

        try:
            planqty = int(data.get("planqty"))
        except (TypeError, ValueError):
            return error_response(message="planqty must be integer"), 400

        opercd = str(data.get("opercd") or getattr(g, "user_cd", "")).strip()
        if not opercd:
            return error_response(message="opercd is required"), 400

        result = service.create_ex_gh_detail(
            opbillid=opbillid,
            custcd=custcd,
            planqty=planqty,
            opercd=opercd,
            opqty=int(data.get("opqty", 0) or 0),
            clqty=int(data.get("clqty", 0) or 0),
            useflg=str(data.get("useflg", "0")).strip() or "0",
            impdate=data.get("impdate"),
            traindate=data.get("traindate"),
            newaddress=data.get("newaddress"),
            newcustcd=data.get("newcustcd"),
            eid=data.get("eid"),
            address=data.get("address"),
            newcustcard=data.get("newcustcard"),
            custcard=data.get("custcard"),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400

        return success_response(data=result), 201
    except Exception as exc:
        return error_response(message=str(exc)), 500


@ex_gh_bp.route("/ex-ghs/audit", methods=["POST"])
def submit_audit() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """批量送审。"""
    try:
        data = request.get_json() or {}
        opbillids = data.get("opbillids") or []
        if not isinstance(opbillids, list) or not opbillids:
            return error_response(
                message="opbillids is required and must be non-empty list"
            ), 400

        opercd = str(data.get("opercd") or getattr(g, "user_cd", "")).strip()
        if not opercd:
            return error_response(message="opercd is required"), 400

        result = service.submit_audit(opbillids=opbillids, opercd=opercd)
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@ex_gh_bp.route("/ex-ghs/<opbillid>/invalidate", methods=["POST"])
def invalidate_ex_gh(opbillid: str) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """作废旧机翻新计划。"""
    try:
        opercd = str(
            (request.get_json() or {}).get("opercd") or getattr(g, "user_cd", "")
        ).strip()
        if not opercd:
            return error_response(message="opercd is required"), 400

        result = service.invalidate_ex_gh(opbillid=opbillid, opercd=opercd)
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
