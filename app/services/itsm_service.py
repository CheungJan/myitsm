"""ITSM 核心业务服务层（状态机集成）。"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.extensions import db
from app.models.master import Area, CustPosRl, Customer, Eid, SysCode
from app.models.system import User
from app.repositories.itsm_repository import (
    AccessoriesUpdateRepository,
    CloseBillRepository,
    D2DRepository,
    DeviceChangeRepository,
    DispatchRepository,
    FreeReplaceRepository,
    LiabilityRegRepository,
    MaintenanceAttcRepository,
    MaintenanceDailyRepository,
    MaintenanceDailyTrackRepository,
    MaintenanceLiabilityRepository,
    MaintenanceOpenRepository,
    MaintenancePlanRepository,
    MaintenanceRenovateRepository,
    MaintenanceT17Repository,
    NoCloseTrackRepository,
    OnChooseDtRepository,
    PayListRepository,
    PosDetailRepository,
    RecycleTaskRepository,
    RepairInfoRepository,
    RVRepository,
    StoreCloseRepository,
    TimepointAreaRepository,
)
from app.services.state_machine import StateMachine

if TYPE_CHECKING:
    from app.models.itsm import DeviceChange, MaintenanceRenovate, RecycleTask, StoreClose

# ---------------------------------------------------------------------------
# 业务码值常量（避免硬编码散落各方法）
# ---------------------------------------------------------------------------

# CustPosRl.useflg：设备绑定有效标志
RL_USEFLG_ACTIVE = "1"
RL_USEFLG_INACTIVE = "0"

# CustPosRl.asset_status：资产状态
ASSET_STATUS_ACTIVE = "ACTIVE"
ASSET_STATUS_RETURNED = "RETURNED"

# PlanCust.plan_status：预计划状态
PLAN_STATUS_COMPLETED = "01"  # 计划完成
PLAN_STATUS_IN_PROGRESS = "04"  # 实施中

# EidTrack.type：业务语义层追踪类型
TRACK_TYPE_ALLOCATE = "C"  # 客户分配
TRACK_TYPE_RECYCLE = "R"  # 回收
TRACK_TYPE_TRANSFER = "T"  # 客户转移
TRACK_TYPE_ATTRIBUTE = "A"  # 属性变更

# tmm43_eid.asset_owner：资产归属
ASSET_OWNER_CUSTOMER = "01"  # 客户资产
# asset_owner 不等于 "01" 即为自有资产（02=公司等）

# ITSM 单据关单状态
CLOSE_STATUS = "5"

# 关单自动创建入库单的 sysparm 配置键（统一命名 stock_in_whcd_{invtyp}）
SYSPARM_STOCK_IN_WHCD_PREFIX = "stock_in_whcd_"
SYSPARM_SERVICE_RETURN_WHCD = "stock_in_whcd_3"  # 服务返还仓（IV=3）
SYSPARM_RECYCLE_RETURN_WHCD = "stock_in_whcd_7"  # 回收仓（IV=7）
SYSPARM_RENOVATE_RETURN_WHCD = "stock_in_whcd_7"  # 翻新返还仓（IV=7，与回收共用）


def _get_sysparm_whcd(parm_cd: str, default: str = "") -> str:
    """从 sysparm 读取仓库编码，未配置时返回 default。"""
    from app.models.system import SysParm

    sp = db.session.get(SysParm, parm_cd)
    return (sp.parm_val or default) if sp else default


def _create_stock_in_draft(
    invtyp: str,
    whcd: str,
    refbillid: str,
    memo: str,
    eid_items: list[dict[str, Any]],
    creator: str,
) -> str | None:
    """创建入库草稿（auditflg='0'）。

    Args:
        invtyp: 入库类型（3=服务返还, 7=回收入库）
        whcd: 仓库编码
        refbillid: 关联单据号（ITSM 单号）
        memo: 备注
        eid_items: [{"eid": ..., "itemcd": ...}, ...]
        creator: 操作人

    Returns:
        inbillid 或 None（无明细时）
    """
    if not eid_items or not whcd:
        return None

    from app.repositories.warehouse_repository import StockInRepository

    data = {
        "invtyp": invtyp,
        "whcd": whcd,
        "refbillid": refbillid,
        "memo": memo,
    }
    record = StockInRepository.create(data, creator)
    for idx, item in enumerate(eid_items, start=1):
        StockInRepository.add_detail(
            inbillid=record.inbillid,
            whcd=record.whcd,
            lineno=idx,
            data={
                "itemcd": item.get("itemcd") or "",
                "itemtyp": item.get("itemtyp") or "01",
                "inqty": 1,
                "eid": item.get("eid") or "",
            },
        )
    return record.inbillid


def _enrich_store_card(items: list[dict[str, Any]], key: str = "store_id") -> list[dict[str, Any]]:
    """为维护单记录补充 store_cust_card / area_cd / area_nm（从 tmm22_customers 关联查询）。"""
    ids = {r.get(key) for r in items if r.get(key)}
    if not ids:
        return items
    rows = (
        db.session.query(Customer.cust_cd, Customer.cust_card, Customer.area_cd, Area.area_nm)
        .outerjoin(Area, Area.area_cd == Customer.area_cd)
        .filter(Customer.cust_cd.in_(ids))
        .all()
    )
    cards: dict[str, str] = {}
    area_cds: dict[str, str] = {}
    area_nms: dict[str, str] = {}
    for cust_cd, cust_card, area_cd, area_nm in rows:
        cards[cust_cd] = cust_card or ""
        if area_cd:
            area_cds[cust_cd] = area_cd
            area_nms[cust_cd] = area_nm or ""
    for r in items:
        sid = r.get(key)
        if sid and sid in cards:
            r["store_cust_card"] = cards[sid]
            if sid in area_cds:
                r["area_cd"] = area_cds[sid]
                r["area_nm"] = area_nms[sid]
    return items


def _enrich_user_names(
    items: list[dict[str, Any]],
    fields: list[str],
) -> list[dict[str, Any]]:
    """为子表记录批量翻译人员编码→姓名（tmc13_users）。

    对 items 中每个 field 追加 field_nm 字段。
    """
    if not items or not fields:
        return items
    codes: set[str] = set()
    for r in items:
        for f in fields:
            v = str(r.get(f, "")).strip()
            if v:
                codes.add(v)
    if not codes:
        return items
    from app.models.system import User

    user_map = {
        u.user_cd: u.user_nm or u.user_cd
        for u in db.session.query(User).filter(User.user_cd.in_(codes)).all()
    }
    for r in items:
        for f in fields:
            v = str(r.get(f, "")).strip()
            if v and v in user_map:
                r[f"{f}_nm"] = user_map[v]
    return items


def _enrich_group_names(
    items: list[dict[str, Any]],
    field: str = "accpectd_group",
) -> list[dict[str, Any]]:
    """为子表记录翻译组编码→组名（tmc12_groups）。"""
    if not items:
        return items
    codes = {str(r.get(field, "")).strip() for r in items if r.get(field)}
    if not codes:
        return items
    from app.models.system import Group

    group_map = {
        g.group_cd: g.group_nm or g.group_cd
        for g in db.session.query(Group).filter(Group.group_cd.in_(codes)).all()
    }
    for r in items:
        v = str(r.get(field, "")).strip()
        if v and v in group_map:
            r[f"{field}_nm"] = group_map[v]
    return items


def _enrich_sys_codes(
    items: list[dict[str, Any]],
    field: str,
    code_typ: str,
) -> list[dict[str, Any]]:
    """为子表记录翻译系统字典代码→名称（tmm31_syscodes）。

    Args:
        items: 记录列表
        field: 待翻译的字段名
        code_typ: 字典类型（如 ZT=状态, GZ=故障类型, MY=满意度评价）

    Returns:
        补充 {field}_nm 字段后的记录列表
    """
    if not items:
        return items
    codes = {str(r.get(field, "")).strip() for r in items if r.get(field)}
    if not codes:
        return items
    code_map = dict(
        db.session.query(SysCode.code_cd, SysCode.code_nm)
        .filter(SysCode.code_typ == code_typ, SysCode.code_cd.in_(codes))
        .all()
    )
    for r in items:
        v = str(r.get(field, "")).strip()
        if v and v in code_map:
            r[f"{field}_nm"] = code_map[v]
    return items


def _enrich_notify_status(
    items: list[dict[str, Any]],
    ref_type: str,
) -> list[dict[str, Any]]:
    """为子表记录补充通知状态字段（重构 PB fxbz/ywfx）。

    PB 原 fxbz（飞信状态）= 已发/未发
    PB 原 ywfx（飞信数据）= 已产生/未产生

    重构后通过 TNTF02_NOTIFICATION 表查询：
    - notify_status: sent=已发, pending=未发, failed=失败, 无记录=未发
    - notify_data: Y=已产生通知数据, N=未产生

    Args:
        items: 记录列表
        ref_type: 通知关联业务类型（如 dispatch/maintenance）

    Returns:
        补充 notify_status / notify_data 字段后的记录列表
    """
    if not items:
        return items
    from app.models.notification import Notification

    # 按 maintenance_id 批量查询通知记录
    # 按 dispatch_id 精确匹配（同一工单多次派工各自独立追踪通知状态）
    dispatch_ids = {r.get("id") for r in items if r.get("id")}
    if not dispatch_ids:
        return items
    rows = (
        db.session.query(
            Notification.dispatch_id, Notification.send_status, Notification.read_status
        )
        .filter(Notification.ref_type == ref_type, Notification.dispatch_id.in_(dispatch_ids))
        .all()
    )
    status_order = {"sent": 3, "pending": 2, "failed": 1}
    notify_map: dict[int, dict[str, str]] = {}
    for did, send_st, read_st in rows:
        if did is None:
            continue
        prev = notify_map.get(did)
        if prev is None or status_order.get(send_st, 0) > status_order.get(prev.get("send", ""), 0):
            notify_map[did] = {"send": send_st or "", "read": read_st or "unread"}
    for r in items:
        did = r.get("id")
        if did and did in notify_map:
            info = notify_map[did]
            r["notify_status"] = info["send"]
            r["notify_data"] = "Y"
            r["notify_read"] = "Y" if info.get("read") == "read" else "N"
        else:
            r["notify_status"] = "N"
            r["notify_data"] = "N"
            r["notify_read"] = "N"
    return items


def _enrich_daily_refs(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """为日常维护单记录补充字典翻译字段（对齐 PB d_maintenanceday_one 显示）。

    补充字段：
    - fault_type_nm：故障类型名称（tmm31_syscodes code_typ='GZ'）
    - current_status_nm：当前状态名称（tmm31_syscodes code_typ='ZT'）
    - creator_nm / updator_nm / firstor_nm：人员姓名（tmc13_users.user_nm）
    """
    if not items:
        return items

    # 故障类型字典（GZ）
    fault_codes = {r.get("fault_type") for r in items if r.get("fault_type")}
    fault_map: dict[str, str] = {}
    if fault_codes:
        fault_map = dict(
            db.session.query(SysCode.code_cd, SysCode.code_nm)
            .filter(SysCode.code_typ == "GZ", SysCode.code_cd.in_(fault_codes))
            .all()
        )

    # 当前状态字典（ZT）
    status_codes = {r.get("current_status") for r in items if r.get("current_status")}
    status_map: dict[str, str] = {}
    if status_codes:
        status_map = dict(
            db.session.query(SysCode.code_cd, SysCode.code_nm)
            .filter(SysCode.code_typ == "ZT", SysCode.code_cd.in_(status_codes))
            .all()
        )

    # 人员编码 → 姓名（creator / updator / firstor）
    user_codes = {
        r.get(k) for r in items for k in ("creator", "updator", "firstor") if r.get(k)
    }
    user_map: dict[str, str] = {}
    if user_codes:
        user_map = dict(
            db.session.query(User.user_cd, User.user_nm)
            .filter(User.user_cd.in_(user_codes))
            .all()
        )

    for r in items:
        r["fault_type_nm"] = fault_map.get(r.get("fault_type") or "", "")
        r["current_status_nm"] = status_map.get(r.get("current_status") or "", "")
        r["creator_nm"] = user_map.get(r.get("creator") or "", "")
        r["updator_nm"] = user_map.get(r.get("updator") or "", "")
        r["firstor_nm"] = user_map.get(r.get("firstor") or "", "")
    return items


class _BaseMaintenanceService:
    """维护单服务基类，封装通用状态流转逻辑。"""

    @staticmethod
    def _do_transition(
        record: Any,
        to_status: str,
        operator: str,
        remark: str | None,
        *,
        track_fn: Any | None = None,
        pk_field: str = "maintenance_id",
    ) -> dict[str, object]:
        """执行状态流转。"""
        from_status: str = record.current_status or "1"
        result = StateMachine.validate_transition(from_status, to_status)
        if not result["valid"]:
            return {"success": False, "error": result.get("error", "状态流转验证失败")}

        record.current_status = to_status
        record.update_time = datetime.now(UTC)
        record.updator = operator

        if track_fn is not None:
            pk_value: str = getattr(record, pk_field)
            track_fn(
                maintenance_id=pk_value,
                from_status=from_status,
                to_status=to_status,
                oper_cd=operator,
                remark=remark,
            )

        return {
            "success": True,
            "from_status": from_status,
            "to_status": to_status,
        }


class MaintenanceDailyService(_BaseMaintenanceService):
    """日常维护单业务服务。"""

    @staticmethod
    def get(maintenance_id: str) -> dict[str, Any] | None:
        record = MaintenanceDailyRepository.get_by_id(maintenance_id)
        if record is None:
            return None
        enriched = _enrich_store_card([record.to_dict()])
        enriched = _enrich_daily_refs(enriched)
        return enriched[0]

    @staticmethod
    def list_records(
        status: str | None = None,
        store_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
        *,
        current_status: str | None = None,
        maintenance_id: str | None = None,
        company_id: str | None = None,
        area_cd: str | None = None,
        firstor: str | None = None,
        cust_card: str | None = None,
        cust_nm: str | None = None,
        address: str | None = None,
        fault_type: str | None = None,
        short_description: str | None = None,
        request_begin: str | None = None,
        request_end: str | None = None,
        first_begin: str | None = None,
        first_end: str | None = None,
        dispatch_to: str | None = None,
        area_user: str | None = None,
    ) -> dict[str, Any]:
        # 兼容前端 current_status 参数，与 status 合并
        effective_status = status or current_status
        items, total = MaintenanceDailyRepository.list_by_filters(
            status=effective_status,
            store_id=store_id,
            page=page,
            per_page=per_page,
            maintenance_id=maintenance_id,
            company_id=company_id,
            area_cd=area_cd,
            firstor=firstor,
            cust_card=cust_card,
            cust_nm=cust_nm,
            address=address,
            fault_type=fault_type,
            short_description=short_description,
            request_begin=request_begin,
            request_end=request_end,
            first_begin=first_begin,
            first_end=first_end,
            dispatch_to=dispatch_to,
            area_user=area_user,
        )
        enriched = _enrich_store_card([item.to_dict() for item in items])
        enriched = _enrich_daily_refs(enriched)
        return {
            "items": enriched,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = MaintenanceDailyRepository.create(data, creator)
        db.session.commit()
        # 自动派单：按规则引擎解析目标（故障类型 + 门店）
        store_id = record.store_id or data.get("store_id")
        if store_id:
            DispatchService.auto_create(
                record.maintenance_id, store_id, creator, record.fault_type
            )
        return record.to_dict()

    @staticmethod
    def update(maintenance_id: str, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        record = MaintenanceDailyRepository.get_by_id(maintenance_id)
        if record is None:
            return None
        MaintenanceDailyRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()

    def transition(
        self,
        maintenance_id: str,
        to_status: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        record = MaintenanceDailyRepository.get_by_id(maintenance_id)
        if record is None:
            return {"success": False, "error": "维护单不存在"}
        result = self._do_transition(
            record,
            to_status,
            operator,
            remark,
            track_fn=MaintenanceDailyRepository.add_track,
            pk_field="maintenance_id",
        )
        if result.get("success"):
            # 关单完成（to_status=5）：自动创建服务返还入库草稿（IV=3）
            if to_status == CLOSE_STATUS:
                self._create_service_return_inbound(record, operator)
            db.session.commit()
        return result

    @staticmethod
    def _create_service_return_inbound(record: Any, operator: str) -> None:
        """日常维护单关单时，为自有资产旧配件创建服务返还入库草稿（IV=3）。

        从 TIT25_ACCESSORIES_UPDATE 中取 old_accessories_id，过滤 asset_owner != '01'（自有资产），
        排除耗材（Item.consume='1'）和已标记不入库（in_wh='2'）的记录，
        按仓库配置 sysparm 'service_return_whcd' 创建入库草稿。
        """
        from app.models.itsm import AccessoriesUpdate
        from app.models.master import Eid as EidModel, Item

        # 查询本工单配件变更记录
        rows = (
            db.session.query(AccessoriesUpdate)
            .filter(
                AccessoriesUpdate.maintenance_id == record.maintenance_id,
                AccessoriesUpdate.old_accessories_id.isnot(None),
                AccessoriesUpdate.old_accessories_id != "",
                AccessoriesUpdate.in_wh.is_distinct_from("2"),  # 排除已标记不入库
            )
            .all()
        )
        if not rows:
            return

        eids = [r.old_accessories_id for r in rows if r.old_accessories_id]
        if not eids:
            return

        # 过滤自有资产（asset_owner != '01'）
        eid_rows = (
            db.session.query(EidModel)
            .filter(
                EidModel.eid.in_(eids),
                EidModel.asset_owner != ASSET_OWNER_CUSTOMER,
            )
            .all()
        )
        if not eid_rows:
            return

        # 排除耗材
        itemcds = {e.itemcd for e in eid_rows}
        consumable_items = {
            r[0]
            for r in db.session.query(Item.item_cd)
            .filter(Item.item_cd.in_(itemcds), Item.consume == "1")
            .all()
        }

        eid_items = [
            {"eid": e.eid, "itemcd": e.itemcd, "itemtyp": e.itemtyp or "01"}
            for e in eid_rows
            if e.itemcd not in consumable_items
        ]
        if not eid_items:
            return

        whcd = _get_sysparm_whcd(SYSPARM_SERVICE_RETURN_WHCD)
        if not whcd:
            return  # 未配置仓库，跳过自动创建

        _create_stock_in_draft(
            invtyp="3",
            whcd=whcd,
            refbillid=record.maintenance_id,
            memo=f"日常维护单 {record.maintenance_id} 关单自动创建服务返还入库",
            eid_items=eid_items,
            creator=operator,
        )


class MaintenanceOpenService(_BaseMaintenanceService):
    """新机开通单业务服务。"""

    @staticmethod
    def get(opening_id: str) -> dict[str, Any] | None:
        record = MaintenanceOpenRepository.get_by_id(opening_id)
        if record is None:
            return None
        data = record.to_dict()
        # 附带 equipments 子表（TIT14_EQUIPMENT_OPEN）
        data["equipments"] = [
            {
                "id": eq.id,
                "device_id": eq.device_id,
                "item_cd": None,  # EquipmentOpen 无 item_cd 字段，前端按 device_id 显示
                "price": float(eq.price) if eq.price is not None else None,
                "delivery_id": eq.delivery_id,
                "is_finish": eq.is_finish,
                "is_change": eq.is_change,
                "change_eid": eq.change_eid,
                "from_custcard": eq.from_custcard,
                "from_posid": eq.from_posid,
                "from_custcd": eq.from_custcd,
            }
            for eq in record.equipments
        ]
        return data

    @staticmethod
    def list_records(
        status: str | None = None,
        store_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = MaintenanceOpenRepository.list_by_filters(
            status=status, store_id=store_id, page=page, per_page=per_page
        )
        enriched = _enrich_store_card([item.to_dict() for item in items])
        return {
            "items": enriched,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = MaintenanceOpenRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(opening_id: str, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        record = MaintenanceOpenRepository.get_by_id(opening_id)
        if record is None:
            return None
        MaintenanceOpenRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()

    # ---- TIT14 设备明细 ----
    @staticmethod
    def add_equipment(opening_id: str, data: dict[str, Any], creator: str) -> dict[str, Any]:
        data["creator"] = creator
        eq = MaintenanceOpenRepository.add_equipment(opening_id, data)
        db.session.commit()
        return eq.to_dict()

    @staticmethod
    def delete_equipment(opening_id: str, eq_id: int) -> bool:
        ok = MaintenanceOpenRepository.delete_equipment(opening_id, eq_id)
        if ok:
            db.session.commit()
        return ok

    def transition(
        self,
        opening_id: str,
        to_status: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        record = MaintenanceOpenRepository.get_by_id(opening_id)
        if record is None:
            return {"success": False, "error": "开通单不存在"}
        result = self._do_transition(record, to_status, operator, remark, pk_field="new_opening_id")
        if result.get("success"):
            # 关单完成（to_status=5）：
            # 1. 写 tmm43_eid_track type='C'（设备分配到门店）
            # 2. 写 tmm35_cust_pos_rl（设备绑定到门店）
            # 3. 回写预计划 plan_status='01'（计划完成）
            if to_status == CLOSE_STATUS:
                self._write_eid_track_on_close(record, operator)
                self._link_equipment_to_store(record, operator)
                self._write_back_plan_status(record, operator)
            db.session.commit()
        return result

    @staticmethod
    def _write_eid_track_on_close(record: Any, operator: str) -> None:
        """开通单关单时写 tmm43_eid_track type='C' 记录。

        从主设备 device_id 和附表 equipments 取 EID 列表，
        对每个 EID 写一条 type='C' 记录，refid=预计划号（通过 imple_billid 反查）。
        """
        from datetime import UTC
        from datetime import datetime as _dt

        from app.models.master import Eid as EidModel
        from app.models.sales import PlanCust
        from app.repositories.system_repository import SystemRepository

        # 收集 EID 列表（主设备 + 附表）
        eids: list[str] = []
        if record.device_id:
            eids.append(record.device_id)
        for eq in record.equipments:
            if eq.device_id and eq.device_id not in eids:
                eids.append(eq.device_id)

        if not eids:
            return

        # 反查预计划号（imple_billid = new_opening_id）
        planno = (
            db.session.query(PlanCust.planno)
            .filter(PlanCust.imple_billid == record.new_opening_id)
            .scalar()
        ) or ""

        change_date = _dt.now(UTC)
        for eid in eids:
            eid_rec = db.session.query(EidModel).filter(EidModel.eid == eid).first()
            if eid_rec is None:
                continue
            SystemRepository.create_eid_track(
                eid=eid,
                itemcd=eid_rec.itemcd or "",
                track_type=TRACK_TYPE_ALLOCATE,
                operator=operator,
                refid=planno,
                change_date=change_date,
                cust_cd=None,
                n_cust_cd=record.store_id,
                sflg=eid_rec.sflg,
                n_sflg=eid_rec.sflg,
                whcd=eid_rec.whcd,
                n_whcd=eid_rec.whcd,
                install_date=None,
                n_install_date=change_date,
                remark=f"开通单 {record.new_opening_id} 关单，设备绑定到门店 {record.store_id}",
            )

    @staticmethod
    def _link_equipment_to_store(record: Any, operator: str) -> None:
        """开通单关单时写 tmm35_cust_pos_rl（设备绑定到门店）。

        对每个 EID 写一条 CustPosRl 记录，标记设备已分配到客户门店。
        若已存在同 eid + useflg='1' 的记录，更新 posupddate 而非重复插入。
        """
        from datetime import UTC
        from datetime import datetime as _dt

        from app.models.master import CustPosRl
        from app.models.master import Eid as EidModel

        eids: list[str] = []
        if record.device_id:
            eids.append(record.device_id)
        for eq in record.equipments:
            if eq.device_id and eq.device_id not in eids:
                eids.append(eq.device_id)

        if not eids or not record.store_id:
            return

        now = _dt.now(UTC)
        for eid in eids:
            eid_rec = db.session.query(EidModel).filter(EidModel.eid == eid).first()
            item_cd = eid_rec.itemcd if eid_rec else ""

            # 查是否已有活跃绑定
            existing = (
                db.session.query(CustPosRl)
                .filter(CustPosRl.eid == eid, CustPosRl.useflg == RL_USEFLG_ACTIVE)
                .first()
            )
            if existing:
                # 已绑定到其他门店：失效旧记录，写新记录
                if existing.cust_cd != record.store_id:
                    existing.useflg = RL_USEFLG_INACTIVE
                    existing.asset_status = ASSET_STATUS_RETURNED
                    db.session.add(
                        CustPosRl(
                            cust_cd=record.store_id,
                            eid=eid,
                            item_cd=item_cd,
                            useflg=RL_USEFLG_ACTIVE,
                            posupddate=now,
                            asset_status=ASSET_STATUS_ACTIVE,
                            created_from="MAINTENANCE_OPEN",
                            source_id=record.new_opening_id,
                        )
                    )
                else:
                    existing.posupddate = now
                    existing.asset_status = ASSET_STATUS_ACTIVE
            else:
                db.session.add(
                    CustPosRl(
                        cust_cd=record.store_id,
                        eid=eid,
                        item_cd=item_cd,
                        useflg=RL_USEFLG_ACTIVE,
                        posupddate=now,
                        asset_status=ASSET_STATUS_ACTIVE,
                        created_from="MAINTENANCE_OPEN",
                        source_id=record.new_opening_id,
                    )
                )

    @staticmethod
    def _write_back_plan_status(record: Any, operator: str) -> None:
        """开通单关单时回写预计划 plan_status='01'（计划完成）。

        对齐 PB"实施完成即计划完成"优化，消除人工配置确认环节。
        仅当预计划当前 plan_status='04'（实施中）时回写。
        """
        from app.models.sales import PlanCust

        plan = (
            db.session.query(PlanCust)
            .filter(PlanCust.imple_billid == record.new_opening_id)
            .first()
        )
        if plan is None:
            return
        if (plan.plan_status or "00") != PLAN_STATUS_IN_PROGRESS:
            return
        plan.plan_status = PLAN_STATUS_COMPLETED
        plan.update_time = datetime.now(UTC)
        plan.updator = operator


class MaintenanceRenovateService(_BaseMaintenanceService):
    """旧机翻新单业务服务。"""

    @staticmethod
    def get(renew_id: str) -> dict[str, Any] | None:
        record = MaintenanceRenovateRepository.get_by_id(renew_id)
        if record is None:
            return None
        enriched = _enrich_store_card([record.to_dict()])
        return enriched[0]

    @staticmethod
    def list_records(
        status: str | None = None,
        store_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = MaintenanceRenovateRepository.list_by_filters(
            status=status, store_id=store_id, page=page, per_page=per_page
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = MaintenanceRenovateRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(renew_id: str, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        record = MaintenanceRenovateRepository.get_by_id(renew_id)
        if record is None:
            return None
        MaintenanceRenovateRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()

    # ---- TIT15 设备明细 ----
    @staticmethod
    def list_equipments(renew_id: str) -> list[dict[str, Any]]:
        return [e.to_dict() for e in MaintenanceRenovateRepository.list_equipments(renew_id)]

    @staticmethod
    def add_equipment(renew_id: str, data: dict[str, Any], creator: str) -> dict[str, Any]:
        data["creator"] = creator
        eq = MaintenanceRenovateRepository.add_equipment(renew_id, data)
        db.session.commit()
        return eq.to_dict()

    @staticmethod
    def delete_equipment(renew_id: str, eq_id: int) -> bool:
        ok = MaintenanceRenovateRepository.delete_equipment(renew_id, eq_id)
        if ok:
            db.session.commit()
        return ok

    def transition(
        self,
        renew_id: str,
        to_status: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        record = MaintenanceRenovateRepository.get_by_id(renew_id)
        if record is None:
            return {"success": False, "error": "翻新单不存在"}
        result = self._do_transition(record, to_status, operator, remark, pk_field="renew_id")
        if result.get("success"):
            # 11c: 关单（to_status=5）时写 EidTrack + rl 转移 + 回写计划 + 自动创建回收入库草稿
            if to_status == CLOSE_STATUS:
                self._write_eid_track_on_close_renovate(record, operator)
                self._transfer_rl_on_close_renovate(record, operator)
                self._write_back_plan_status_renovate(record, operator)
                self._create_recycle_inbound_renovate(record, operator)
            db.session.commit()
        return result

    @staticmethod
    def _write_eid_track_on_close_renovate(record: MaintenanceRenovate, operator: str) -> None:
        """翻新单关单时写 tmm43_eid_track：旧机 type='R'（回收）+ 新机 type='C'（分配）。

        对齐 PB usp_plan_confrim L301-356, L403-405。
        refid=预计划号（通过 imple_billid 反查）。
        """
        from app.models.master import Eid as EidModel
        from app.models.sales import PlanCust
        from app.repositories.system_repository import SystemRepository

        planno = (
            db.session.query(PlanCust.planno)
            .filter(PlanCust.imple_billid == record.renew_id)
            .scalar()
        ) or ""

        change_date = datetime.now(UTC)

        # 旧机写 type='R'（回收）
        if record.old_device_id:
            eid_rec = (
                db.session.query(EidModel).filter(EidModel.eid == record.old_device_id).first()
            )
            if eid_rec:
                SystemRepository.create_eid_track(
                    eid=record.old_device_id,
                    itemcd=eid_rec.itemcd or "",
                    track_type=TRACK_TYPE_RECYCLE,
                    operator=operator,
                    refid=planno,
                    change_date=change_date,
                    cust_cd=record.store_id,
                    n_cust_cd=None,
                    sflg=eid_rec.sflg,
                    n_sflg=eid_rec.sflg,
                    whcd=eid_rec.whcd,
                    n_whcd=eid_rec.whcd,
                    install_date=eid_rec.install_date,
                    n_install_date=eid_rec.install_date,
                    remark=(
                        f"翻新单 {record.renew_id} 关单，旧机 "
                        f"{record.old_device_id} 从门店 {record.store_id} 回收"
                    ),
                )

        # 新机写 type='C'（分配）
        if record.new_device_id:
            eid_rec = (
                db.session.query(EidModel).filter(EidModel.eid == record.new_device_id).first()
            )
            if eid_rec:
                SystemRepository.create_eid_track(
                    eid=record.new_device_id,
                    itemcd=eid_rec.itemcd or "",
                    track_type=TRACK_TYPE_ALLOCATE,
                    operator=operator,
                    refid=planno,
                    change_date=change_date,
                    cust_cd=None,
                    n_cust_cd=record.store_id,
                    sflg=eid_rec.sflg,
                    n_sflg=eid_rec.sflg,
                    whcd=eid_rec.whcd,
                    n_whcd=eid_rec.whcd,
                    install_date=None,
                    n_install_date=change_date,
                    remark=(
                        f"翻新单 {record.renew_id} 关单，新机 "
                        f"{record.new_device_id} 分配到门店 {record.store_id}"
                    ),
                )

    @staticmethod
    def _transfer_rl_on_close_renovate(record: MaintenanceRenovate, operator: str) -> None:
        """翻新单关单时转移 tmm35_cust_pos_rl：旧机失效 + 新机新建。

        对齐 PB usp_plan_confrim L301-356, L403-405。
        """
        from app.models.master import CustPosRl
        from app.models.master import Eid as EidModel

        now = datetime.now(UTC)

        # 旧机 rl 失效
        if record.old_device_id:
            old_rl = (
                db.session.query(CustPosRl)
                .filter(
                    CustPosRl.eid == record.old_device_id,
                    CustPosRl.useflg == RL_USEFLG_ACTIVE,
                )
                .first()
            )
            if old_rl:
                old_rl.useflg = RL_USEFLG_INACTIVE
                old_rl.asset_status = ASSET_STATUS_RETURNED
                old_rl.posupddate = now
            # 旧机回库待核实：tmm43_eid.sflg='3'（待检），对齐 PB USP_PLAN_CONFRIM
            # 注：sflg='2' 是"已报废"，'3' 才是"待检/待核实"
            old_eid = (
                db.session.query(EidModel).filter(EidModel.eid == record.old_device_id).first()
            )
            if old_eid:
                old_eid.sflg = "3"

        # 新机 rl 新建或更新
        if record.new_device_id and record.store_id:
            new_rl = (
                db.session.query(CustPosRl)
                .filter(
                    CustPosRl.eid == record.new_device_id,
                    CustPosRl.cust_cd == record.store_id,
                    CustPosRl.useflg == RL_USEFLG_ACTIVE,
                )
                .first()
            )
            if new_rl:
                new_rl.posupddate = now
                new_rl.asset_status = ASSET_STATUS_ACTIVE
            else:
                eid_rec = (
                    db.session.query(EidModel).filter(EidModel.eid == record.new_device_id).first()
                )
                item_cd = eid_rec.itemcd if eid_rec else ""
                db.session.add(
                    CustPosRl(
                        cust_cd=record.store_id,
                        eid=record.new_device_id,
                        item_cd=item_cd,
                        useflg="1",
                        posupddate=now,
                        asset_status="ACTIVE",
                        created_from="MAINTENANCE_RENOVATE",
                        source_id=record.renew_id,
                    )
                )

    @staticmethod
    def _create_recycle_inbound_renovate(record: MaintenanceRenovate, operator: str) -> None:
        """翻新单关单时，为旧机创建回收入库草稿（IV=7）。

        按仓库配置 sysparm 'renovate_return_whcd' 创建入库草稿。
        仅当旧机 asset_owner != '01'（自有资产）时创建。
        """
        if not record.old_device_id:
            return

        from app.models.master import Eid as EidModel

        eid_rec = (
            db.session.query(EidModel).filter(EidModel.eid == record.old_device_id).first()
        )
        if not eid_rec or eid_rec.asset_owner == ASSET_OWNER_CUSTOMER:
            return  # 客户资产不回收

        whcd = _get_sysparm_whcd(SYSPARM_RENOVATE_RETURN_WHCD)
        if not whcd:
            return

        _create_stock_in_draft(
            invtyp="7",
            whcd=whcd,
            refbillid=record.renew_id,
            memo=f"翻新单 {record.renew_id} 关单自动创建回收入库",
            eid_items=[
                {
                    "eid": eid_rec.eid,
                    "itemcd": eid_rec.itemcd,
                    "itemtyp": eid_rec.itemtyp or "02",  # 旧机
                }
            ],
            creator=operator,
        )

    @staticmethod
    def _write_back_plan_status_renovate(record: MaintenanceRenovate, operator: str) -> None:
        """回写预计划 plan_status='01'（计划完成）。

        仅当预计划当前 plan_status='04'（实施中）时回写。
        """
        from app.models.sales import PlanCust

        plan = db.session.query(PlanCust).filter(PlanCust.imple_billid == record.renew_id).first()
        if plan is None:
            return
        if (plan.plan_status or "00") != PLAN_STATUS_IN_PROGRESS:
            return
        plan.plan_status = PLAN_STATUS_COMPLETED
        plan.update_time = datetime.now(UTC)
        plan.updator = operator


class DeviceChangeService(_BaseMaintenanceService):
    """磁卡号变更单业务服务（含P0-4磁卡号历史优化）。"""

    @staticmethod
    def get(change_id: str) -> dict[str, Any] | None:
        record = DeviceChangeRepository.get_by_id(change_id)
        if record is None:
            return None
        enriched = _enrich_store_card([record.to_dict()])
        return enriched[0]

    @staticmethod
    def list_records(
        status: str | None = None,
        store_id: str | None = None,
        change_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = DeviceChangeRepository.list_by_filters(
            status=status,
            store_id=store_id,
            change_type=change_type,
            page=page,
            per_page=per_page,
        )
        enriched = _enrich_store_card([item.to_dict() for item in items])
        return {
            "items": enriched,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = DeviceChangeRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(change_id: str, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        record = DeviceChangeRepository.get_by_id(change_id)
        if record is None:
            return None
        DeviceChangeRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()

    def transition(
        self,
        change_id: str,
        to_status: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        record = DeviceChangeRepository.get_by_id(change_id)
        if record is None:
            return {"success": False, "error": "变更单不存在"}

        result = self._do_transition(
            record, to_status, operator, remark, pk_field="device_change_id"
        )

        if result.get("success"):
            # CK/BG/BQ 三种变更类型都在审核完成（to_status=5）时同步客户表并写历史
            if to_status == CLOSE_STATUS and record.change_type in ("CK", "BG", "BQ"):
                self._sync_customer_and_history(record, operator, remark)

            # 11b: 设备转移按 device_id + new_store_id 判断（对齐 PB USP_PLAN_CONFRIM V_NEW_POSID）
            # 预计划入口 CHANGE_TYPE 始终为 CK，不能依赖 change_type=='BG' 触发设备转移
            if to_status == CLOSE_STATUS:
                if record.device_id and record.new_store_id:
                    self._write_eid_track_on_close_bg(record, operator)
                    self._transfer_rl_on_close_bg(record, operator)
                self._write_back_plan_status(record, operator)

            db.session.commit()

        return result

    @staticmethod
    def _write_eid_track_on_close_bg(record: DeviceChange, operator: str) -> None:
        """BG 子类型关单时写 tmm43_eid_track type='T'（客户转移）记录。

        设备从 A 客户（store_id）转移到 B 客户（new_store_id）。
        refid=预计划号（通过 imple_billid 反查）。
        """
        from app.models.master import Eid as EidModel
        from app.models.sales import PlanCust
        from app.repositories.system_repository import SystemRepository

        if not record.device_id:
            return

        planno = (
            db.session.query(PlanCust.planno)
            .filter(PlanCust.imple_billid == record.device_change_id)
            .scalar()
        ) or ""

        eid_rec = db.session.query(EidModel).filter(EidModel.eid == record.device_id).first()
        if eid_rec is None:
            return

        change_date = datetime.now(UTC)
        SystemRepository.create_eid_track(
            eid=record.device_id,
            itemcd=eid_rec.itemcd or "",
            track_type=TRACK_TYPE_TRANSFER,
            operator=operator,
            refid=planno,
            change_date=change_date,
            cust_cd=record.store_id,
            n_cust_cd=record.new_store_id,
            sflg=eid_rec.sflg,
            n_sflg=eid_rec.sflg,
            whcd=eid_rec.whcd,
            n_whcd=eid_rec.whcd,
            install_date=eid_rec.install_date,
            n_install_date=eid_rec.install_date,
            remark=(
                f"磁卡号变更单 {record.device_change_id} 关单，设备从 "
                f"{record.store_id} 转移到 {record.new_store_id}"
            ),
        )

    @staticmethod
    def _transfer_rl_on_close_bg(record: DeviceChange, operator: str) -> None:
        """设备转移关单时转移 tmm35_cust_pos_rl + 设备回库 + 目标客户合并。

        旧门店（store_id）rl 失效（useflg=0, asset_status=RETURNED, maintenancetyp='BG', maintenanceno=变更单号, maintenancedate=now）；
        新门店（new_store_id）rl 新建或更新（useflg=1, asset_status=ACTIVE, maintenancetyp='BG', maintenanceno=变更单号, maintenancedate=now）；
        设备回库（tmm43_eid.sflg='8'，对齐 PB USP_ASSET_C_A sltyp='BG' v_back='Y'）；
        目标客户合并（tmm22_customers.useflg='0'，对齐 PB USP_PLAN_CONFRIM）。
        对齐 PB usp_plan_confrim L221-243。
        """
        from app.models.master import CustPosRl
        from app.models.master import Customer as CustomerModel
        from app.models.master import Eid as EidModel

        if not record.device_id or not record.new_store_id:
            return

        now = datetime.now(UTC)
        maintenance_no = record.device_change_id or ""

        # 旧门店 rl 失效（对齐 PB: useflg='0', MAINTENANCETYP='BG', maintenanceno, maintenancedate）
        old_rl = (
            db.session.query(CustPosRl)
            .filter(
                CustPosRl.eid == record.device_id,
                CustPosRl.cust_cd == record.store_id,
                CustPosRl.useflg == RL_USEFLG_ACTIVE,
            )
            .first()
        )
        if old_rl:
            old_rl.useflg = RL_USEFLG_INACTIVE
            old_rl.asset_status = ASSET_STATUS_RETURNED
            old_rl.maintenancetyp = "BG"
            old_rl.maintenanceno = maintenance_no
            old_rl.maintenancedate = now
            old_rl.posupddate = now

        # 新门店 rl 新建或更新（对齐 PB: useflg='1', MAINTENANCETYP='BG', maintenanceno, maintenancedate）
        new_rl = (
            db.session.query(CustPosRl)
            .filter(
                CustPosRl.eid == record.device_id,
                CustPosRl.cust_cd == record.new_store_id,
                CustPosRl.useflg == RL_USEFLG_ACTIVE,
            )
            .first()
        )
        if new_rl:
            new_rl.posupddate = now
            new_rl.asset_status = ASSET_STATUS_ACTIVE
            new_rl.maintenancetyp = "BG"
            new_rl.maintenanceno = maintenance_no
            new_rl.maintenancedate = now
        else:
            eid_rec = db.session.query(EidModel).filter(EidModel.eid == record.device_id).first()
            item_cd = eid_rec.itemcd if eid_rec else ""
            db.session.add(
                CustPosRl(
                    cust_cd=record.new_store_id,
                    eid=record.device_id,
                    item_cd=item_cd,
                    useflg=RL_USEFLG_ACTIVE,
                    posupddate=now,
                    asset_status=ASSET_STATUS_ACTIVE,
                    maintenancetyp="BG",
                    maintenanceno=maintenance_no,
                    maintenancedate=now,
                    created_from="DEVICE_CHANGE",
                    source_id=record.device_change_id,
                )
            )

        # 设备状态保持原值不变（对齐 PB USP_PLAN_CONFRIM）
        # 磁卡号变更：设备物理位置不动，只改客户归属，不经过仓库，sflg 不更新
        # 注：旧实现设 sflg='8'（在库）不正确，磁卡号变更不涉及实物回仓库

        # 目标客户合并：tmm22_customers.useflg='0'（合并/废弃），对齐 PB USP_PLAN_CONFRIM
        target_customer = db.session.get(CustomerModel, record.new_store_id)
        if target_customer:
            target_customer.useflg = "0"

    @staticmethod
    def _write_back_plan_status(record: DeviceChange, operator: str) -> None:
        """回写预计划 plan_status='01'（计划完成）。

        对齐 PB"实施完成即计划完成"优化。仅当预计划当前 plan_status='04'（实施中）时回写。
        CK/BQ/BG 三种子类型都回写。
        """
        from app.models.sales import PlanCust

        plan = (
            db.session.query(PlanCust)
            .filter(PlanCust.imple_billid == record.device_change_id)
            .first()
        )
        if plan is None:
            return
        if (plan.plan_status or "00") != PLAN_STATUS_IN_PROGRESS:
            return
        plan.plan_status = PLAN_STATUS_COMPLETED
        plan.update_time = datetime.now(UTC)
        plan.updator = operator

    @staticmethod
    def _sync_customer_and_history(record: DeviceChange, operator: str, remark: str | None) -> None:
        """审核完成时同步客户主表并写历史表（CK/BG/BG 三种类型）。"""
        cust_cd = record.store_id or ""
        if not cust_cd:
            return

        customer = db.session.get(Customer, cust_cd)
        if customer is None:
            return

        change_type = record.change_type
        device_change_id = record.device_change_id

        if change_type in ("CK", "BG"):
            # 磁卡号变更：同步 cust_card，历史表记录旧/新磁卡号
            old_card = customer.cust_card or ""
            new_card = record.new_store_card or ""
            if new_card and new_card != old_card:
                customer.cust_card = new_card
                customer.replacedate = datetime.now(UTC)
            DeviceChangeRepository.save_customer_history(
                {
                    "cust_cd": cust_cd,
                    "change_type": change_type,
                    "old_value": old_card,
                    "new_value": new_card,
                    "oper_cd": operator,
                    "oper_date": datetime.now(UTC),
                    "change_reason": remark or f"{change_type} 磁卡号变更",
                    "device_change_id": device_change_id,
                }
            )
        elif change_type == "BQ":
            # 信息变更：同步联系人/电话/地址，历史表记录旧/新信息（JSON 快照）
            old_info = {
                "contactor": customer.contactor or "",
                "phone_no": customer.phone_no or "",
                "address": customer.address or "",
            }
            new_contactor = record.new_contactor or customer.contactor or ""
            new_tel = record.new_tel or customer.phone_no or ""
            new_address = record.new_address or customer.address or ""
            customer.contactor = new_contactor
            customer.phone_no = new_tel
            customer.address = new_address
            new_info = {
                "contactor": new_contactor,
                "phone_no": new_tel,
                "address": new_address,
            }
            DeviceChangeRepository.save_customer_history(
                {
                    "cust_cd": cust_cd,
                    "change_type": change_type,
                    "old_value": json.dumps(old_info, ensure_ascii=False),
                    "new_value": json.dumps(new_info, ensure_ascii=False),
                    "oper_cd": operator,
                    "oper_date": datetime.now(UTC),
                    "change_reason": remark or "BQ 信息变更",
                    "device_change_id": device_change_id,
                }
            )


class StoreCloseService(_BaseMaintenanceService):
    """门店关闭业务服务。"""

    @staticmethod
    def get(close_id: str) -> dict[str, Any] | None:
        record = StoreCloseRepository.get_by_id(close_id)
        if record is None:
            return None
        enriched = _enrich_store_card([record.to_dict()])
        return enriched[0]

    @staticmethod
    def list_records(
        status: str | None = None,
        store_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = StoreCloseRepository.list_by_filters(
            status=status, store_id=store_id, page=page, per_page=per_page
        )
        enriched = _enrich_store_card([item.to_dict() for item in items])
        return {
            "items": enriched,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = StoreCloseRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(close_id: str, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        record = StoreCloseRepository.get_by_id(close_id)
        if record is None:
            return None
        StoreCloseRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()

    def transition(
        self,
        close_id: str,
        to_status: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        record = StoreCloseRepository.get_by_id(close_id)
        if record is None:
            return {"success": False, "error": "关闭单不存在"}
        result = self._do_transition(record, to_status, operator, remark, pk_field="store_close_id")
        if result.get("success"):
            # 关单完成（to_status=5）联动客户经营状态（对齐 usp_plan_confrim 门店关闭分支）
            if to_status == CLOSE_STATUS and record.store_id:
                from app.services.customer_service import CustomerService

                CustomerService.set_store_close_status(record.store_id, record.close_type, operator)
                # 11e: 门店所有活跃 EID 写 type='R' + rl 全失效 + 回写计划 + 自动创建回收入库草稿
                self._write_eid_track_on_close_store(record, operator)
                self._invalidate_rl_on_close_store(record, operator)
                self._write_back_plan_status_store(record, operator)
                self._create_recycle_inbound_store(record, operator)
            db.session.commit()
        return result

    @staticmethod
    def _write_eid_track_on_close_store(record: StoreClose, operator: str) -> None:
        """门店关闭关单时写 tmm43_eid_track type='R'（回收）。

        对齐 PB usp_plan_confrim type='4' 分支 L591-593。
        对门店所有活跃 EID 写 R 记录，cust_cd=门店，n_cust_cd=None。
        refid=预计划号（通过 imple_billid 反查）。
        """
        from app.models.master import CustPosRl
        from app.models.master import Eid as EidModel
        from app.models.sales import PlanCust
        from app.repositories.system_repository import SystemRepository

        planno = (
            db.session.query(PlanCust.planno)
            .filter(PlanCust.imple_billid == record.store_close_id)
            .scalar()
        ) or ""

        change_date = datetime.now(UTC)

        # 查门店所有活跃 EID（通过 rl 反查，rl.useflg='1'）
        active_eids = (
            db.session.query(CustPosRl.eid, CustPosRl.item_cd)
            .filter(
                CustPosRl.cust_cd == record.store_id,
                CustPosRl.useflg == RL_USEFLG_ACTIVE,
            )
            .all()
        )

        for eid_val, item_cd in active_eids:
            eid_rec = db.session.query(EidModel).filter(EidModel.eid == eid_val).first()
            if eid_rec is None:
                continue
            SystemRepository.create_eid_track(
                eid=eid_val,
                itemcd=eid_rec.itemcd or item_cd or "",
                track_type=TRACK_TYPE_RECYCLE,
                operator=operator,
                refid=planno,
                change_date=change_date,
                cust_cd=record.store_id,
                n_cust_cd=None,
                sflg=eid_rec.sflg,
                n_sflg=eid_rec.sflg,
                whcd=eid_rec.whcd,
                n_whcd=eid_rec.whcd,
                install_date=eid_rec.install_date,
                n_install_date=eid_rec.install_date,
                remark=(
                    f"门店关闭 {record.store_close_id} 关单，设备 "
                    f"{eid_val} 从门店 {record.store_id} 回收"
                ),
            )

    @staticmethod
    def _invalidate_rl_on_close_store(record: StoreClose, operator: str) -> None:
        """门店关闭关单时失效 tmm35_cust_pos_rl + 设备回库待核实。

        门店所有活跃 rl 失效（useflg=0, asset_status=RETURNED），
        并将对应 tmm43_eid.sflg 置为 '2'（待核实），对齐 PB USP_PLAN_CONFRIM。
        """
        from app.models.master import CustPosRl
        from app.models.master import Eid as EidModel

        now = datetime.now(UTC)

        rls = (
            db.session.query(CustPosRl)
            .filter(
                CustPosRl.cust_cd == record.store_id,
                CustPosRl.useflg == RL_USEFLG_ACTIVE,
            )
            .all()
        )
        eid_vals = [rl.eid for rl in rls]
        for rl in rls:
            rl.useflg = RL_USEFLG_INACTIVE
            rl.asset_status = ASSET_STATUS_RETURNED
            rl.posupddate = now
        # 批量将设备回库待核实：tmm43_eid.sflg='3'（待检），对齐 PB USP_PLAN_CONFRIM
        # 注：sflg='2' 是"已报废"，'3' 才是"待检/待核实"
        if eid_vals:
            db.session.query(EidModel).filter(EidModel.eid.in_(eid_vals)).update(
                {"sflg": "3"}, synchronize_session=False
            )

    @staticmethod
    def _create_recycle_inbound_store(record: StoreClose, operator: str) -> None:
        """门店关闭关单时，为所有回收的自有资产创建回收入库草稿（IV=7）。

        按仓库配置 sysparm 'recycle_return_whcd' 创建入库草稿。
        仅当 asset_owner != '01'（自有资产）时创建。

        注：此方法在 _invalidate_rl_on_close_store 之后调用，
        此时 rl 已失效（useflg=0, asset_status=RETURNED），
        故按 cust_cd + asset_status=RETURNED 查询刚失效的 rl。
        """
        from app.models.master import CustPosRl, Eid as EidModel

        # 取门店刚失效的 rl（asset_status=RETURNED）的 eid
        rls = (
            db.session.query(CustPosRl.eid)
            .filter(
                CustPosRl.cust_cd == record.store_id,
                CustPosRl.asset_status == ASSET_STATUS_RETURNED,
            )
            .all()
        )
        eid_vals = [r.eid for r in rls if r.eid]
        if not eid_vals:
            return

        eid_rows = (
            db.session.query(EidModel)
            .filter(
                EidModel.eid.in_(eid_vals),
                EidModel.asset_owner != ASSET_OWNER_CUSTOMER,
            )
            .all()
        )
        if not eid_rows:
            return

        whcd = _get_sysparm_whcd(SYSPARM_RECYCLE_RETURN_WHCD)
        if not whcd:
            return

        eid_items = [
            {"eid": e.eid, "itemcd": e.itemcd, "itemtyp": e.itemtyp or "02"}
            for e in eid_rows
        ]
        _create_stock_in_draft(
            invtyp="7",
            whcd=whcd,
            refbillid=record.store_close_id,
            memo=f"门店关闭 {record.store_close_id} 关单自动创建回收入库",
            eid_items=eid_items,
            creator=operator,
        )

    @staticmethod
    def _write_back_plan_status_store(record: StoreClose, operator: str) -> None:
        """回写预计划 plan_status='01'（计划完成）。

        仅当预计划当前 plan_status='04'（实施中）时回写。
        """
        from app.models.sales import PlanCust

        plan = (
            db.session.query(PlanCust)
            .filter(PlanCust.imple_billid == record.store_close_id)
            .first()
        )
        if plan is None:
            return
        if (plan.plan_status or "00") != PLAN_STATUS_IN_PROGRESS:
            return
        plan.plan_status = PLAN_STATUS_COMPLETED
        plan.update_time = datetime.now(UTC)
        plan.updator = operator


# ---------------------------------------------------------------------------
# 设备资产与收费判断
# ---------------------------------------------------------------------------


class ChargeService:
    """ITSM 收费判断服务。"""

    @staticmethod
    def should_charge(store_id: str) -> dict[str, Any]:
        """判断门店是否需要收费及收费原因。

        客户资产（asset_owner='01'）为收费对象，保修期内预留免费逻辑。
        """
        assets = (
            db.session.query(CustPosRl)
            .filter(CustPosRl.cust_cd == store_id, CustPosRl.useflg == "1")
            .join(Eid, CustPosRl.eid == Eid.eid)
            .all()
        )

        chargeable: list[dict[str, Any]] = []
        for a in assets:
            if a.eid and getattr(a.eid, "asset_owner", None) == ASSET_OWNER_CUSTOMER:
                chargeable.append({"eid": a.eid.eid, "reason": "客户资产"})

        return {
            "should_charge": len(chargeable) > 0,
            "chargeable_assets": chargeable,
            "count": len(chargeable),
        }


# ---------------------------------------------------------------------------
# 公用附表服务
# ---------------------------------------------------------------------------


class D2DService:
    """上门服务记录服务（公用附表 TIT23）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = D2DRepository.list_by_maintenance_id(maintenance_id)
        result = [item.to_dict() for item in items]
        result = _enrich_user_names(result, ["d2d_engineer", "creator", "updator"])
        result = _enrich_sys_codes(result, "d2d_type", "D2D")
        result = _enrich_sys_codes(result, "jjbz", "ZT")
        return result

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = D2DRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(record_id: int, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        record = D2DRepository.get_by_id(record_id)
        if record is None:
            return None
        D2DRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()


class RVService:
    """客户回访服务（公用附表 TIT24）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = RVRepository.list_by_maintenance_id(maintenance_id)
        result = [item.to_dict() for item in items]
        result = _enrich_user_names(result, ["rv_operator", "creator", "updator"])
        result = _enrich_sys_codes(result, "satisfaction", "MY")
        return result

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = RVRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(record_id: int, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        record = RVRepository.get_by_id(record_id)
        if record is None:
            return None
        RVRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()


class AccessoriesUpdateService:
    """配件更新服务（TIT25）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = AccessoriesUpdateRepository.list_by_maintenance_id(maintenance_id)
        result = [item.to_dict() for item in items]
        result = _enrich_user_names(result, ["engineer_id", "creator", "updator"])
        return result

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = AccessoriesUpdateRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(record_id: int, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        record = AccessoriesUpdateRepository.get_by_id(record_id)
        if record is None:
            return None
        AccessoriesUpdateRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()


class CloseBillService:
    """关单服务（TIT27）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = CloseBillRepository.list_by_maintenance_id(maintenance_id)
        result = [item.to_dict() for item in items]
        result = _enrich_user_names(result, ["creator", "updator"])
        return result

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = CloseBillRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(record_id: int, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        record = CloseBillRepository.get_by_id(record_id)
        if record is None:
            return None
        CloseBillRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()


class DispatchRuleService:
    """派单规则引擎（TIT30_DISPATCH_RULE）。

    按故障类型匹配规则，依次尝试 target → fallback → ultimate_fallback，
    解析出 (accpectd_group, accpectder)。target_type 含义：
      - area_manager: 查门店所属区域的 usercd，组默认 'A1'
      - group_leader: 查 target_value 组编码的 leader_cd
      - manual: 不自动派单，返回 None
    """

    @staticmethod
    def resolve(
        fault_type: str | None,
        store_id: str | None,
    ) -> dict[str, Any] | None:
        """解析派单目标。

        Returns:
            {"accpectd_group": str, "accpectder": str, "rule_id": int} 或 None
        """
        from app.models.itsm import DispatchRule
        from app.models.system import Group

        # 按 priority 升序查询有效规则
        rules = (
            db.session.query(DispatchRule)
            .filter(DispatchRule.useflg == "1")
            .order_by(DispatchRule.priority.asc())
            .all()
        )
        if not rules:
            return None

        # 匹配优先级：fault_type + store_id 精确 > fault_type 精确 > store_id 精确 > 通用
        def _score(rule: DispatchRule) -> int:
            score = 0
            if fault_type and rule.fault_type and rule.fault_type == fault_type:
                score += 2
            if store_id and rule.store_id and rule.store_id == store_id:
                score += 1
            return score

        # 仅保留有匹配的规则，按分数降序（priority 已升序）
        scored = [(r, _score(r)) for r in rules]
        max_score = max(s for _, s in scored) if scored else 0
        # fault_type 或 store_id 至少有一项匹配，或通用规则（score=0 但 fault_type/store_id 均空）
        matched_candidates = [
            r for r, s in scored
            if s == max_score and (
                (fault_type and r.fault_type and r.fault_type == fault_type)
                or (store_id and r.store_id and r.store_id == store_id)
                or (not r.fault_type and not r.store_id)
            )
        ]
        matched = matched_candidates[0] if matched_candidates else None
        if matched is None:
            return None

        # 解析区域经理
        def _resolve_area_manager() -> tuple[str, str] | None:
            if not store_id:
                return None
            customer = db.session.query(Customer).filter(Customer.cust_cd == store_id).first()
            if customer is None or not customer.area_cd:
                return None
            area = (
                db.session.query(Area)
                .filter(Area.area_cd == customer.area_cd, Area.useflg == "1")
                .first()
            )
            if area is None or not area.usercd:
                return None
            return ("A1", area.usercd)

        # 解析组长
        def _resolve_group_leader(group_cd: str | None) -> tuple[str, str] | None:
            if not group_cd:
                return None
            group = db.session.get(Group, group_cd)
            if group is None or not group.leader_cd:
                return None
            return (group_cd, group.leader_cd)

        # 负载均衡：组内成员中当前未关单派工数最少者
        def _resolve_group_load_balance(group_cd: str | None) -> tuple[str, str] | None:
            if not group_cd:
                return None
            from app.models.itsm import MaintenanceDispatch, UserGroup
            from app.models.system import User

            # 组内在职成员
            members = (
                db.session.query(UserGroup.user_cd)
                .join(User, User.user_cd == UserGroup.user_cd)
                .filter(UserGroup.group_cd == group_cd, User.status == "1")
                .all()
            )
            member_cds = [m[0] for m in members]
            if not member_cds:
                return None
            # 统计每位成员当前未关单（维护单状态非 3/9）的派工数
            closed = ("3", "9")
            rows = (
                db.session.query(
                    MaintenanceDispatch.accpectder,
                    db.func.count(MaintenanceDispatch.id),
                )
                .join(MaintenanceDaily, MaintenanceDaily.maintenance_id == MaintenanceDispatch.maintenance_id)
                .filter(
                    MaintenanceDispatch.accpectd_group == group_cd,
                    MaintenanceDispatch.accpectder.in_(member_cds),
                    ~MaintenanceDaily.current_status.in_(closed),
                )
                .group_by(MaintenanceDispatch.accpectder)
                .all()
            )
            load_map = {r[0]: r[1] for r in rows}
            # 选负载最少者（0 负载优先），并列时取 member_cds 顺序第一个
            sorted_members = sorted(member_cds, key=lambda cd: load_map.get(cd, 0))
            return (group_cd, sorted_members[0])

        # 依次尝试三级目标
        for t_type, t_value in (
            (matched.target_type, matched.target_value),
            (matched.fallback_type, matched.fallback_value),
            (matched.ultimate_fallback_type, matched.ultimate_fallback_value),
        ):
            if not t_type:
                continue
            if t_type == "manual":
                return None
            if t_type == "area_manager":
                res = _resolve_area_manager()
                if res:
                    return {
                        "accpectd_group": res[0],
                        "accpectder": res[1],
                        "rule_id": matched.rule_id,
                        "target_type": t_type,
                        "target_value": t_value,
                        "auto_dispatch": getattr(matched, "auto_dispatch", "1") or "1",
                    }
            elif t_type == "group_leader":
                res = _resolve_group_leader(t_value)
                if res:
                    return {
                        "accpectd_group": res[0],
                        "accpectder": res[1],
                        "rule_id": matched.rule_id,
                        "target_type": t_type,
                        "target_value": t_value,
                        "auto_dispatch": getattr(matched, "auto_dispatch", "1") or "1",
                    }
            elif t_type == "load_balance":
                res = _resolve_group_load_balance(t_value)
                if res:
                    return {
                        "accpectd_group": res[0],
                        "accpectder": res[1],
                        "rule_id": matched.rule_id,
                        "target_type": t_type,
                        "target_value": t_value,
                        "auto_dispatch": getattr(matched, "auto_dispatch", "1") or "1",
                    }
        return None

    @staticmethod
    def list_rules() -> list[dict[str, Any]]:
        from app.models.itsm import DispatchRule

        rules = (
            db.session.query(DispatchRule)
            .filter(DispatchRule.useflg == "1")
            .order_by(DispatchRule.priority.asc())
            .all()
        )
        return [r.to_dict() for r in rules]

    @staticmethod
    def create_rule(data: dict[str, Any], creator: str) -> dict[str, Any]:
        """新增派单规则。"""
        from datetime import datetime

        from app.models.itsm import DispatchRule

        rule = DispatchRule(
            rule_name=data.get("rule_name", ""),
            priority=data.get("priority", 99),
            fault_type=data.get("fault_type") or None,
            store_id=data.get("store_id") or None,
            target_type=data.get("target_type") or None,
            target_value=data.get("target_value") or None,
            fallback_type=data.get("fallback_type") or None,
            fallback_value=data.get("fallback_value") or None,
            ultimate_fallback_type=data.get("ultimate_fallback_type") or None,
            ultimate_fallback_value=data.get("ultimate_fallback_value") or None,
            useflg="1",
            creator=creator,
            create_time=datetime.now(),
        )
        db.session.add(rule)
        db.session.commit()
        return rule.to_dict()

    @staticmethod
    def update_rule(rule_id: int, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        """更新派单规则。"""
        from datetime import datetime

        from app.models.itsm import DispatchRule

        rule = db.session.get(DispatchRule, rule_id)
        if rule is None:
            return None
        for k in (
            "rule_name", "priority", "fault_type", "store_id",
            "target_type", "target_value",
            "fallback_type", "fallback_value",
            "ultimate_fallback_type", "ultimate_fallback_value",
            "useflg",
        ):
            if k in data:
                setattr(rule, k, data[k] if data[k] != "" else None)
        rule.updator = updator
        rule.update_time = datetime.now()
        db.session.commit()
        return rule.to_dict()

    @staticmethod
    def delete_rule(rule_id: int) -> bool:
        """删除派单规则（物理删除）。"""
        from app.models.itsm import DispatchRule

        rule = db.session.get(DispatchRule, rule_id)
        if rule is None:
            return False
        db.session.delete(rule)
        db.session.commit()
        return True


class DispatchService:
    """分派服务（TIT21）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = DispatchRepository.list_by_maintenance_id(maintenance_id)
        result = [item.to_dict() for item in items]
        result = _enrich_user_names(result, ["operator", "accpectder", "creator", "updator"])
        result = _enrich_group_names(result, "accpectd_group")
        result = _enrich_sys_codes(result, "maintenance_type", "MT")
        result = _enrich_notify_status(result, "dispatch")
        return result

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        # 派工时间默认当前时间
        if not data.get("dispatch_time"):
            data["dispatch_time"] = datetime.now()
        record = DispatchRepository.create(data, creator)
        # 业务操作流水ID：派工记录自身主键，flush 获取 id 后回填
        db.session.flush()
        if not record.business_operation_id:
            from sqlalchemy import func
            from app.models.itsm import MaintenanceDispatch as _MD
            max_op = db.session.query(func.max(_MD.business_operation_id)).filter(
                _MD.maintenance_id == record.maintenance_id
            ).scalar()
            record.business_operation_id = (max_op or 0) + 1
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(record_id: int, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        record = DispatchRepository.get_by_id(record_id)
        if record is None:
            return None
        DispatchRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def auto_create(
        maintenance_id: str,
        store_id: str,
        creator: str,
        fault_type: str | None = None,
    ) -> dict[str, Any] | None:
        """维护单创建时按派单规则自动生成派工记录。

        逻辑链：
        1. DispatchRuleService.resolve(fault_type, store_id) 解析目标
           - area_manager: 门店→区域→区域负责人
           - group_leader: 组编码→组长
           - manual: 不自动派单
           - 失败时按 fallback → ultimate_fallback 链式兜底
        2. 解析成功则插入 tit21_maintenance_dispatch 记录
        3. 创建时一次性渲染 DISPATCH 通知模板快照写入 TNTF02_NOTIFICATION

        Args:
            maintenance_id: 维护单号
            store_id: 门店ID（即客户编码 custcd）
            creator: 创建人编码
            fault_type: 故障类型（用于规则匹配）

        Returns:
            派工记录 dict 或 None（规则命中 manual 或全部兜底失败时跳过）
        """
        import logging
        logger = logging.getLogger(__name__)
        try:
            target = DispatchRuleService.resolve(fault_type, store_id)
            if target is None or target.get("auto_dispatch") == "0":
                logger.info(
                    f"自动派单跳过：maintenance_id={maintenance_id}, "
                    f"fault_type={fault_type} 命中 manual 或无可用目标"
                )
                return None
            data = {
                "maintenance_id": maintenance_id,
                "operator": creator,
                "accpectd_group": target["accpectd_group"],
                "accpectder": target["accpectder"],
                "dispatch_time": datetime.now(),
            }
            record = DispatchRepository.create(data, creator)
            db.session.flush()
            # 业务操作流水ID：派工记录自身主键
            if not record.business_operation_id:
                from sqlalchemy import func
                from app.models.itsm import MaintenanceDispatch as _MD2
                max_op = db.session.query(func.max(_MD2.business_operation_id)).filter(
                    _MD2.maintenance_id == record.maintenance_id
                ).scalar()
                record.business_operation_id = (max_op or 0) + 1
            # 创建通知快照（与派工同事务，一次性渲染模板）
            DispatchService._create_notification(record, store_id, fault_type, creator)
            db.session.commit()
            logger.info(
                f"自动派单成功：maintenance_id={maintenance_id}, "
                f"accpectder={target['accpectder']}, rule_id={target.get('rule_id')}"
            )
            return record.to_dict()
        except Exception as e:
            db.session.rollback()
            logger.warning(f"自动派单失败 maintenance_id={maintenance_id}: {e}")
            return None

    @staticmethod
    def _create_notification(
        record: Any,
        store_id: str | None,
        fault_type: str | None,
        creator: str,
    ) -> None:
        """派工创建时一次性渲染 DISPATCH 模板写入通知快照。

        模板渲染采用 Jinja2，占位符一次性替换后落库，后续不再重渲染。
        """
        import logging
        from jinja2 import Template

        from app.models.notification import NotificationTemplate
        from app.repositories.notification_repository import NotificationRepository

        logger = logging.getLogger(__name__)
        try:
            tpl = db.session.get(NotificationTemplate, "DISPATCH")
            if tpl is None:
                logger.warning("DISPATCH 通知模板未配置，跳过通知创建")
                return
            # 解析分派人姓名
            accpectder = record.accpectder or ""
            accpectder_name = accpectder
            if accpectder:
                user = db.session.query(User).filter(User.user_cd == accpectder).first()
                if user and user.user_nm:
                    accpectder_name = user.user_nm
            context = {
                "maintenance_id": record.maintenance_id,
                "store_id": store_id or "",
                "accpectder_name": accpectder_name,
                "accpectd_group": record.accpectd_group or "",
                "fault_type": fault_type or "",
            }
            subject = Template(tpl.subject or "").render(**context)
            body = Template(tpl.body or "").render(**context)
            NotificationRepository.create(
                {
                    "template_id": "DISPATCH",
                    "channel": "internal",
                    "recipient": accpectder,
                    "subject": subject,
                    "body": body,
                    "ref_type": "dispatch",
                    "ref_id": str(record.maintenance_id),
                    "dispatch_id": getattr(record, "id", None),
                    "send_status": "pending",
                },
                creator,
            )
        except Exception as e:
            logger.warning(f"派工通知创建失败 maintenance_id={record.maintenance_id}: {e}")


class RecycleTaskService(_BaseMaintenanceService):
    """回收任务服务（TIT20，P0-1/优化4.2）。

    将取机/回收业务从日常维护单中剖离出来，
    拥有独立的状态机和生命周期。
    """

    @staticmethod
    def get(recycle_id: str) -> dict[str, Any] | None:
        record = RecycleTaskRepository.get_by_id(recycle_id)
        if record is None:
            return None
        enriched = _enrich_store_card([record.to_dict()], key="cust_cd")
        return enriched[0]

    @staticmethod
    def list_records(
        task_status: str | None = None,
        cust_cd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = RecycleTaskRepository.list_by_filters(
            task_status=task_status, cust_cd=cust_cd, page=page, per_page=per_page
        )
        enriched = _enrich_store_card([item.to_dict() for item in items], key="cust_cd")
        return {
            "items": enriched,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = RecycleTaskRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(recycle_id: str, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        record = RecycleTaskRepository.get_by_id(recycle_id)
        if record is None:
            return None
        RecycleTaskRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()

    def transition(
        self,
        recycle_id: str,
        to_status: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        record = RecycleTaskRepository.get_by_id(recycle_id)
        if record is None:
            return {"success": False, "error": "回收任务不存在"}
        from_status: str = record.task_status or "1"
        result = StateMachine.validate_transition(from_status, to_status)
        if not result["valid"]:
            return {"success": False, "error": result.get("error", "状态流转验证失败")}
        RecycleTaskRepository.update_status(record, to_status, operator)
        # 11d: 关单（to_status=5）时写 EidTrack + rl 失效 + 回写计划 + 自动创建回收入库草稿
        if to_status == CLOSE_STATUS:
            self._write_eid_track_on_close_recycle(record, operator)
            self._invalidate_rl_on_close_recycle(record, operator)
            self._write_back_plan_status_recycle(record, operator)
            self._create_recycle_inbound_recycle(record, operator)
        db.session.commit()
        return {"success": True, "from_status": from_status, "to_status": to_status}

    @staticmethod
    def _write_eid_track_on_close_recycle(record: RecycleTask, operator: str) -> None:
        """回收任务关单时写 tmm43_eid_track type='R'（回收）。

        对齐 PB usp_plan_confrim type='3' 分支 L591-593。
        对每个明细 asset_id 写一条 R 记录，cust_cd=门店，n_cust_cd=None。
        refid=预计划号（通过 imple_billid 反查）。
        """
        from app.models.master import Eid as EidModel
        from app.models.sales import PlanCust
        from app.repositories.system_repository import SystemRepository

        planno = (
            (
                db.session.query(PlanCust.planno)
                .filter(PlanCust.imple_billid == record.recycle_id)
                .scalar()
            )
            or record.plan_no
            or ""
        )

        change_date = datetime.now(UTC)

        for dtl in record.details:
            eid_val = dtl.asset_id or ""
            if not eid_val:
                continue
            eid_rec = db.session.query(EidModel).filter(EidModel.eid == eid_val).first()
            if eid_rec is None:
                continue
            SystemRepository.create_eid_track(
                eid=eid_val,
                itemcd=eid_rec.itemcd or "",
                track_type=TRACK_TYPE_RECYCLE,
                operator=operator,
                refid=planno,
                change_date=change_date,
                cust_cd=record.cust_cd,
                n_cust_cd=None,
                sflg=eid_rec.sflg,
                n_sflg=eid_rec.sflg,
                whcd=eid_rec.whcd,
                n_whcd=dtl.warehouse_cd or eid_rec.whcd,
                install_date=eid_rec.install_date,
                n_install_date=eid_rec.install_date,
                remark=(
                    f"回收任务 {record.recycle_id} 关单，设备 "
                    f"{eid_val} 从门店 {record.cust_cd} 回收"
                ),
            )

    @staticmethod
    def _invalidate_rl_on_close_recycle(record: RecycleTask, operator: str) -> None:
        """回收任务关单时失效 tmm35_cust_pos_rl + 设备回库待核实。

        对每个明细 asset_id 失效对应的活跃 rl（useflg=0, asset_status=RETURNED），
        并将 tmm43_eid.sflg 置为 '2'（待核实），对齐 PB USP_PLAN_CONFRIM。
        """
        from app.models.master import CustPosRl
        from app.models.master import Eid as EidModel

        now = datetime.now(UTC)

        for dtl in record.details:
            eid_val = dtl.asset_id or ""
            if not eid_val:
                continue
            rl = (
                db.session.query(CustPosRl)
                .filter(
                    CustPosRl.eid == eid_val,
                    CustPosRl.useflg == RL_USEFLG_ACTIVE,
                )
                .first()
            )
            if rl:
                rl.useflg = RL_USEFLG_INACTIVE
                rl.asset_status = ASSET_STATUS_RETURNED
                rl.posupddate = now
            # 设备回库待核实：tmm43_eid.sflg='3'（待检），对齐 PB USP_PLAN_CONFRIM
            # 注：sflg='2' 是"已报废"，'3' 才是"待检/待核实"
            eid_rec = db.session.query(EidModel).filter(EidModel.eid == eid_val).first()
            if eid_rec:
                eid_rec.sflg = "3"

    @staticmethod
    def _create_recycle_inbound_recycle(record: RecycleTask, operator: str) -> None:
        """回收任务关单时，为明细中自有资产创建回收入库草稿（IV=7）。

        按仓库配置 sysparm 'recycle_return_whcd' 创建入库草稿。
        仅当 asset_owner != '01'（自有资产）时创建。
        """
        from app.models.master import Eid as EidModel

        eid_vals = [d.asset_id for d in record.details if d.asset_id]
        if not eid_vals:
            return

        eid_rows = (
            db.session.query(EidModel)
            .filter(
                EidModel.eid.in_(eid_vals),
                EidModel.asset_owner != ASSET_OWNER_CUSTOMER,
            )
            .all()
        )
        if not eid_rows:
            return

        whcd = _get_sysparm_whcd(SYSPARM_RECYCLE_RETURN_WHCD)
        if not whcd:
            return

        eid_items = [
            {"eid": e.eid, "itemcd": e.itemcd, "itemtyp": e.itemtyp or "02"}
            for e in eid_rows
        ]
        _create_stock_in_draft(
            invtyp="7",
            whcd=whcd,
            refbillid=record.recycle_id,
            memo=f"回收任务 {record.recycle_id} 关单自动创建回收入库",
            eid_items=eid_items,
            creator=operator,
        )

    @staticmethod
    def _write_back_plan_status_recycle(record: RecycleTask, operator: str) -> None:
        """回写预计划 plan_status='01'（计划完成）。

        仅当预计划当前 plan_status='04'（实施中）时回写。
        """
        from app.models.sales import PlanCust

        plan = db.session.query(PlanCust).filter(PlanCust.imple_billid == record.recycle_id).first()
        if plan is None:
            return
        if (plan.plan_status or "00") != PLAN_STATUS_IN_PROGRESS:
            return
        plan.plan_status = PLAN_STATUS_COMPLETED
        plan.update_time = datetime.now(UTC)
        plan.updator = operator

    @staticmethod
    def add_detail(recycle_id: str, data: dict[str, Any]) -> dict[str, Any]:
        dtl = RecycleTaskRepository.add_detail(recycle_id, data)
        db.session.commit()
        return dtl.to_dict()

    @staticmethod
    def delete_detail(recycle_id: str, asset_id: str) -> bool:
        """删除回收任务明细。"""
        return RecycleTaskRepository.delete_detail(recycle_id, asset_id)

    @staticmethod
    def list_details(recycle_id: str) -> list[dict[str, Any]]:
        items = RecycleTaskRepository.list_details(recycle_id)
        return [item.to_dict() for item in items]


class MaintenancePlanService:
    """保养计划服务（TIT17_PLAN）。"""

    @staticmethod
    def get(plan_id: int) -> dict[str, Any] | None:
        record = MaintenancePlanRepository.get_by_id(plan_id)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_records(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = MaintenancePlanRepository.list_all(page=page, per_page=per_page)
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = MaintenancePlanRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(plan_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        record = MaintenancePlanRepository.get_by_id(plan_id)
        if record is None:
            return None
        MaintenancePlanRepository.update(record, data)
        db.session.commit()
        return record.to_dict()


class MaintenanceT17Service(_BaseMaintenanceService):
    """日常保养工单服务（TIT17_MAINTENANCE）。"""

    @staticmethod
    def get(maintenance_id: str) -> dict[str, Any] | None:
        record = MaintenanceT17Repository.get_by_id(maintenance_id)
        if record is None:
            return None
        enriched = _enrich_store_card([record.to_dict()])
        return enriched[0]

    @staticmethod
    def list_records(
        status: str | None = None,
        store_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = MaintenanceT17Repository.list_by_filters(
            status=status, store_id=store_id, page=page, per_page=per_page
        )
        enriched = _enrich_store_card([item.to_dict() for item in items])
        return {
            "items": enriched,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    def transition(
        self,
        maintenance_id: str,
        to_status: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        record = MaintenanceT17Repository.get_by_id(maintenance_id)
        if record is None:
            return {"success": False, "error": "保养工单不存在"}
        result = self._do_transition(record, to_status, operator, remark, pk_field="maintenance_id")
        if result.get("success"):
            db.session.commit()
        return result


# TODO(cleanup): 免费更换（TIT28）已废弃，FreeReplaceService 不再被业务调用。
# 保留仅供历史数据查询，后续版本与 Repository/Model/Schema/API 一并清理。
class FreeReplaceService(_BaseMaintenanceService):
    """免费更换工单服务（TIT28_FREE_REPLACE）—— 已废弃。"""

    @staticmethod
    def get(renew_id: str) -> dict[str, Any] | None:
        record = FreeReplaceRepository.get_by_id(renew_id)
        if record is None:
            return None
        result = record.to_dict()
        result["equipments"] = [d.to_dict() for d in record.equipments]  # type: ignore[attr-defined]
        return result

    @staticmethod
    def list_records(
        status: str | None = None,
        store_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = FreeReplaceRepository.list_by_filters(
            status=status, store_id=store_id, page=page, per_page=per_page
        )
        enriched = _enrich_store_card([item.to_dict() for item in items])
        return {
            "items": enriched,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(
        data: dict[str, Any],
        details: list[dict[str, Any]],
        creator: str,
    ) -> dict[str, Any]:
        record = FreeReplaceRepository.create(data, creator)
        for detail_data in details:
            FreeReplaceRepository.add_detail(renew_id=record.renew_id, data=detail_data)
        db.session.commit()
        return record.to_dict()

    def transition(
        self,
        renew_id: str,
        to_status: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        record = FreeReplaceRepository.get_by_id(renew_id)
        if record is None:
            return {"success": False, "error": "免费更换单不存在"}

        result = self._do_transition(record, to_status, operator, remark, pk_field="renew_id")

        if result.get("success"):
            FreeReplaceRepository.update_status(record, to_status, operator)
            db.session.commit()
        return result


# ============================================================================
# ITSM 附表 Service（P1 补全）
# ============================================================================


class PayListService:
    """收费记录服务（TIT26_PAYLIST）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = PayListRepository.list_by_maintenance_id(maintenance_id)
        result = [item.to_dict() for item in items]
        result = _enrich_user_names(result, ["engineer_id", "creator", "updator"])
        return result

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = PayListRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(record_id: int, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        record = PayListRepository.get_by_id(record_id)
        if record is None:
            return None
        PayListRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()


class MaintenanceLiabilityService:
    """维护单责任豁免服务（TIT10_MAINTENANCE_LIABILITY）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = MaintenanceLiabilityRepository.list_by_maintenance_id(maintenance_id)
        return [item.to_dict() for item in items]

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = MaintenanceLiabilityRepository.create(data)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(record_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        from app.models.itsm import MaintenanceLiability

        record = db.session.get(MaintenanceLiability, record_id)
        if record is None:
            return None
        MaintenanceLiabilityRepository.update(record, data)
        db.session.commit()
        return record.to_dict()


class LiabilityRegService:
    """责任豁免字典服务（TIT02_LIABILITYREG）。"""

    @staticmethod
    def get(liab_cd: str) -> dict[str, Any] | None:
        record = LiabilityRegRepository.get_by_id(liab_cd)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [d.to_dict() for d in record.details]
        return result

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        items = LiabilityRegRepository.list_all()
        return [item.to_dict() for item in items]

    @staticmethod
    def create(data: dict[str, Any], details: list[dict[str, Any]]) -> dict[str, Any]:
        record = LiabilityRegRepository.create(data)
        for detail_data in details:
            LiabilityRegRepository.add_detail(liab_cd=record.liab_cd, data=detail_data)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(liab_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = LiabilityRegRepository.get_by_id(liab_cd)
        if record is None:
            return None
        LiabilityRegRepository.update(record, data)
        db.session.commit()
        return record.to_dict()


class MaintenanceAttcService:
    """附件服务（TIT11_MAINTENANCE_ATTC）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = MaintenanceAttcRepository.list_by_maintenance_id(maintenance_id)
        return [item.to_dict() for item in items]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = MaintenanceAttcRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()


class PosDetailService:
    """换机配件明细服务（TIT10_POS_DETAIL）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = PosDetailRepository.list_by_maintenance_id(maintenance_id)
        return [item.to_dict() for item in items]

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = PosDetailRepository.create(data)
        db.session.commit()
        return record.to_dict()


class NoCloseTrackService:
    """未关单跟踪服务（TIT29_NOCLOSE_TRACK）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = NoCloseTrackRepository.list_by_maintenance_id(maintenance_id)
        return [item.to_dict() for item in items]

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = NoCloseTrackRepository.list_all(page=page, per_page=per_page)
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = NoCloseTrackRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()


class RepairInfoService:
    """报修信息服务（TIT05_REPAIRINFO）。"""

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = RepairInfoRepository.list_all(page=page, per_page=per_page)
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = RepairInfoRepository.create(data)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def delete(record_id: int) -> bool:
        from app.models.itsm import RepairInfo

        record = db.session.get(RepairInfo, record_id)
        if record is None:
            return False
        RepairInfoRepository.delete(record)
        db.session.commit()
        return True


class TimepointAreaService:
    """时间点级别服务（TIT01_TIMEPOINT_AREA）。"""

    @staticmethod
    def get(levels: str) -> dict[str, Any] | None:
        record = TimepointAreaRepository.get_by_id(levels)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        items = TimepointAreaRepository.list_all()
        return [item.to_dict() for item in items]

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = TimepointAreaRepository.create(data)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(levels: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = TimepointAreaRepository.get_by_id(levels)
        if record is None:
            return None
        TimepointAreaRepository.update(record, data)
        db.session.commit()
        return record.to_dict()


class MaintenanceDailyTrackService:
    """状态变更轨迹服务（TIT10_MAIN_TRACK）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = MaintenanceDailyTrackRepository.list_by_maintenance_id(maintenance_id)
        return [item.to_dict() for item in items]

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = MaintenanceDailyTrackRepository.create(data)
        db.session.commit()
        return record.to_dict()


class OnChooseDtService:
    """开通选择明细服务（TIT19_ON_CHOOSEDT）。"""

    @staticmethod
    def list_by_bill_id(bill_id: str) -> list[dict[str, Any]]:
        items = OnChooseDtRepository.list_by_bill_id(bill_id)
        return [item.to_dict() for item in items]

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = OnChooseDtRepository.create(data)
        db.session.commit()
        return record.to_dict()
