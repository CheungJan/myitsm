# -*- coding: utf-8 -*-
"""
代码表 API。
文件说明：提供代码项列表、详情、保存与作废接口。
作者：Cascade
创建时间：2026-04-20

端点：
- GET /api/v1/code-tables
- GET /api/v1/code-tables/<codetyp>/<codecd>
- POST /api/v1/code-tables/save
- POST /api/v1/code-tables/<codetyp>/<codecd>/invalidate
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, g, request

from app.services.codetable_service import CodeTableService
from app.utils.response import error_response, success_response

codetable_bp = Blueprint("codetable", __name__)
service = CodeTableService()


@codetable_bp.route("/code-tables", methods=["GET"])
def list_codes() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询代码项列表。"""
    try:
        codetyp = str(request.args.get("codetyp") or "").strip()
        include_invalid = str(request.args.get("include_invalid", "0")).strip() in {
            "1",
            "true",
            "True",
        }
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))

        result = service.list_codes(
            codetyp=codetyp,
            include_invalid=include_invalid,
            page=page,
            page_size=page_size,
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@codetable_bp.route("/code-tables/<codetyp>/<codecd>", methods=["GET"])
def get_code(codetyp: str, codecd: str) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """查询代码项详情。"""
    try:
        result = service.get_code(codetyp=codetyp, codecd=codecd)
        if not result.get("success"):
            return error_response(message=result.get("error")), 404
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@codetable_bp.route("/code-tables/save", methods=["POST"])
def save_code() -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """保存代码项。"""
    try:
        data = request.get_json() or {}
        opercd = str(data.get("opercd") or getattr(g, "user_cd", "")).strip()

        result = service.save_code(
            codetyp=str(data.get("codetyp") or "").strip(),
            codecd=str(data.get("codecd") or "").strip(),
            codenm=str(data.get("codenm") or "").strip(),
            opercd=opercd,
            useflg=str(data.get("useflg", "1")).strip() or "1",
            memo=data.get("memo"),
        )
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500


@codetable_bp.route("/code-tables/<codetyp>/<codecd>/invalidate", methods=["POST"])
def invalidate_code(
    codetyp: str, codecd: str
) -> tuple[Dict[str, Any], int] | Dict[str, Any]:
    """作废代码项。"""
    try:
        opercd = str(
            (request.get_json() or {}).get("opercd") or getattr(g, "user_cd", "")
        ).strip()
        result = service.invalidate_code(codetyp=codetyp, codecd=codecd, opercd=opercd)
        if not result.get("success"):
            return error_response(message=result.get("error")), 400
        return success_response(data=result)
    except Exception as exc:
        return error_response(message=str(exc)), 500
