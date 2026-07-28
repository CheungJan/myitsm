"""
库存预警与价格管理 API。

路由前缀：/api/v1/inventory
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.inventory import (
    AdjustPriceCreate,
    InventoryLimitCreate,
    InventoryLimitUpdate,
    PriceCreate,
    PriceUpdate,
)
from app.services.inventory_service import (
    AdjustPriceService,
    InventoryLimitService,
    PriceService,
)
from app.utils.response import error_response, success_response

__all__ = ["inventory_bp"]

inventory_bp = Blueprint("inventory", __name__)


# ---- 库存预警 ----


@inventory_bp.get("/inventory-limits")
@login_required
def list_limits():  # type: ignore[no-untyped-def]
    """库存预警列表。"""
    data = InventoryLimitService.list_all()
    return success_response(data=data)


@inventory_bp.get("/inventory-limits/<itemcd>")
@login_required
def get_limit(itemcd: str):  # type: ignore[no-untyped-def]
    """库存预警详情。"""
    data = InventoryLimitService.get(itemcd)
    if data is None:
        return error_response(message="预警规则不存在", code=404)
    return success_response(data=data)


@inventory_bp.post("/inventory-limits")
@login_required
def create_limit():  # type: ignore[no-untyped-def]
    """创建库存预警。"""
    body = InventoryLimitCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = InventoryLimitService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@inventory_bp.put("/inventory-limits/<itemcd>")
@login_required
def update_limit(itemcd: str):  # type: ignore[no-untyped-def]
    """更新库存预警。"""
    body = InventoryLimitUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = InventoryLimitService.update(itemcd, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="预警规则不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 价格规则 ----


@inventory_bp.get("/prices")
@login_required
def list_prices():  # type: ignore[no-untyped-def]
    """价格规则列表。"""
    data = PriceService.list_all()
    return success_response(data=data)


@inventory_bp.post("/prices")
@login_required
def create_price():  # type: ignore[no-untyped-def]
    """创建价格规则。"""
    body = PriceCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = PriceService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@inventory_bp.put("/prices/<itemcd>/<busityp>")
@login_required
def update_price(itemcd: str, busityp: str):  # type: ignore[no-untyped-def]
    """更新价格规则。"""
    body = PriceUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = PriceService.update(itemcd, busityp, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="价格规则不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 调价 ----


@inventory_bp.get("/adjust-prices")
@login_required
def list_all_adjust_prices():  # type: ignore[no-untyped-def]
    """调价记录列表（全部）。"""
    page: int = request.args.get("page", 1, type=int)
    per_page: int = request.args.get("per_page", 20, type=int)
    data = AdjustPriceService.list_all(page=page, per_page=per_page)
    return success_response(data=data)


@inventory_bp.get("/adjust-prices/<pabillid>")
@login_required
def get_adjust_price_detail(pabillid: str):  # type: ignore[no-untyped-def]
    """调价记录详情。"""
    data = AdjustPriceService.list_by_bill(pabillid)
    return success_response(data=data)


@inventory_bp.post("/adjust-prices")
@login_required
def create_adjust_price():  # type: ignore[no-untyped-def]
    """创建调价记录。"""
    body = AdjustPriceCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = AdjustPriceService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


# ---- 标签管理 (TMM40_LABEL) ----


@inventory_bp.get("/labels")
@login_required
def list_labels():  # type: ignore[no-untyped-def]
    """标签列表，支持 classcd / useflg / labelid 过滤。"""
    from app.extensions import db as _db
    from app.models.inventory import Label
    page: int = request.args.get("page", 1, type=int)
    per_page: int = request.args.get("per_page", 20, type=int)
    classcd: str | None = request.args.get("classcd") or None
    useflg: str | None = request.args.get("useflg") or None
    labelid: str | None = request.args.get("labelid") or None
    query = _db.session.query(Label)
    if classcd:
        query = query.filter(Label.classcd == classcd)
    if useflg is not None:
        query = query.filter(Label.useflg == useflg)
    if labelid:
        query = query.filter(Label.labelid.ilike(f"%{labelid}%"))
    query = query.order_by(Label.gendate.desc(), Label.labelid)
    total: int = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return success_response(data={
        "items": [{"labelid": i.labelid, "classcd": i.classcd, "opercd": i.opercd,
                    "gendate": str(i.gendate) if i.gendate else None,
                    "useflg": i.useflg} for i in items],
        "total": total, "page": page, "per_page": per_page
    })


@inventory_bp.post("/labels/bulk")
@login_required
def bulk_create_labels():  # type: ignore[no-untyped-def]
    """批量录入标签到 TMM40_LABEL（跳过已存在）。

    Body: {"rows": [{"labelid": "...", "classcd": "..."}, ...]}
    """
    from datetime import datetime
    from app.extensions import db as _db
    from app.models.inventory import Label
    body = request.get_json(silent=True) or {}
    rows = body.get("rows") or []
    if not rows:
        return error_response("rows 不能为空", 400)
    operator: str = g.current_user
    now = datetime.now()
    inserted = 0
    for row in rows:
        lid = (row.get("labelid") or "").strip()
        ccd = (row.get("classcd") or "").strip()
        if not lid or not ccd:
            continue
        existing = _db.session.get(Label, (lid, ccd))
        if existing:
            continue
        _db.session.add(Label(labelid=lid, classcd=ccd, opercd=operator, gendate=now, upddate=now, useflg="1"))
        inserted += 1
    _db.session.commit()
    return success_response(data={"inserted": inserted, "total": len(rows)}, message=f"录入 {inserted} 条")


@inventory_bp.post("/labels/generate")
@login_required
def generate_labels():  # type: ignore[no-untyped-def]
    """批量生成标签（PB规则：classcd+YY+月后缀+序号 或 YYYYMMDD+sign+序号）。

    Body:
      classcd - 中类编码(6位), typflg - '0'耗材/'1'固定资产,
      count - 生成数量, date - 日期(默认今天), sign - 标识(typflg=1时使用)
    """
    from datetime import datetime as _dt
    from app.extensions import db as _db
    body = request.get_json(silent=True) or {}
    classcd: str = (body.get("classcd") or "").strip()
    typflg: str = (body.get("typflg") or "1").strip()
    count: int = max(1, min(int(body.get("count") or 1), 10000))
    date_str: str = (body.get("date") or "").strip()
    sign: str = (body.get("sign") or "").strip()

    if not classcd or len(classcd) < 2:
        return error_response("classcd 格式无效", 400)

    dt = _dt.strptime(date_str[:10], "%Y-%m-%d") if date_str else _dt.now()
    now = _dt.now()
    operator: str = g.current_user
    from app.models.inventory import Label

    # PB生成规则
    if typflg == "0":
        yy = dt.strftime("%y")
        m = dt.month
        month_suffix = {12: 'C', 11: 'B', 10: 'A'}.get(m, str(m))
        # classcd 不足6位补零（如 BS42→BS4200, SU01→SU0100）
        padded_cd = classcd.ljust(6, '0')
        prefix = f"{padded_cd}{yy}{month_suffix}"
    else:
        prefix = f"{dt.strftime('%Y%m%d')}{sign}"

    # 查已有最大序号
    last_label = _db.session.query(Label.labelid).filter(
        Label.labelid.like(f"{prefix}%"), Label.classcd == classcd
    ).order_by(Label.labelid.desc()).first()
    start_seq = 1
    if last_label and last_label.labelid:
        try:
            start_seq = int(last_label.labelid[len(prefix):]) + 1
        except ValueError:
            start_seq = 1

    inserted = 0
    for i in range(count):
        labelid = f"{prefix}{start_seq + i:04d}"
        existing = _db.session.get(Label, (labelid, classcd))
        if not existing:
            _db.session.add(Label(labelid=labelid, classcd=classcd, opercd=operator, gendate=now, upddate=now, useflg="1"))
            inserted += 1

    _db.session.commit()
    return success_response(data={
        "prefix": prefix, "start_seq": start_seq, "inserted": inserted, "count": count,
    }, message=f"生成 {inserted} 条标签")


@inventory_bp.post("/labels/activate")
@login_required
def activate_label():  # type: ignore[no-untyped-def]
    """激活单条标签：TMM40_LABEL.useflg='0' + 在 TMM43_EID 建立记录。

    Body:
      labelid  - 标签号
      classcd  - 物料中类
      itemcd   - 物料编码（绑定到哪个物料）
      whcd     - 仓库（可选）
      qcflg    - 质检标志，默认 GA（合格/成品）；配件传 DJ（待检）
      prddate  - 生产日期（可选，YYYY-MM-DD）
    """
    from datetime import datetime
    from app.extensions import db as _db
    from app.models.inventory import Label
    from app.models.master import Eid
    body = request.get_json(silent=True) or {}
    labelid = (body.get("labelid") or "").strip()
    classcd = (body.get("classcd") or "").strip()
    itemcd = (body.get("itemcd") or "").strip()
    whcd = (body.get("whcd") or "").strip()
    qcflg = (body.get("qcflg") or "GA").strip()
    prddate_str: str | None = body.get("prddate")
    if not labelid or not classcd or not itemcd:
        return error_response("labelid / classcd / itemcd 为必填", 400)
    label = _db.session.get(Label, (labelid, classcd))
    if label is None:
        return error_response(f"标签 {labelid} 不存在", 404)
    if label.useflg == "0":
        return error_response(f"标签 {labelid} 已激活", 409)
    operator: str = g.current_user
    now = datetime.now()
    # 1. 标记已激活
    label.useflg = "0"
    label.upddate = now
    # 2. 建立 EID 记录（若已存在则跳过）
    existing_eid = _db.session.get(Eid, (itemcd, labelid))
    if existing_eid is None:
        prd_dt = None
        if prddate_str:
            try:
                prd_dt = datetime.strptime(prddate_str[:10], "%Y-%m-%d")
            except ValueError:
                pass
        sflg = "1" if qcflg == "GA" else "3"   # GA=合格在库, DJ=待检
        new_eid = Eid(
            itemcd=itemcd,
            eid=labelid,
            opercd=operator,
            gendate=now,
            useflg="1",
            sflg=sflg,
            qcflg=qcflg,
            whcd=whcd or None,
            prddate=prd_dt,
            etyp="1",
            asset_type="01",
            itemtyp=qcflg,
        )
        _db.session.add(new_eid)
    _db.session.commit()
    return success_response(data={"labelid": labelid, "itemcd": itemcd, "qcflg": qcflg}, message="激活成功")


@inventory_bp.post("/labels/batch-activate")
@login_required
def batch_activate_labels():  # type: ignore[no-untyped-def]
    """批量激活标签。

    Body:
      qcflg  - 批次默认质检标志（GA/DJ），可被单条覆盖
      labels - [{"labelid","classcd","itemcd","whcd","prddate","qcflg(可选)"}]
    """
    from datetime import datetime
    from app.extensions import db as _db
    from app.models.inventory import Label
    from app.models.master import Eid
    body = request.get_json(silent=True) or {}
    labels = body.get("labels") or []
    default_qcflg: str = (body.get("qcflg") or "GA").strip()
    if not labels:
        return error_response("labels 不能为空", 400)
    operator: str = g.current_user
    now = datetime.now()
    success_list, failed_list = [], []
    for row in labels:
        lid = (row.get("labelid") or "").strip()
        ccd = (row.get("classcd") or "").strip()
        icd = (row.get("itemcd") or "").strip()
        if not lid or not ccd or not icd:
            failed_list.append({"labelid": lid, "reason": "缺少必填字段"})
            continue
        label = _db.session.get(Label, (lid, ccd))
        if label is None:
            failed_list.append({"labelid": lid, "reason": "标签不存在"})
            continue
        if label.useflg == "0":
            failed_list.append({"labelid": lid, "reason": "已激活"})
            continue
        qcflg = (row.get("qcflg") or default_qcflg).strip()
        whcd = (row.get("whcd") or "").strip()
        prd_dt = None
        if row.get("prddate"):
            try:
                prd_dt = datetime.strptime(str(row["prddate"])[:10], "%Y-%m-%d")
            except ValueError:
                pass
        label.useflg = "0"
        label.upddate = now
        existing_eid = _db.session.get(Eid, (icd, lid))
        if existing_eid is None:
            sflg = "1" if qcflg == "GA" else "3"
            _db.session.add(Eid(
                itemcd=icd, eid=lid, opercd=operator, gendate=now,
                useflg="1", sflg=sflg, qcflg=qcflg,
                whcd=whcd or None, prddate=prd_dt, etyp="1", asset_type="01",
                itemtyp=qcflg,
            ))
        success_list.append(lid)
    _db.session.commit()
    return success_response(data={"success": len(success_list), "failed": len(failed_list), "errors": failed_list})


@inventory_bp.get("/labels/available")
@login_required
def list_available_labels():  # type: ignore[no-untyped-def]
    """预览指定 classcd 的可用（未激活）标签。

    Query: classcd=xxx&qty=10
    """
    from app.extensions import db as _db
    from app.models.inventory import Label
    classcd: str | None = request.args.get("classcd") or None
    qty: int = request.args.get("qty", 10, type=int)
    if not classcd:
        return error_response("classcd 为必填", 400)
    items = (
        _db.session.query(Label)
        .filter(Label.classcd == classcd, Label.useflg == "1")
        .order_by(Label.labelid)
        .limit(qty)
        .all()
    )
    return success_response(data=[{"labelid": i.labelid, "classcd": i.classcd} for i in items])
