# -*- coding: utf-8 -*-
"""
资产作废审核 API。
文件说明：提供待审核作废单列表、明细、审批、作废接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/asset-audits
- GET /api/v1/asset-audits/<opbillid>/details
- POST /api/v1/asset-audits/approve
- POST /api/v1/asset-audits/invalidate
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.asset_audit_service import AssetAuditService
from app.utils.response import error_response, success_response

asset_audit_bp = Blueprint("asset_audit", __name__)
service = AssetAuditService()


@asset_audit_bp.route("/asset-audits", methods=["GET"])
def list_asset_audits() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询待审核作废单列表。"""
    try:
        result = service.list_pending_audits(
            opbillid=request.args.get("opbillid"),
            custcd=request.args.get("custcd"),
            custcard=request.args.get("custcard"),
            sltyp=request.args.get("sltyp"),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 20)),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@asset_audit_bp.route("/asset-audits/<opbillid>/details", methods=["GET"])
def list_asset_audit_details(
    opbillid: str,
) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询作废单明细。"""
    try:
        result = service.list_audit_details(
            opbillid=opbillid,
            custcd_like=str(request.args.get("custcd_like", "%")),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@asset_audit_bp.route("/asset-audits/approve", methods=["POST"])
def approve_asset_audit() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """审批作废单。"""
    try:
        data = request.get_json() or {}
        result = service.approve_audit(
            opbillid=str(data.get("opbillid") or "").strip(),
            custcd=str(data.get("custcd") or "").strip(),
            opercd=str(data.get("opercd") or getattr(g, "user_cd", "")).strip(),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@asset_audit_bp.route("/asset-audits/invalidate", methods=["POST"])
def invalidate_asset_audit() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """作废作废单。"""
    try:
        data = request.get_json() or {}
        result = service.invalidate_audit(
            opbillid=str(data.get("opbillid") or "").strip(),
            opercd=str(data.get("opercd") or getattr(g, "user_cd", "")).strip(),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
