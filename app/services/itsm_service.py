"""ITSM 核心业务服务层（状态机集成）。"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.extensions import db
from app.models.itsm import (
    AccessoriesUpdate,
    DeviceChange,
    Maintenance,
    MaintenanceD2D,
    MaintenanceDaily,
    MaintenanceOpen,
    MaintenanceRenovate,
    RecycleTask,
    StoreClose,
)
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
from app.services.business_flow_service import BusinessFlowService
from app.services.event_bus import EventBus

if TYPE_CHECKING:
    pass

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
ASSET_OWNER_CUSTOMER = "03"  # 门店资产（OW字典：客户购买的设备）
# asset_owner != "03" 即为公司侧资产（01商用电子/02通方信息/04海晟）

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


def _get_sys_code_nm(code_typ: str, code_cd: str) -> str | None:
    """查单个字典码值的名称（tmm31_syscodes）。

    Args:
        code_typ: 字典类型（如 PAY_SVC, PAY_CONS, C_TYPE）
        code_cd: 字典码值

    Returns:
        字典名称，未找到返回 None
    """
    if not code_cd:
        return None
    row = (
        db.session.query(SysCode.code_nm)
        .filter(SysCode.code_typ == code_typ, SysCode.code_cd == code_cd)
        .first()
    )
    return row[0] if row else None


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

    # 收集所有 (ref_id, dispatch_id) 对，用于匹配通知记录
    # dispatch 类型：ref_id=maintenance_id, dispatch_id=business_operation_id（同单内序号）
    # 其他类型：ref_id=业务ID, dispatch_id=记录自身ID
    ref_pairs: set[tuple[str, int]] = set()
    for r in items:
        if ref_type == "dispatch":
            mid = r.get("maintenance_id")
            opid = r.get("business_operation_id")
            if mid and opid:
                ref_pairs.add((str(mid), int(opid)))
        else:
            rid = r.get("id")
            ref = r.get("ref_id") or r.get("maintenance_id")
            if rid and ref:
                ref_pairs.add((str(ref), int(rid)))

    if not ref_pairs:
        return items

    rows = (
        db.session.query(
            Notification.ref_id, Notification.dispatch_id,
            Notification.send_status, Notification.read_status,
        )
        .filter(Notification.ref_type == ref_type)
        .all()
    )
    status_order = {"sent": 3, "pending": 2, "failed": 1}
    notify_map: dict[tuple[str, int], dict[str, str]] = {}
    for ref, did, send_st, read_st in rows:
        if did is None:
            continue
        key = (ref, did)
        prev = notify_map.get(key)
        if prev is None or status_order.get(send_st or "", 0) > status_order.get(prev.get("send", ""), 0):
            notify_map[key] = {"send": send_st or "", "read": read_st or "unread"}

    for r in items:
        if ref_type == "dispatch":
            mid = r.get("maintenance_id")
            opid = r.get("business_operation_id")
            key = (str(mid), int(opid)) if mid and opid else None
        else:
            rid = r.get("id")
            ref = r.get("ref_id") or r.get("maintenance_id")
            key = (str(ref), int(rid)) if rid and ref else None
        if key and key in notify_map:
            info = notify_map[key]
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

    # 更换次数 ghsl（对齐 PB d_whd_report/d_whd_report_ex：COUNT TIT25_ACCESSORIES_UPDATE）
    # C7 报表适配：TIT25/TIT26 合并后统一查 TIT25，审核标志用 auditflg
    mid_list = [r.get("maintenance_id") for r in items if r.get("maintenance_id")]
    ghsl_map: dict[str, int] = {}
    if mid_list:
        rows = (
            db.session.query(
                AccessoriesUpdate.maintenance_id,
                db.func.count(AccessoriesUpdate.id),
            )
            .filter(AccessoriesUpdate.maintenance_id.in_(mid_list))
            .group_by(AccessoriesUpdate.maintenance_id)
            .all()
        )
        ghsl_map = {mid: int(cnt) for mid, cnt in rows}

    for r in items:
        r["fault_type_nm"] = fault_map.get(r.get("fault_type") or "", "")
        r["current_status_nm"] = status_map.get(r.get("current_status") or "", "")
        r["creator_nm"] = user_map.get(r.get("creator") or "", "")
        r["updator_nm"] = user_map.get(r.get("updator") or "", "")
        r["firstor_nm"] = user_map.get(r.get("firstor") or "", "")
        r["ghsl"] = ghsl_map.get(r.get("maintenance_id") or "", 0)
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
            # 完成维修（to_status=5 已解决）：触发 L1-L11 联动（配件/资产落地）
            # 回访确认关单（to_status=3 已关闭）：只改状态，不触发联动（联动已在 5 时完成）
            if to_status == CLOSE_STATUS:
                # P0-1: 完成维修时读 TIT23 最新 d2d_result 派生 is_success
                # 离店不改状态，完成维修才是唯一触发器
                self._derive_is_success_from_latest_d2d(record)
                self._create_service_return_inbound(record, operator)
                # 1a 阶段关单联动 L1/L2/L3/L11
                self._write_eid_track_on_daily_close(record, operator)
                self._update_eid_warranty_on_daily_close(record, operator)
                self._update_pos_r_eid_on_daily_close(record, operator)
                self._write_pos_detail_on_daily_close(record, operator)
                # 1b 阶段关单联动 L4/L5
                self._clear_new_part_whcd_on_close(record, operator)
                self._scrap_old_part_on_close(record, operator)
            # to_status=3（回访确认关单）：只改状态，不触发联动
            db.session.commit()
        return result

    @staticmethod
    def _derive_is_success_from_latest_d2d(record: Any) -> None:
        """完成维修时从 TIT23 最新离店记录派生 is_success。

        离店不改主表状态，完成维修 transition(5) 时：
        - 读 TIT23 最新 d2d_type='2'（离店）记录的 d2d_result/closure_reason
        - 按 StateMachine.resolve_is_success 派生 is_success
        """
        from app.models.itsm import MaintenanceD2D

        latest_d2d = (
            db.session.query(MaintenanceD2D)
            .filter(
                MaintenanceD2D.maintenance_id == record.maintenance_id,
                MaintenanceD2D.d2d_type == "2",  # 离店
                MaintenanceD2D.useflg == "1",
            )
            .order_by(MaintenanceD2D.leave_time.desc())
            .first()
        )
        if latest_d2d is None:
            return
        d2d_result = latest_d2d.d2d_result
        closure_reason = getattr(latest_d2d, "closure_reason", None)
        record.is_success = StateMachine.resolve_is_success(d2d_result, closure_reason)

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

    @staticmethod
    def _write_eid_track_on_daily_close(record: Any, operator: str) -> None:
        """L1：日常维护单关单时写 tmm43_eid_track type='A'（配件更换属性变更）。

        对每条配件更新记录（TIT25_ACCESSORIES_UPDATE），写一条 EidTrack 轨迹。
        """
        from app.models.itsm import AccessoriesUpdate
        from app.models.master import Eid as EidModel, EidTrack

        rows = (
            db.session.query(AccessoriesUpdate)
            .filter(
                AccessoriesUpdate.maintenance_id == record.maintenance_id,
                AccessoriesUpdate.old_accessories_id.isnot(None),
                AccessoriesUpdate.old_accessories_id != "",
            )
            .all()
        )
        if not rows:
            return

        change_date = datetime.now()
        for r in rows:
            old_eid = (
                db.session.query(EidModel)
                .filter(EidModel.eid == r.old_accessories_id)
                .first()
            )
            if not old_eid:
                continue
            new_eid = (
                db.session.query(EidModel)
                .filter(EidModel.eid == r.new_accessories_id)
                .first()
                if r.new_accessories_id
                else None
            )
            track = EidTrack(
                type=TRACK_TYPE_ATTRIBUTE,  # 'A' 属性变更
                change_date=change_date,
                itemcd=old_eid.itemcd,
                eid=old_eid.eid,
                opercd=operator,
                gendate=change_date,
                useflg="1",
                sflg=old_eid.sflg,
                n_sflg=new_eid.sflg if new_eid else old_eid.sflg,
                whcd=old_eid.whcd,
                n_whcd=old_eid.whcd,
                refid=record.maintenance_id,
                n_refid=record.maintenance_id,
                install_date=old_eid.install_date,
                n_install_date=new_eid.install_date if new_eid else old_eid.install_date,
                asset_owner=old_eid.asset_owner,
                n_asset_owner=new_eid.asset_owner if new_eid else old_eid.asset_owner,
                remark=f"日常维护单 {record.maintenance_id} 关单，配件更换",
            )
            db.session.add(track)

    @staticmethod
    def _update_eid_warranty_on_daily_close(record: Any, operator: str) -> None:
        """L2：日常维护单关单时更新 tmm43_eid.warranty_expire（新配件保修期）。

        对每条配件更新记录，新配件的 warranty_expire = install_date + newperiod/oldperiod。
        """
        from app.models.itsm import AccessoriesUpdate
        from app.models.master import Eid as EidModel, Item

        rows = (
            db.session.query(AccessoriesUpdate)
            .filter(
                AccessoriesUpdate.maintenance_id == record.maintenance_id,
                AccessoriesUpdate.new_accessories_id.isnot(None),
                AccessoriesUpdate.new_accessories_id != "",
            )
            .all()
        )
        if not rows:
            return

        change_date = datetime.now()
        for r in rows:
            new_eid = (
                db.session.query(EidModel)
                .filter(EidModel.eid == r.new_accessories_id)
                .first()
            )
            if not new_eid:
                continue
            # 新配件安装日期 = 关单日期
            new_eid.install_date = change_date
            # 派生保修到期日
            item = db.session.get(Item, new_eid.itemcd)
            if item:
                period = item.newperiod if new_eid.old_degree == 12 else item.oldperiod
                if period:
                    from datetime import timedelta

                    new_eid.warranty_expire = change_date + timedelta(days=int(period))

    @staticmethod
    def _update_pos_r_eid_on_daily_close(record: Any, operator: str) -> None:
        """L3：日常维护单关单时更新 tmm44_pos_r_eid（整机更换时旧eid失效+新eid关联）。

        仅对 c_type='4'（整机更换）的记录执行。
        """
        from app.models.itsm import AccessoriesUpdate
        from app.models.master import PosREid

        rows = (
            db.session.query(AccessoriesUpdate)
            .filter(
                AccessoriesUpdate.maintenance_id == record.maintenance_id,
                AccessoriesUpdate.c_type == "4",  # 整机更换
            )
            .all()
        )
        if not rows:
            return

        change_date = datetime.now()
        for r in rows:
            # 旧整机 eid 失效
            if r.old_accessories_id:
                old_rows = (
                    db.session.query(PosREid)
                    .filter(PosREid.eid == r.old_accessories_id, PosREid.useflg == "1")
                    .all()
                )
                for old_row in old_rows:
                    old_row.useflg = "0"
                    old_row.upddate = change_date
            # 新整机 eid 关联
            if r.new_accessories_id:
                new_row = PosREid(
                    posid=r.device_id or "",
                    eid=r.new_accessories_id,
                    itemcd=r.itemcd or "",
                    opercd=operator,
                    gendate=change_date,
                    upddate=change_date,
                    useflg="1",
                )
                db.session.add(new_row)

    @staticmethod
    def _write_pos_detail_on_daily_close(record: Any, operator: str) -> None:
        """L11：日常维护单关单时写 TIT10_POS_DETAIL（c_type=4 整机更换记录）。

        对每条 c_type='4' 的配件更新记录，写一条 PosDetail 整机更换明细。
        """
        from app.models.itsm import AccessoriesUpdate, PosDetail

        rows = (
            db.session.query(AccessoriesUpdate)
            .filter(
                AccessoriesUpdate.maintenance_id == record.maintenance_id,
                AccessoriesUpdate.c_type == "4",  # 整机更换
            )
            .all()
        )
        if not rows:
            return

        change_date = datetime.now()
        for r in rows:
            # 旧整机记录（noflg='0' 旧设备）
            if r.old_accessories_id:
                old_detail = PosDetail(
                    bill_id=record.maintenance_id,
                    noflg="0",  # 旧设备
                    device_id=r.device_id or "",
                    item_cd=r.itemcd or "",
                    accessories_id=r.old_accessories_id,
                    status="5",  # 已关单
                    create_time=change_date,
                    creator=operator,
                )
                db.session.add(old_detail)
            # 新整机记录（noflg='1' 新设备）
            if r.new_accessories_id:
                new_detail = PosDetail(
                    bill_id=record.maintenance_id,
                    noflg="1",  # 新设备
                    device_id=r.device_id or "",
                    item_cd=r.itemcd or "",
                    accessories_id=r.new_accessories_id,
                    status="5",  # 已关单
                    create_time=change_date,
                    creator=operator,
                )
                db.session.add(new_detail)

    @staticmethod
    def _clear_new_part_whcd_on_close(record: Any, operator: str) -> None:
        """L4：日常维护单关单时清空新配件 whcd（标记已安装）。

        对每条配件更新记录（TIT25_ACCESSORIES_UPDATE）的新配件（new_accessories_id），
        将 tmm43_eid.whcd 置 NULL，sflg 保持 '1'（已使用）。

        ES 字典 '1' 双义靠 whcd 区分：
          - whcd = 工程师仓 → 持有中（服务领用出库后）
          - whcd = NULL → 已安装（关单 L4 后）

        对齐 PB USP_TRANS_IN_CONFRIM.sql:914-917 set sflg='1', refid=v_id。
        """
        from app.models.itsm import AccessoriesUpdate
        from app.models.master import Eid as EidModel

        rows = (
            db.session.query(AccessoriesUpdate)
            .filter(
                AccessoriesUpdate.maintenance_id == record.maintenance_id,
                AccessoriesUpdate.new_accessories_id.isnot(None),
                AccessoriesUpdate.new_accessories_id != "",
            )
            .all()
        )
        if not rows:
            return

        change_date = datetime.now()
        for r in rows:
            db.session.query(EidModel).filter(
                EidModel.eid == r.new_accessories_id
            ).update(
                {
                    "whcd": None,  # 清空仓库，标记已安装
                    "refid": record.maintenance_id,  # 关联单号
                    "gendate": change_date,
                    "opercd": operator,
                },
                synchronize_session=False,
            )

    @staticmethod
    def _scrap_old_part_on_close(record: Any, operator: str) -> None:
        """L5：日常维护单关单时处理旧配件报废（in_wh='2' 的记录）。

        对 TIT25_ACCESSORIES_UPDATE 中 in_wh='2'（不入库=报废）的旧配件：
          - tmm43_eid.sflg = '2'（已报废）
          - refid = maintenance_id
          - gendate = now
          - opercd = operator
          - whcd = NULL（离库）

        in_wh!='2' 的旧配件走 L6 服务返还入库草稿流程（已实现），L5 不重复。

        对齐 PB USP_TRANS_IN_CONFRIM.sql:922-930 operflg='0' 分支：
          set sflg='2', refid=v_id, gendate=sysdate, opercd=v_userid where eid=v_oldeid
        """
        from app.models.itsm import AccessoriesUpdate
        from app.models.master import Eid as EidModel

        rows = (
            db.session.query(AccessoriesUpdate)
            .filter(
                AccessoriesUpdate.maintenance_id == record.maintenance_id,
                AccessoriesUpdate.old_accessories_id.isnot(None),
                AccessoriesUpdate.old_accessories_id != "",
                AccessoriesUpdate.in_wh == "2",  # 仅处理报废标记
            )
            .all()
        )
        if not rows:
            return

        change_date = datetime.now()
        for r in rows:
            db.session.query(EidModel).filter(
                EidModel.eid == r.old_accessories_id
            ).update(
                {
                    "sflg": "2",  # 已报废
                    "refid": record.maintenance_id,
                    "gendate": change_date,
                    "opercd": operator,
                    "whcd": None,  # 离库
                },
                synchronize_session=False,
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
        from app.models.master import Eid as EidModel
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

        # 1a C7：PF×BM_S→OW 映射（设备来源 + 业务模式 → 资产所属）
        # 00商用仓库 + 销售 → 门店资产 OW 03（所有权转客户）
        # 00商用仓库 + 租赁/借用/投放/合作 → 商用电子 OW 01（我们持有）
        # 03IT公司 → 通方信息 OW 02
        # 04海晟 → 海晟 OW 04
        pf_ow_map = {
            "00": {"01": "03", None: "01"},  # 商用仓库: 销售→门店 / 其他→商用电子
            "03": {None: "02"},               # IT公司→通方信息
            "04": {None: "04"},               # 海晟→海晟
        }
        pos_from = plan.pos_from
        eid_val = plan.posid
        if eid_val and pos_from in pf_ow_map:
            business_mode = plan.business_mode
            bm_map = pf_ow_map[pos_from]
            new_owner = bm_map.get(business_mode) or bm_map.get(None) or "01"
            eid_rec = (
                db.session.query(EidModel).filter(EidModel.eid == eid_val).first()
            )
            if eid_rec and eid_rec.asset_owner != new_owner:
                eid_rec.asset_owner = new_owner


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

        # 1a C7：PF×BM_S→OW 映射（旧机翻新，对齐 MO 逻辑）
        from app.models.master import Eid as EidModel

        pf_ow_map = {
            "00": {"01": "03", None: "01"},
            "03": {None: "02"},
            "04": {None: "04"},
        }
        pos_from = plan.pos_from
        eid_val = plan.posid
        if eid_val and pos_from in pf_ow_map:
            business_mode = plan.business_mode
            bm_map = pf_ow_map[pos_from]
            new_owner = bm_map.get(business_mode) or bm_map.get(None) or "01"
            eid_rec = (
                db.session.query(EidModel).filter(EidModel.eid == eid_val).first()
            )
            if eid_rec and eid_rec.asset_owner != new_owner:
                eid_rec.asset_owner = new_owner


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
        # jjbz 字段已废弃（事项 18），保留 PB 数据迁移兼容，不再翻译
        # result = _enrich_sys_codes(result, "jjbz", "ZT")
        # d2d_result 直接用 ZT 字典码值，翻译为状态名称
        result = _enrich_sys_codes(result, "d2d_result", "ZT")
        # closure_reason 用 CLO_REASON 字典翻译（code_typ VARCHAR(10) 限制用短码）
        result = _enrich_sys_codes(result, "closure_reason", "CLO_REASON")
        return result

    @staticmethod
    def get_default_engineer(maintenance_id: str) -> dict[str, Any]:
        """获取上门工程师默认值：最新派工人 → 区域负责人。

        对齐文档 §5.1.1：
        1. 优先取 TIT21_MAINTENANCE_DISPATCH 按 dispatch_time 最新一条的 accpectder
        2. 无派工记录则取工单划区的区域负责人（tmm46_area.usercd）
        3. 都无则返回空，前端兜底取当前登录用户
        """
        from app.models.itsm import MaintenanceDispatch
        from sqlalchemy import desc as sa_desc

        # 1. 最新派工记录的分派人
        latest = (
            db.session.query(MaintenanceDispatch.accpectder)
            .filter(MaintenanceDispatch.maintenance_id == maintenance_id)
            .filter(MaintenanceDispatch.accpectder.isnot(None))
            .order_by(sa_desc(MaintenanceDispatch.dispatch_time))
            .first()
        )
        if latest and latest[0]:
            return {"engineer": latest[0], "source": "latest_dispatch"}

        # 2. 工单划区的区域负责人
        md = MaintenanceDailyRepository.get_by_id(maintenance_id)
        if md and md.store_id:
            customer = db.session.get(Customer, md.store_id)
            if customer and customer.area_cd:
                area = db.session.get(Area, customer.area_cd)
                if area and area.usercd:
                    return {"engineer": area.usercd, "source": "area_manager"}

        return {"engineer": "", "source": "none"}

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = D2DRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(record_id: int, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        """更新上门服务记录。

        审核意见 5 采纳：仅当传入结构化字段时才重新拼句 d2d_descripiton，
        否则保留原值（历史数据保护）。
        """
        record = D2DRepository.get_by_id(record_id)
        if record is None:
            return None

        # 结构化字段存在时重新拼句（历史数据只改其他字段则保留原 d2d_descripiton）
        structured_keys = {"d2d_phenomenon", "d2d_reason", "d2d_handling", "d2d_result", "closure_reason", "d2d_note"}
        if any(k in data for k in structured_keys):
            # 合并已有字段值与新传入值
            phenomenon = data.get("d2d_phenomenon", record.d2d_phenomenon)
            reason = data.get("d2d_reason", record.d2d_reason)
            handling = data.get("d2d_handling", record.d2d_handling)
            d2d_result = data.get("d2d_result", record.d2d_result)
            closure_reason = data.get("closure_reason", record.closure_reason)
            note = data.get("d2d_note", record.d2d_note)

            handling_sentence = D2DService._compose_handling_sentence(
                record.maintenance_id, handling
            )
            result_nm = StateMachine.D2D_RESULT_NM.get(d2d_result or "", "")
            closure_reason_nm = StateMachine.CLOSURE_REASON_NM.get(
                closure_reason or "", ""
            ) if closure_reason else None
            data["d2d_descripiton"] = D2DService._compose_description(
                phenomenon, reason, handling_sentence, result_nm, closure_reason_nm, note
            )

        D2DRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()

    # ------------------------------------------------------------------
    # 离店解决四要素结构化（事项 18）
    # 映射字典统一由 StateMachine 提供（审核意见 11，避免各 Service 重复）
    # ------------------------------------------------------------------
    # 保留类属性引用，向后兼容（内部转调 StateMachine）
    _D2D_RESULT_TO_IS_SUCCESS = StateMachine.D2D_RESULT_TO_IS_SUCCESS
    _CLOSURE_REASON_TO_IS_SUCCESS = StateMachine.CLOSURE_REASON_TO_IS_SUCCESS
    _D2D_RESULT_NM = StateMachine.D2D_RESULT_NM
    _CLOSURE_REASON_NM = StateMachine.CLOSURE_REASON_NM

    @staticmethod
    def _compose_handling_sentence(maintenance_id: str, d2d_handling: str | None) -> str:
        """
        自动拼句处理过程描述。

        来源：
        - TIT25_ACCESSORIES_UPDATE（换件动作 + 收费金额）
        - TWH 领用出库（服务领用，暂不查询，由 TIT25 间接体现）
        - TIT23 到店/催单/记录（次数统计）
        - 工程师手输 d2d_handling（补充）

        Returns:
            拼接后的处理过程文本（≤500 字符）
        """
        parts: list[str] = []

        # 1. 换件动作 + 收费金额（TIT25）
        # 注：TIT25_ACCESSORIES_UPDATE 无 useflg 字段
        accessories = (
            db.session.query(AccessoriesUpdate)
            .filter(
                AccessoriesUpdate.maintenance_id == maintenance_id,
            )
            .all()
        )
        if accessories:
            replace_items = [
                a for a in accessories if a.c_type == "1" and a.old_accessories_id
            ]
            buy_items = [a for a in accessories if a.c_type == "2"]
            service_items = [a for a in accessories if a.c_type == "3"]
            exchange_items = [a for a in accessories if a.c_type == "4"]
            consumable_items = [a for a in accessories if a.c_type == "5"]
            if replace_items:
                parts.append(
                    f"更换配件{len(replace_items)}件（"
                    + "、".join(
                        (a.accessories_type or "") for a in replace_items[:5]
                    )
                    + ("..." if len(replace_items) > 5 else "")
                    + "）"
                )
            if buy_items:
                parts.append(
                    f"购买配件{len(buy_items)}件（"
                    + "、".join(
                        (a.accessories_type or "") for a in buy_items[:5]
                    )
                    + ("..." if len(buy_items) > 5 else "")
                    + "）"
                )
            if exchange_items:
                parts.append(
                    f"整机更换{len(exchange_items)}次（"
                    + "、".join(
                        (a.accessories_type or "") for a in exchange_items[:5]
                    )
                    + ("..." if len(exchange_items) > 5 else "")
                    + "）"
                )
            if service_items:
                svc_types = "、".join(
                    (a.paytype or "") for a in service_items[:5] if a.paytype
                )
                parts.append(
                    f"纯服务费{len(service_items)}项"
                    + (f"（{svc_types}）" if svc_types else "")
                )
            if consumable_items:
                parts.append(
                    f"耗材线材{len(consumable_items)}项（"
                    + "、".join(
                        (a.accessories_type or "") for a in consumable_items[:5]
                    )
                    + ("..." if len(consumable_items) > 5 else "")
                    + "）"
                )
            # 收费金额汇总（所有 c_type 的 price + payje）
            total_charge = sum(
                float(a.price or 0) + float(a.payje or 0) for a in accessories
            )
            if total_charge > 0:
                parts.append(f"收费{total_charge:.2f}元")

        # 2. 到店/催单/记录次数（TIT23）
        d2d_records = (
            db.session.query(MaintenanceD2D)
            .filter(
                MaintenanceD2D.maintenance_id == maintenance_id,
                MaintenanceD2D.useflg == "1",
            )
            .all()
        )
        arrive_count = sum(1 for r in d2d_records if r.d2d_type == "1")
        urge_count = sum(1 for r in d2d_records if r.d2d_type == "3")
        if arrive_count > 0:
            parts.append(f"上门{arrive_count}次")
        if urge_count > 0:
            parts.append(f"催单{urge_count}次")

        # 3. 工程师手输补充
        if d2d_handling:
            parts.append(d2d_handling)

        sentence = "；".join(parts)
        # 截断到 500 字符
        return sentence[:500] if len(sentence) > 500 else sentence

    @staticmethod
    def _compose_description(
        phenomenon: str | None,
        reason: str | None,
        handling_sentence: str,
        result_nm: str,
        closure_reason_nm: str | None,
        note: str | None,
    ) -> str:
        """
        拼接 d2d_descripiton 兼容文本（PB 兼容、列表展示）。

        格式：现象：xxx；原因：xxx；处理：xxx；结果：xxx；补充：xxx
        截断到 200 字符。
        """
        parts: list[str] = []
        if phenomenon:
            parts.append(f"现象：{phenomenon}")
        if reason:
            parts.append(f"原因：{reason}")
        if handling_sentence:
            parts.append(f"处理：{handling_sentence}")
        result_text = result_nm
        if closure_reason_nm:
            result_text = f"{result_nm}（{closure_reason_nm}）"
        parts.append(f"结果：{result_text}")
        if note:
            parts.append(f"补充：{note}")
        sentence = "；".join(parts)
        return sentence[:200] if len(sentence) > 200 else sentence

    # ------------------------------------------------------------------
    # 4 模式差异化（A2a）：到店/离店/催单/记录
    # ------------------------------------------------------------------

    # 主表模型清单（跨单据类型复用 D2D，各自主键字段名不同）
    _MAIN_MODELS: list[tuple[type, str]] = [
        (MaintenanceDaily, "maintenance_id"),        # TIT10 日常维护
        (MaintenanceOpen, "new_opening_id"),          # TIT13 新机开通
        (MaintenanceRenovate, "renew_id"),            # TIT15 旧机翻新
        (DeviceChange, "device_change_id"),           # TIT16 设备变更
        (Maintenance, "daily_maintenance_id"),        # TIT17 日常保养
    ]

    @staticmethod
    def _find_main_record(maintenance_id: str) -> tuple[object | None, str | None]:
        """查询主表记录（兼容多种单据类型）。

        Returns:
            (main_record, fault_type) 或 (None, None)
        """
        for model, pk_field in D2DService._MAIN_MODELS:
            pk_col = getattr(model, pk_field, None)
            if pk_col is None:
                continue
            record = (
                db.session.query(model)
                .filter(pk_col == maintenance_id)
                .first()
            )
            if record is not None:
                fault_type = getattr(record, "fault_type", None)
                return record, fault_type
        return None, None

    @staticmethod
    def _append_faultcode(main_record: object, gzdm: str | None) -> tuple[str | None, str | None]:
        """故障代码回写主表 faultcode（对齐 PB 语义）。

        PB 格式（w_r_itsm_d2d_cdjl.srw）：
            faultcode = archgroup + ',' + gzdm + '/'
        - archgroup: 故障分组（1=整机/2=配件/3=自由录入），从 tit04_archivecode 查
        - gzdm: 故障代码（arch_cd 值）

        去重：完整 entry 已存在则不追加。

        Returns:
            (arch_group, fault_type) 用于责任记录判断
        """
        if not gzdm:
            return None, None
        # 查 arch_group 和 fault_type
        from app.models.itsm import ArchiveCode

        arch = (
            db.session.query(ArchiveCode)
            .filter(ArchiveCode.arch_cd == gzdm)
            .first()
        )
        arch_group = arch.arch_group if arch else "3"  # 默认自由录入
        fault_type = arch.fault_type if arch else None
        entry = f"{arch_group},{gzdm}/"

        current = getattr(main_record, "faultcode", "") or ""
        if entry in current:
            return arch_group, fault_type
        new_faultcode = (current + entry) if current else entry
        setattr(main_record, "faultcode", new_faultcode[:200])
        return arch_group, fault_type

    @staticmethod
    def _get_last_d2d(maintenance_id: str) -> object | None:
        """获取最后一条有效 d2d 记录（按 business_operation_id 倒序）。"""
        return (
            db.session.query(MaintenanceD2D)
            .filter(
                MaintenanceD2D.maintenance_id == maintenance_id,
                MaintenanceD2D.useflg == "1",
            )
            .order_by(MaintenanceD2D.business_operation_id.desc())
            .first()
        )

    @staticmethod
    def _next_d2d_group(maintenance_id: str) -> int:
        """生成下一个 d2d_group（Max+1，对齐 PB of_checkgroup）。"""
        from sqlalchemy import func

        max_group = (
            db.session.query(func.coalesce(func.max(MaintenanceD2D.d2d_group), 0))
            .filter(MaintenanceD2D.maintenance_id == maintenance_id)
            .scalar()
        )
        return int(max_group or 0) + 1

    @staticmethod
    def _check_group(maintenance_id: str, d2d_type: str) -> int | None:
        """分组校验（A2c，对齐 PB of_checkgroup）。

        规则：
        - 到店(1)：上一条不能是到店（否则报错），新分组 = Max(d2d_group)+1
        - 离店(2)：上一条不能是离店（否则报错），用最后一条的 d2d_group
        - 催单(3)：用最后一条的 d2d_group（需离店后才能催单）
        - 记录(4)：用最后一条的 d2d_group（无校验）

        Returns:
            d2d_group 值（到店返回新分组，其他返回最后分组）

        Raises:
            ValueError: 分组校验失败
        """
        last = D2DService._get_last_d2d(maintenance_id)

        if d2d_type == "1":  # 到店
            if last and last.d2d_type == "1":
                raise ValueError("当前分组已记录过到店信息，不能再次添加到店信息")
            return D2DService._next_d2d_group(maintenance_id)

        if d2d_type == "2":  # 离店
            if last is None:
                raise ValueError("当前维护单未记录到店信息，不能添加离店信息")
            if last.d2d_type == "2":
                raise ValueError("当前分组已记录过离店信息，不能再次添加离店信息")
            return last.d2d_group

        if d2d_type == "3":  # 催单
            # 仅阻断：到店未离店（工程师仍在门店现场，无需催单）
            # 无记录 / 最后是离店 / 最后是记录 / 最后是催单 → 均允许
            if last is not None and last.d2d_type == "1":
                raise ValueError("当前到店未离店（工程师仍在门店），不能催单")
            return last.d2d_group if last else D2DService._next_d2d_group(maintenance_id)

        # 记录(4)：用最后分组，无校验
        if last:
            return last.d2d_group
        return D2DService._next_d2d_group(maintenance_id)

    @staticmethod
    def _validate_four_elements(
        maintenance_id: str,
        d2d_result: str | None,
        data: dict[str, Any],
    ) -> None:
        """四要素差异化必填校验（A2c，对齐 §5.3.1）。

        规则：
        - d2d_result='5'(已解决) + 有换件(TIT25 c_type=1/4)：现象/原因/处理/结果全必填
        - d2d_result='5'(已解决) + 无换件：现象/处理/结果必填，原因可放宽
        - d2d_result='3'(关闭)/'4'(未解决)/'6'(转修)/'7'(待配件)：处理/结果必填
        - 到店/催单/记录：不强制（本方法不校验）

        Raises:
            ValueError: 必填字段缺失
        """
        if d2d_result is None:
            return

        phenomenon = data.get("d2d_phenomenon")
        reason = data.get("d2d_reason")
        handling = data.get("d2d_handling")
        note = data.get("d2d_note")

        # 查是否有换件记录（TIT25 c_type=1/4）
        # 注：TIT25_ACCESSORIES_UPDATE 无 useflg 字段，所有记录均视为有效
        has_replace = (
            db.session.query(AccessoriesUpdate)
            .filter(
                AccessoriesUpdate.maintenance_id == maintenance_id,
                AccessoriesUpdate.c_type.in_(["1", "4"]),
            )
            .count()
        ) > 0

        # 处理/结果对所有离店结果必填
        if not handling and not note:
            # handling 或 note 至少填一个（note 作为处理补充）
            raise ValueError("处理过程(d2d_handling)或补充说明(d2d_note)至少填一个")

        if d2d_result == "5":  # 已解决
            if not phenomenon:
                raise ValueError("d2d_result='5' 已解决时实际现象(d2d_phenomenon)必填")
            if has_replace and not reason:
                raise ValueError(
                    "d2d_result='5' 已解决且有换件时原因(d2d_reason)必填"
                )

    @staticmethod
    def _auto_generate_liability(
        maintenance_id: str,
        d2d_result: str | None,
        gzdm: str | None,
        main_fault_type: str | None,
        operator: str,
    ) -> None:
        """责任记录自动生成（A2b，对齐 PB §5.3.3）。

        规则：d2d_result='4'(未解决) 且主表 fault_type='1'(POS 设备类，对齐 PB is_fault_type='1') 时，
        自动插入 TIT10_MAINTENANCE_LIABILITY 责任记录（type='1' 未成功）。

        PB 语义：保内 POS 设备未解决 → 生成责任记录供考核。
        main_fault_type 来自主表 fault_type 字段（设备分类 1=POS/2=视频/3=其他），
        非 ArchiveCode.fault_type（硬件分类前缀如 01=打印机）。
        """
        if d2d_result != "4" or main_fault_type != "1":
            return
        # 查是否已有 type='1' 的责任记录（避免重复）
        from app.models.itsm import MaintenanceLiability

        existing = (
            db.session.query(MaintenanceLiability)
            .filter(
                MaintenanceLiability.maintenance_id == maintenance_id,
                MaintenanceLiability.type == "1",
                MaintenanceLiability.useflg == "1",
            )
            .first()
        )
        if existing is not None:
            return
        # 插入责任记录（type='1' 未成功，is_finish='0' 未处理）
        # exceptions_cd 填 gzdm 保留故障溯源
        liability = MaintenanceLiability(
            maintenance_id=maintenance_id,
            exceptions_cd=gzdm,
            exceptions_nm="保内设备未解决",
            dept_nm="",
            assess_flg="Y",
            exempt_flg="N",
            type="1",
            is_finish="0",
            useflg="1",
            set_from="AUTO_D2D",
        )
        db.session.add(liability)

    @staticmethod
    def _update_main_on_leave(
        maintenance_id: str,
        d2d_result: str | None,
        closure_reason: str | None,
        gzdm: str | None,
        operator: str,
        leave_time: datetime | None,
    ) -> None:
        """离店时联动主表（current_status + is_success + leave_time + firstor/first_time + faultcode）。

        PB 语义修正（P0-1）：
        - 离店不改 current_status，不触发 L1-L11 联动
        - leave_time 若空则填充（第一次离店时间）
        - firstor/first_time 若空则用本次 d2d 工程师/到店时间填充
        - faultcode 追加 gzdm
        - current_status/is_success 由完成维修 transition(5) 时按 TIT23 最新 d2d_result 派生
        """
        main_record, main_fault_type = D2DService._find_main_record(maintenance_id)
        if main_record is None:
            return

        # P0-1 修正：离店不改 current_status，不触发 L1-L11 联动
        # 离店只写 TIT23 + 填充主表 leave_time/firstor/first_time/faultcode
        # 完成维修 transition(5) 才是唯一触发器：改状态 + 读 TIT23 + 触发联动
        # is_success 也不在离店派生（由 transition 时按 d2d_result 派生）

        # leave_time：第一次离店时间（若空才填）
        if leave_time and not getattr(main_record, "leave_time", None):
            main_record.leave_time = leave_time

        # firstor/first_time：若空则查本次上门分组的第一条到店记录填充
        if not getattr(main_record, "firstor", None) or not getattr(main_record, "first_time", None):
            first_arrive = (
                db.session.query(MaintenanceD2D)
                .filter(
                    MaintenanceD2D.maintenance_id == maintenance_id,
                    MaintenanceD2D.d2d_type == "1",  # 到店
                    MaintenanceD2D.useflg == "1",
                )
                .order_by(MaintenanceD2D.arrive_time.asc())
                .first()
            )
            if first_arrive:
                if not getattr(main_record, "firstor", None):
                    main_record.firstor = first_arrive.d2d_engineer
                if not getattr(main_record, "first_time", None):
                    main_record.first_time = first_arrive.arrive_time

        # 故障代码回写主表 faultcode（arch.fault_type 仅用于 faultcode 拼接，不参与责任判断）
        D2DService._append_faultcode(main_record, gzdm)

        # 责任记录自动生成（A2b：d2d_result='4' + 主表 fault_type='1' POS 设备类）
        D2DService._auto_generate_liability(
            maintenance_id, d2d_result, gzdm, main_fault_type, operator
        )

        main_record.update_time = datetime.now(UTC)
        main_record.updator = operator

    @staticmethod
    def arrive_store(
        maintenance_id: str,
        data: dict[str, Any],
        operator: str,
    ) -> dict[str, Any]:
        """到店登记保存（d2d_type='1'）。

        PB 语义（w_r_itsm_d2d.srw）：
        - 记录到店时间、工程师
        - 若主表 firstor/first_time 为空，填充本次到店信息
        - 业务流水（A2b 补）

        Args:
            maintenance_id: 维护单ID
            data: {d2d_engineer, arrive_time, d2d_phone, ...}
            operator: 操作人

        Returns:
            保存后的 d2d 记录 dict
        """
        d2d_data = dict(data)
        d2d_data["d2d_type"] = "1"  # 到店
        d2d_data["maintenance_id"] = maintenance_id
        # 到店时间默认当前
        if not d2d_data.get("arrive_time"):
            d2d_data["arrive_time"] = datetime.now(UTC)
        # 分组校验（A2c）：到店新分组
        d2d_data["d2d_group"] = D2DService._check_group(maintenance_id, "1")
        # 业务流水序号（A2b）
        d2d_data["business_operation_id"] = BusinessFlowService.next_seq(
            maintenance_id, MaintenanceD2D
        )
        record = D2DRepository.create(d2d_data, operator)
        # 业务流水日志（A2b）
        BusinessFlowService.log(
            maintenance_id,
            record.business_operation_id,
            "到店登记",
            operator,
            f"到店: {d2d_data.get('d2d_engineer', '')}",
        )

        # 联动主表：firstor/first_time 若空则填充 + current_status 1→2（到店=已分配）
        main_record, _ = D2DService._find_main_record(maintenance_id)
        if main_record is not None:
            # 到店后主表状态流转为 ASSIGNED(2)，对齐 PB §5.1.2
            if getattr(main_record, "current_status", None) == "1":
                main_record.current_status = "2"
            if not getattr(main_record, "firstor", None):
                main_record.firstor = d2d_data.get("d2d_engineer")
            if not getattr(main_record, "first_time", None):
                main_record.first_time = d2d_data.get("arrive_time")
            main_record.update_time = datetime.now(UTC)
            main_record.updator = operator

        db.session.commit()
        return record.to_dict()

    @staticmethod
    def urge(
        maintenance_id: str,
        data: dict[str, Any],
        operator: str,
    ) -> dict[str, Any]:
        """催单保存（d2d_type='3'）。

        PB 语义（w_r_itsm_d2d.srw of_checkgroup）：
        - 催单只在最后一组 + d2d_type='2' 时同步主表状态
        - 催单本身不直接改主表 current_status（只有离店才改）
        - 业务流水（A2b 补）
        - 分组校验（A2c 补）

        Args:
            maintenance_id: 维护单ID
            data: {d2d_engineer, d2d_descripiton, d2d_phone, ...}
            operator: 操作人

        Returns:
            保存后的 d2d 记录 dict
        """
        d2d_data = dict(data)
        d2d_data["d2d_type"] = "3"  # 催单
        d2d_data["maintenance_id"] = maintenance_id
        # 分组校验（A2c）：催单用最后分组
        d2d_data["d2d_group"] = D2DService._check_group(maintenance_id, "3")
        # 业务流水序号（A2b）
        d2d_data["business_operation_id"] = BusinessFlowService.next_seq(
            maintenance_id, MaintenanceD2D
        )
        record = D2DRepository.create(d2d_data, operator)
        # 业务流水日志（A2b）
        BusinessFlowService.log(
            maintenance_id,
            record.business_operation_id,
            "催单",
            operator,
            d2d_data.get("d2d_descripiton", ""),
        )
        # 催单不直接联动主表状态（A2c 分组校验时再处理）
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def record(
        maintenance_id: str,
        data: dict[str, Any],
        operator: str,
    ) -> dict[str, Any]:
        """记录保存（d2d_type='4'，到场说明/客户反馈）。

        PB 语义：仅业务流水，不联动主表。

        Args:
            maintenance_id: 维护单ID
            data: {d2d_engineer, d2d_descripiton, d2d_phone, ...}
            operator: 操作人

        Returns:
            保存后的 d2d 记录 dict
        """
        d2d_data = dict(data)
        d2d_data["d2d_type"] = "4"  # 记录
        d2d_data["maintenance_id"] = maintenance_id
        # 分组校验（A2c）：记录用最后分组
        d2d_data["d2d_group"] = D2DService._check_group(maintenance_id, "4")
        # 业务流水序号（A2b）
        d2d_data["business_operation_id"] = BusinessFlowService.next_seq(
            maintenance_id, MaintenanceD2D
        )
        record = D2DRepository.create(d2d_data, operator)
        # 业务流水日志（A2b）
        BusinessFlowService.log(
            maintenance_id,
            record.business_operation_id,
            "记录",
            operator,
            d2d_data.get("d2d_descripiton", ""),
        )
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def leave_store(
        maintenance_id: str,
        data: dict[str, Any],
        operator: str,
    ) -> dict[str, Any]:
        """
        离店登记保存（四要素结构化 + 自动拼句 + 主表联动）。

        Args:
            maintenance_id: 维护单ID
            data: 四要素字段 {d2d_phenomenon, d2d_reason, d2d_handling,
                             d2d_result, closure_reason, d2d_note,
                             gzdm, device_id, accessories_id, ...}
            operator: 操作人

        Returns:
            保存后的 d2d 记录 dict

        联动主表（A2a 补全）：
            - current_status = d2d_result
            - is_success 按 d2d_result/closure_reason 映射派生（StateMachine）
            - leave_time 若空则填充（第一次离店时间）
            - firstor/first_time 若空则查到店记录填充
            - faultcode 追加 gzdm
        """
        d2d_result = data.get("d2d_result")
        closure_reason = data.get("closure_reason")
        gzdm = data.get("gzdm")

        # 校验：d2d_result='3' 时 closure_reason 必填
        if d2d_result == "3" and not closure_reason:
            raise ValueError("d2d_result='3' 关闭时 closure_reason 必填")

        # 四要素差异化必填校验（A2c）
        D2DService._validate_four_elements(maintenance_id, d2d_result, data)

        # 自动拼句：处理过程
        handling_sentence = D2DService._compose_handling_sentence(
            maintenance_id, data.get("d2d_handling")
        )

        # 拼句：d2d_descripiton 兼容文本（用 StateMachine 字典）
        result_nm = StateMachine.D2D_RESULT_NM.get(d2d_result or "", "")
        closure_reason_nm = StateMachine.CLOSURE_REASON_NM.get(
            closure_reason or "", ""
        ) if closure_reason else None
        description = D2DService._compose_description(
            data.get("d2d_phenomenon"),
            data.get("d2d_reason"),
            handling_sentence,
            result_nm,
            closure_reason_nm,
            data.get("d2d_note"),
        )

        # 离店时间默认当前
        leave_time = data.get("leave_time") or datetime.now(UTC)

        # 写入 d2d 记录
        d2d_data = dict(data)
        d2d_data["d2d_descripiton"] = description
        d2d_data["d2d_type"] = "2"  # 离店
        d2d_data["leave_time"] = leave_time
        d2d_data["maintenance_id"] = maintenance_id
        # 分组校验（A2c）：离店用最后分组
        d2d_data["d2d_group"] = D2DService._check_group(maintenance_id, "2")
        # 业务流水序号（A2b）
        d2d_data["business_operation_id"] = BusinessFlowService.next_seq(
            maintenance_id, MaintenanceD2D
        )
        record = D2DRepository.create(d2d_data, operator)
        # 业务流水日志（A2b）
        BusinessFlowService.log(
            maintenance_id,
            record.business_operation_id,
            "离店登记",
            operator,
            f"离店: {result_nm}{('（' + closure_reason_nm + '）') if closure_reason_nm else ''}",
        )

        # 联动主表（A2a 补全：leave_time/firstor/first_time/faultcode）
        D2DService._update_main_on_leave(
            maintenance_id, d2d_result, closure_reason, gzdm, operator, leave_time
        )

        # POS 状态同步（A2c 事件驱动）：发 d2d_leave_store 事件，监听器同步 TMM22_CUSTOMERS
        main_record, _ = D2DService._find_main_record(maintenance_id)
        if main_record is not None:
            custcd = getattr(main_record, "custcd", None)
            if custcd:
                EventBus.emit(
                    "d2d_leave_store",
                    {
                        "maintenance_id": maintenance_id,
                        "custcd": custcd,
                        "posstatus": data.get("posstatus", "01"),
                        "posstatus1": data.get("posstatus1", "11"),
                    },
                )

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
        # c_type 用 C_TYPE 字典翻译（1维修/2购买/3纯服务费/4整机更换/5耗材线材）
        result = _enrich_sys_codes(result, "c_type", "C_TYPE")
        # paytype 按 c_type 级联翻译：c_type=3 用 PAY_SVC，c_type=5 用 PAY_CONS
        for r in result:
            ct = r.get("c_type", "")
            pt = r.get("paytype", "")
            if ct == "3" and pt:
                r["paytype_nm"] = _get_sys_code_nm("PAY_SVC", pt)
            elif ct == "5" and pt:
                r["paytype_nm"] = _get_sys_code_nm("PAY_CONS", pt)
        return result

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        # c_type=4 整机更换：后端自动设 posflg=1（更换整机标志，对齐 §6.1.2）
        if data.get("c_type") == "4":
            data["posflg"] = "1"
        record = AccessoriesUpdateRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def get_new_accessories_candidates(
        engineer_id: str, accessories_type: str | None = None
    ) -> list[dict[str, Any]]:
        """查询新配件可选列表（默认仓 + 当前工程师虚拟仓，双来源）。

        对齐 §6.5.3：
        - 默认仓：defaultflg='Y'，sflg='8'（在库可用），etyp='0'（配件类）
        - 工程师虚拟仓：按 engineer_id 查用户名 → 匹配 twh01_warehouse.whnm（C5 已去前缀），
          sflg='1'（工程师持有），etyp='0'
        - accessories_type 非空时按 itemcd 前两位过滤
        """
        from app.models.warehouse import Warehouse

        # 1. 默认仓在库配件
        default_q = (
            db.session.query(Eid)
            .join(Warehouse, Eid.whcd == Warehouse.whcd)
            .filter(
                Warehouse.defaultflg == "Y",
                Warehouse.useflg == "1",
                Eid.useflg == "1",
                Eid.sflg == "8",
                Eid.etyp == "0",
            )
        )
        # 2. 当前工程师虚拟仓持有配件
        # 优先用 User.default_whcd（C5 FK），名字匹配兜底
        engineer_whcd: str | None = None
        if engineer_id:
            user = db.session.query(User).filter(User.user_cd == engineer_id).first()
            if user:
                if getattr(user, "default_whcd", None):
                    engineer_whcd = user.default_whcd
                elif user.user_nm:
                    wh = (
                        db.session.query(Warehouse)
                        .filter(Warehouse.whnm == user.user_nm, Warehouse.useflg == "1")
                        .first()
                    )
                    if wh:
                        engineer_whcd = wh.whcd
        engineer_q = (
            db.session.query(Eid)
            .filter(
                Eid.useflg == "1",
                Eid.sflg == "1",
                Eid.etyp == "0",
            )
        )
        if engineer_whcd:
            engineer_q = engineer_q.filter(Eid.whcd == engineer_whcd)
        else:
            engineer_q = engineer_q.filter(db.false())  # 无工程师仓则空集

        # 合并
        rows = default_q.union(engineer_q).all()
        # 按配件类型过滤（itemcd 前两位）
        if accessories_type:
            prefix = accessories_type[:2]
            rows = [r for r in rows if (r.itemcd or "").startswith(prefix)]
        return [
            {
                "eid": r.eid,
                "itemcd": r.itemcd,
                "whcd": r.whcd,
                "sflg": r.sflg,
                "source": "engineer" if r.sflg == "1" else "default",
            }
            for r in rows
        ]

    @staticmethod
    def get_old_accessories_candidates(store_id: str) -> list[dict[str, Any]]:
        """查询门店有效配件资产（旧配件来源，对齐 §6.5.4）。

        从 tmm35_cust_pos_rl 按门店查资产，useflg='1' 且 asset_status='ACTIVE'。
        """
        rows = (
            db.session.query(CustPosRl)
            .filter(
                CustPosRl.custcd == store_id,
                CustPosRl.useflg == "1",
            )
            .all()
        )
        return [
            {
                "eid": r.eid,
                "itemcd": r.item_cd,
                "asset_type": getattr(r, "asset_type", None),
                "useflg": r.useflg,
            }
            for r in rows
        ]

    @staticmethod
    def update(record_id: int, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        """更新配件更新记录（乐观锁，审核意见 7）。

        客户端须传入 version 字段（当前版本号），若与数据库不一致则拒绝更新。
        """
        record = AccessoriesUpdateRepository.get_by_id(record_id)
        if record is None:
            return None

        # 乐观锁校验
        client_version = data.pop("version", None)
        if client_version is not None and int(client_version) != record.version:
            raise ValueError(
                f"记录已被其他用户修改（当前版本 {record.version}，"
                f"客户端版本 {client_version}），请刷新后重试"
            )

        # version +1
        data["version"] = record.version + 1
        # c_type=4 整机更换：后端自动设 posflg=1（对齐 §6.1.2）
        if data.get("c_type") == "4":
            data["posflg"] = "1"
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
                        "notify_channel": getattr(matched, "notify_channel", None) or "internal",
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
                        "notify_channel": getattr(matched, "notify_channel", None) or "internal",
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
                        "notify_channel": getattr(matched, "notify_channel", None) or "internal",
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
    def send_notification(
        record_id: int,
        channel: str = "internal",
        subject: str | None = None,
        body: str | None = None,
        operator: str = "system",
        template_id: str | None = None,
    ) -> dict[str, Any] | None:
        """按派工记录发送通知：渲染模板，创建 Notification 并发送。

        Args:
            record_id: 派工记录ID
            channel: 通知渠道（internal/email/sms/dingtalk/wecom/feishu/ntfy）
            subject: 自定义标题（空=用模板渲染）
            body: 自定义正文（空=用模板渲染）
            operator: 操作人
            template_id: 指定模板ID（空=用 dispatch 业务类型默认模板）
        """
        record = DispatchRepository.get_by_id(record_id)
        if record is None:
            return None
        from jinja2 import Template
        from app.models.itsm import MaintenanceDaily
        from app.models.notification import NotificationTemplate
        from app.repositories.notification_repository import (
            NotificationRepository,
            NotificationTemplateRepository,
        )
        from app.services.notification_service import NotificationService

        # 选择模板：指定 > dispatch 默认 > DISPATCH 兼容
        tpl = None
        if template_id:
            tpl = db.session.get(NotificationTemplate, template_id)
        if tpl is None:
            tpl = NotificationTemplateRepository.find_default("dispatch")
        if tpl is None:
            tpl = db.session.get(NotificationTemplate, "DISPATCH")
        if tpl is None:
            return None
        # 模板已停用则报错（避免静默用无效模板）
        if tpl.useflg != "1":
            raise ValueError(f"通知模板 {tpl.template_id} 已停用，无法发送")
        # 取维护单+客户上下文
        mnt = db.session.query(MaintenanceDaily).filter(
            MaintenanceDaily.maintenance_id == record.maintenance_id
        ).first()
        store_id = mnt.store_id if mnt else None
        fault_type = mnt.fault_type if mnt else None
        context = DispatchService._build_notify_context(record, store_id, fault_type)
        final_subject = subject or Template(tpl.subject or "").render(**context)
        final_body = body or Template(tpl.body or "").render(**context)
        # 创建通知并发送
        # dispatch_id 直接使用派工的 business_operation_id（跨表共享流水号）
        seq_no = record.business_operation_id
        notif = NotificationRepository.create(
            {
                "template_id": tpl.template_id,
                "channel": channel,
                "recipient": context["accpectder"],
                "subject": final_subject,
                "body": final_body,
                "ref_type": "dispatch",
                "ref_id": str(record.maintenance_id),
                "dispatch_id": seq_no,
                "send_status": "pending",
            },
            operator,
        )
        db.session.commit()
        result = NotificationService.send(notif.id)
        return result

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
            # 创建通知快照（与派工同事务，按规则渠道渲染模板）
            notify_channel = target.get("notify_channel") or "internal"
            DispatchService._create_notification(record, store_id, fault_type, creator, channel=notify_channel)
            db.session.commit()
            # 自动派工自动发送通知（按规则配置渠道）
            try:
                from app.repositories.notification_repository import NotificationRepository as _NR
                notif = _NR.find_latest_by_dispatch(getattr(record, "id", None))
                if notif is not None:
                    from app.services.notification_service import NotificationService
                    NotificationService.send(notif.id)
            except Exception as ne:
                logger.warning(f"自动派工通知发送失败 maintenance_id={maintenance_id}: {ne}")
            logger.info(
                f"自动派单成功：maintenance_id={maintenance_id}, "
                f"accpectder={target['accpectder']}, rule_id={target.get('rule_id')}, "
                f"channel={notify_channel}"
            )
            return record.to_dict()
        except Exception as e:
            db.session.rollback()
            logger.warning(f"自动派单失败 maintenance_id={maintenance_id}: {e}")
            return None

    @staticmethod
    def _build_notify_context(record: Any, store_id: str | None, fault_type: str | None) -> dict[str, Any]:
        """构建派工通知模板渲染上下文（对齐维护单+客户+派工字段）。"""
        from app.models.master import Customer, Area
        from app.models.itsm import MaintenanceDaily

        mnt = db.session.query(MaintenanceDaily).filter(
            MaintenanceDaily.maintenance_id == record.maintenance_id
        ).first()
        # 客户/门店信息
        cust_card = ""
        cust_nm = ""
        address = ""
        phone_no = ""
        contactor = ""
        area_cd = ""
        area_nm = ""
        company_id = ""
        if store_id:
            cust = db.session.query(Customer).filter(Customer.cust_cd == store_id).first()
            if cust:
                cust_card = cust.cust_card or ""
                cust_nm = cust.cust_nm or ""
                address = cust.address or ""
                phone_no = cust.phone_no or ""
                contactor = cust.contactor or ""
                area_cd = cust.area_cd or ""
                company_id = getattr(cust, "company_id", "") or ""
                if area_cd:
                    area = db.session.query(Area).filter(Area.area_cd == area_cd).first()
                    area_nm = area.area_nm if area else ""
        # 分派人姓名
        accpectder = record.accpectder or ""
        accpectder_name = accpectder
        if accpectder:
            user = db.session.query(User).filter(User.user_cd == accpectder).first()
            if user and user.user_nm:
                accpectder_name = user.user_nm
        # 故障类型名称
        fault_type_nm = ""
        if fault_type:
            from app.models.master import SysCode
            sc = db.session.query(SysCode).filter(
                SysCode.code_typ == "GZ", SysCode.code_cd == fault_type
            ).first()
            if sc:
                fault_type_nm = sc.code_nm or ""
        # 状态名称
        current_status = getattr(mnt, "current_status", "") or ""
        current_status_nm = ""
        if current_status:
            from app.models.master import SysCode as _SC
            st = db.session.query(_SC).filter(
                _SC.code_typ == "ZT", _SC.code_cd == current_status
            ).first()
            if st:
                current_status_nm = st.code_nm or ""
        return {
            "maintenance_id": record.maintenance_id,
            "store_id": store_id or "",
            "cust_card": cust_card,
            "cust_nm": cust_nm,
            "address": address,
            "phone_no": phone_no,
            "contactor": contactor,
            "comm_mode": getattr(cust, "comm_mode", "") if cust else "",
            "class_cd": getattr(cust, "class_cd", "") if cust else "",
            "accpectder": accpectder,
            "accpectder_name": accpectder_name,
            "accpectder_nm": accpectder_name,
            "accpectd_group": record.accpectd_group or "",
            "fault_type": fault_type or "",
            "fault_type_nm": fault_type_nm,
            "short_description": getattr(mnt, "short_description", "") or "",
            "detail_description": getattr(mnt, "detail_description", "") or "",
            "device_id": getattr(mnt, "device_id", "") or "",
            "request_time": str(getattr(mnt, "request_time", "") or ""),
            "current_status": current_status,
            "current_status_nm": current_status_nm,
            "emergency_level": getattr(mnt, "emergency_level", "") or "",
            "requester": getattr(mnt, "requester", "") or "",
            "expected_completion_time": str(getattr(mnt, "expected_completion_time", "") or ""),
            "operator": getattr(record, "operator", "") or "",
            "operator_nm": user.user_nm if (user := db.session.query(User).filter(User.user_cd == getattr(record, "operator", "")).first()) else "",
            "dispatch_time": str(getattr(record, "dispatch_time", "") or ""),
            "business_operation_id": str(getattr(record, "business_operation_id", "") or ""),
            "area_cd": area_cd,
            "area_nm": area_nm,
        }

    @staticmethod
    def _create_notification(
        record: Any,
        store_id: str | None,
        fault_type: str | None,
        creator: str,
        channel: str = "internal",
        template_id: str | None = None,
    ) -> None:
        """派工创建时一次性渲染通知模板写入通知快照。

        模板渲染采用 Jinja2，占位符一次性替换后落库，后续不再重渲染。
        若指定 template_id 则用该模板，否则用 dispatch 业务类型默认模板。
        """
        import logging
        from jinja2 import Template

        from app.models.notification import NotificationTemplate
        from app.repositories.notification_repository import (
            NotificationRepository,
            NotificationTemplateRepository,
        )

        logger = logging.getLogger(__name__)
        try:
            # 选择模板：指定 > dispatch 默认 > DISPATCH 兼容
            tpl = None
            if template_id:
                tpl = db.session.get(NotificationTemplate, template_id)
            if tpl is None:
                tpl = NotificationTemplateRepository.find_default("dispatch")
            if tpl is None:
                tpl = db.session.get(NotificationTemplate, "DISPATCH")
            if tpl is None:
                logger.warning("派工通知模板未配置，跳过通知创建")
                return
            if tpl.useflg != "1":
                logger.warning(f"通知模板 {tpl.template_id} 已停用，跳过通知创建")
                return
            context = DispatchService._build_notify_context(record, store_id, fault_type)
            subject = Template(tpl.subject or "").render(**context)
            body = Template(tpl.body or "").render(**context)
            NotificationRepository.create(
                {
                    "template_id": tpl.template_id,
                    "channel": channel,
                    "recipient": context["accpectder"],
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


class ArchiveCodeService:
    """故障代码字典服务（TIT04_ARCHIVECODE，A3 故障代码选择器用）。

    支持：
    - 按 arch_group（故障分组 1=整机/2=配件/3=自由录入）过滤
    - 按 fault_type（设备分类前缀如 01=打印机）过滤
    - 按 parent 查子级（级联用）
    """

    @staticmethod
    def list(
        arch_group: str | None = None,
        fault_type: str | None = None,
        parent: str | None = None,
        keyword: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """查询故障代码字典（支持过滤+关键字搜索）。

        Args:
            arch_group: 故障分组过滤（1/2/3）
            fault_type: 故障类型前缀过滤（如 "01"）
            parent: 父级编码过滤（级联用，默认查顶层 parent='%' 或 useflg='1'）
            keyword: arch_cd/arch_nm 模糊搜索
            limit: 返回条数上限
        """
        from app.models.itsm import ArchiveCode

        q = db.session.query(ArchiveCode).filter(ArchiveCode.useflg == "1")
        if arch_group:
            q = q.filter(ArchiveCode.arch_group == arch_group)
        if fault_type:
            q = q.filter(ArchiveCode.fault_type.like(f"{fault_type}%"))
        if parent:
            q = q.filter(ArchiveCode.parent == parent)
        if keyword:
            kw = f"%{keyword}%"
            q = q.filter(
                db.or_(ArchiveCode.arch_cd.like(kw), ArchiveCode.arch_nm.like(kw))
            )
        q = q.order_by(ArchiveCode.arch_cd).limit(limit)
        return [r.to_dict() for r in q.all()]


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
