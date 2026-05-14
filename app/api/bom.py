"""BOM 管理 API 蓝图。"""

from __future__ import annotations

from typing import Any

from flask import Blueprint, request

from app.api.auth import login_required
from app.schemas.bom import BomCreateRequest, BomDtCreateRequest, BomDtUpdateRequest, BomUpdateRequest
from app.services.bom_service import BomService
from app.utils.response import error_response, success_response

bom_bp = Blueprint("bom", __name__)


@bom_bp.get("/check")
@login_required
def check_bom_status():  # type: ignore[no-untyped-def]
    """批量查询 BOM 状态（items=xxx,yyy → {itemcd: {useflg,bomnm,opercd,updated}}）。"""
    items = request.args.get("items", "")
    if not items:
        return success_response(data={})
    itemcds = [i.strip().upper() for i in items.split(",") if i.strip()]
    from app.extensions import db
    from app.models.master import Bom
    rows = db.session.query(Bom.bomcd, Bom.useflg, Bom.bomnm, Bom.opercd, Bom.upddate).filter(Bom.bomcd.in_(itemcds)).all()
    # 批量查操作员名称
    opercds = list({r[3].strip() for r in rows if r[3]})
    user_map: dict[str, str] = {}
    if opercds:
        users = db.session.execute(db.text("SELECT user_cd, user_nm FROM tmc13_users WHERE user_cd = ANY(:cds)"), {"cds": opercds}).fetchall()
        user_map = {u[0]: u[1] for u in users}
    result: dict[str, Any] = {}
    for r in rows:
        oper_raw = (r[3] or "").strip()
        result[r[0]] = {"useflg": r[1], "bomnm": r[2], "opercd": user_map.get(oper_raw, oper_raw), "upddate": str(r[4])[:10] if r[4] else ""}
    for cd in itemcds:
        if cd not in result:
            result[cd] = None
    return success_response(data=result)


@bom_bp.get("")
@login_required
def list_boms():  # type: ignore[no-untyped-def]
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search")
    class_cd = request.args.get("class_cd")
    return success_response(data=BomService.list_boms(page=page, per_page=per_page, search=search, class_cd=class_cd))


@bom_bp.post("")
@login_required
def create_bom():  # type: ignore[no-untyped-def]
    body = request.get_json(silent=True) or {}
    try:
        req = BomCreateRequest(**body)
    except Exception as e:
        return error_response(str(e), 400)
    return success_response(data=BomService.create_bom(req.model_dump()), code=201)


@bom_bp.get("/<bomcd>")
@login_required
def get_bom(bomcd: str):  # type: ignore[no-untyped-def]
    data = BomService.get_bom(bomcd)
    if data is None:
        return success_response(data=None, message="BOM不存在")
    return success_response(data=data)


@bom_bp.put("/<bomcd>")
@login_required
def update_bom(bomcd: str):  # type: ignore[no-untyped-def]
    body = request.get_json(silent=True) or {}
    try:
        req = BomUpdateRequest(**body)
    except Exception as e:
        return error_response(str(e), 400)
    data = req.model_dump(exclude_none=True)
    if not data:
        return error_response("无更新字段", 400)
    result = BomService.update_bom(bomcd, data)
    if result is None:
        return error_response("BOM不存在", 404)
    return success_response(data=result)


@bom_bp.delete("/<bomcd>")
@login_required
def delete_bom(bomcd: str):  # type: ignore[no-untyped-def]
    if not BomService.delete_bom(bomcd):
        return error_response("BOM不存在", 404)
    return success_response(message="已删除")


@bom_bp.post("/<bomcd>/details")
@login_required
def add_detail(bomcd: str):  # type: ignore[no-untyped-def]
    if BomService.get_bom(bomcd) is None:
        return error_response("BOM不存在", 404)
    body = request.get_json(silent=True) or {}
    try:
        req = BomDtCreateRequest(**body)
    except Exception as e:
        return error_response(str(e), 400)
    return success_response(data=BomService.add_detail(bomcd, req.model_dump()), code=201)


@bom_bp.put("/<bomcd>/details/<itemcd>")
@login_required
def update_detail(bomcd: str, itemcd: str):  # type: ignore[no-untyped-def]
    body = request.get_json(silent=True) or {}
    try:
        req = BomDtUpdateRequest(**body)
    except Exception as e:
        return error_response(str(e), 400)
    data = req.model_dump(exclude_none=True)
    if not data:
        return error_response("无更新字段", 400)
    result = BomService.update_detail(bomcd, itemcd, data)
    if result is None:
        return error_response("明细不存在", 404)
    return success_response(data=result)


@bom_bp.delete("/<bomcd>/details/<itemcd>")
@login_required
def delete_detail(bomcd: str, itemcd: str):  # type: ignore[no-untyped-def]
    if not BomService.delete_detail(bomcd, itemcd):
        return error_response("明细不存在", 404)
    return success_response(message="已删除")
