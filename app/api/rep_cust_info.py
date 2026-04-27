# -*- coding: utf-8 -*-
"""
客户信息报表 API。
文件说明：提供客户基本信息报表查询接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/rep-cust-info
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.rep_cust_info_service import RepCustInfoService
from app.utils.response import error_response, success_response

rep_cust_info_bp = Blueprint("rep_cust_info", __name__)
service = RepCustInfoService()


@rep_cust_info_bp.route("/rep-cust-info", methods=["GET"])
def list_rep_cust_info() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询客户信息报表。"""
    try:
        result = service.list_reports(
            custcard=request.args.get("custcard"),
            classcd=request.args.get("classcd"),
            custnm=request.args.get("custnm"),
            busityp=request.args.get("busityp"),
            useflg=request.args.get("useflg"),
            opendate_from=request.args.get("opendate_from"),
            opendate_to=request.args.get("opendate_to"),
            pptcode=request.args.get("pptcode"),
            zftype=request.args.get("zftype"),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 50)),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
