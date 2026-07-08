"""ITSM 核心业务服务层（状态机集成）。"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.extensions import db
from app.models.master import Customer
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
    """为维护单记录补充 store_cust_card（从 tmm22_customers 关联查询）。"""
    ids = {r.get(key) for r in items if r.get(key)}
    if not ids:
        return items
    cards = dict(
        db.session.query(Customer.cust_cd, Customer.cust_card)
        .filter(Customer.cust_cd.in_(ids))
        .all()
    )
    for r in items:
        sid = r.get(key)
        if sid and sid in cards:
            r["store_cust_card"] = cards[sid]
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
        return record.to_dict()

    @staticmethod
    def list_records(
        status: str | None = None,
        store_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = MaintenanceDailyRepository.list_by_filters(
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
        record = MaintenanceDailyRepository.create(data, creator)
        db.session.commit()
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
                EidModel.asset_owner != "01",
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
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = MaintenanceOpenRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

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
        return record.to_dict()

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
        if not eid_rec or eid_rec.asset_owner == "01":
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
    """设备变更单业务服务（含P0-4磁卡号历史优化）。"""

    @staticmethod
    def get(change_id: str) -> dict[str, Any] | None:
        record = DeviceChangeRepository.get_by_id(change_id)
        if record is None:
            return None
        return record.to_dict()

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
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = DeviceChangeRepository.create(data, creator)
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
                f"设备变更单 {record.device_change_id} 关单，设备从 "
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
        return record.to_dict()

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
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = StoreCloseRepository.create(data, creator)
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
                EidModel.asset_owner != "01",
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
# 公用附表服务
# ---------------------------------------------------------------------------


class D2DService:
    """上门服务记录服务（公用附表 TIT23）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = D2DRepository.list_by_maintenance_id(maintenance_id)
        return [item.to_dict() for item in items]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = D2DRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()


class RVService:
    """客户回访服务（公用附表 TIT24）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = RVRepository.list_by_maintenance_id(maintenance_id)
        return [item.to_dict() for item in items]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = RVRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()


class AccessoriesUpdateService:
    """配件更新服务（TIT25）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = AccessoriesUpdateRepository.list_by_maintenance_id(maintenance_id)
        return [item.to_dict() for item in items]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = AccessoriesUpdateRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()


class CloseBillService:
    """关单服务（TIT27）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = CloseBillRepository.list_by_maintenance_id(maintenance_id)
        return [item.to_dict() for item in items]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = CloseBillRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()


class DispatchService:
    """分派服务（TIT21）。"""

    @staticmethod
    def list_by_maintenance_id(maintenance_id: str) -> list[dict[str, Any]]:
        items = DispatchRepository.list_by_maintenance_id(maintenance_id)
        return [item.to_dict() for item in items]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = DispatchRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()


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
        return record.to_dict()

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
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = RecycleTaskRepository.create(data, creator)
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
                EidModel.asset_owner != "01",
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
        return record.to_dict()

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


class FreeReplaceService(_BaseMaintenanceService):
    """免费更换工单服务（TIT28_FREE_REPLACE）。"""

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
        return [item.to_dict() for item in items]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = PayListRepository.create(data, creator)
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
