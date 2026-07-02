"""销售管理业务服务层。

优化方案1/3/4：预计划 plantyp 路由自动生成下游 ITSM 单据 +
客户生命周期管理 + 作废级联事务保护。
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.extensions import db
from app.models.master import CustClass, Customer
from app.repositories.sales_repository import (
    PlanCustRepository,
    PlanServeRepository,
    SalesBillRepository,
    SalesExtendRepository,
)
from app.services.customer_service import CustomerService

logger = logging.getLogger(__name__)


def _normalize_class_cd(custcd: str) -> str:
    """将销售单据中的 custcd 转为 tmm21_custclass.class_cd 格式（2位编号）。"""
    if not custcd:
        return ""
    s = custcd.strip()
    try:
        return str(int(s)).zfill(2)
    except ValueError:
        return s


def _enrich_class_nm(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """为销售记录补充 class_nm（从 tmm21_custclass 关联查询）。"""
    cds = {_normalize_class_cd(r.get("custcd", "")) for r in items if r.get("custcd")}
    cds.discard("")
    if not cds:
        return items
    names = dict(
        db.session.query(CustClass.class_cd, CustClass.class_nm)
        .filter(CustClass.class_cd.in_(cds))
        .all()
    )
    for r in items:
        cd = _normalize_class_cd(r.get("custcd", ""))
        if cd and cd in names:
            r["class_nm"] = names[cd]
    return items


# ============================================================================
# PlanStatus 状态机
# ============================================================================


class PlanStatus(str, Enum):
    """预计划状态码（对齐 PB tmm31_syscodes codetyp='TS'）。

    PB 码表定义：00=计划中 01=计划完成 02=分派中 03=实施完成
    04=实施中 08=计划退回 09=计划作废。
    """

    PLANNING = "00"  # 计划中
    COMPLETED = "01"  # 计划完成（呼出确认+实施完成）
    DISPATCHING = "02"  # 分派中
    IMPL_DONE = "03"  # 实施完成（下游单据已生成）
    IMPLEMENTING = "04"  # 实施中
    RETURNED = "08"  # 计划退回
    VOIDED = "09"  # 计划作废

    @classmethod
    def from_code(cls, code: str) -> "PlanStatus | None":
        """从码值获取枚举，兼容 1 位/2 位码。"""
        s = str(code).strip().zfill(2)
        mapping = {m.value: m for m in cls}
        return mapping.get(s)

    @property
    def display_name(self) -> str:
        names: dict[str, str] = {
            "00": "计划中",
            "01": "计划完成",
            "02": "分派中",
            "03": "实施完成",
            "04": "实施中",
            "08": "计划退回",
            "09": "计划作废",
        }
        return names.get(self.value, self.value)


class PlanStatusMachine:
    """预计划状态机 —— 对齐 PB TS 码表流转。"""

    TRANSITIONS: dict[PlanStatus, list[PlanStatus]] = {
        PlanStatus.PLANNING: [PlanStatus.COMPLETED, PlanStatus.DISPATCHING, PlanStatus.VOIDED],
        PlanStatus.COMPLETED: [PlanStatus.DISPATCHING, PlanStatus.VOIDED],
        PlanStatus.DISPATCHING: [
            PlanStatus.IMPL_DONE,
            PlanStatus.IMPLEMENTING,
            PlanStatus.RETURNED,
            PlanStatus.VOIDED,
        ],
        PlanStatus.IMPL_DONE: [PlanStatus.IMPLEMENTING, PlanStatus.COMPLETED],
        PlanStatus.IMPLEMENTING: [
            PlanStatus.IMPL_DONE,
            PlanStatus.COMPLETED,
            PlanStatus.RETURNED,
            PlanStatus.VOIDED,
        ],
        PlanStatus.RETURNED: [PlanStatus.PLANNING, PlanStatus.VOIDED],
    }
    TERMINAL_STATES: set[PlanStatus] = {
        PlanStatus.COMPLETED,
        PlanStatus.VOIDED,
    }

    @classmethod
    def can_transition(cls, from_state: PlanStatus, to_state: PlanStatus) -> bool:
        """检查流转是否合法。"""
        allowed = cls.TRANSITIONS.get(from_state, [])
        return to_state in allowed

    @classmethod
    def get_allowed_transitions(cls, from_code: str) -> list[str]:
        """获取当前状态下允许流转的目标状态码列表。"""
        current = PlanStatus.from_code(from_code)
        if current is None:
            return []
        allowed = cls.TRANSITIONS.get(current, [])
        return [s.value for s in allowed]

    @classmethod
    def is_terminal(cls, code: str) -> bool:
        """是否为终态。"""
        state = PlanStatus.from_code(code)
        if state is None:
            return False
        return state in cls.TERMINAL_STATES

    @classmethod
    def validate_transition(cls, from_code: str, to_code: str) -> dict[str, object]:
        """校验状态流转，返回结构化结果。"""
        from_state = PlanStatus.from_code(from_code)
        to_state = PlanStatus.from_code(to_code)
        if from_state is None:
            return {"valid": False, "error": f"无效的当前状态码: {from_code}"}
        if to_state is None:
            return {"valid": False, "error": f"无效的目标状态码: {to_code}"}
        if cls.is_terminal(from_code):
            return {
                "valid": False,
                "error": f"终态（{from_state.display_name}）不可再流转",
                "allowed_transitions": [],
            }
        if not cls.can_transition(from_state, to_state):
            allowed = cls.get_allowed_transitions(from_code)
            return {
                "valid": False,
                "error": (
                    f"不允许从 {from_state.display_name}({from_code}) "
                    f"流转到 {to_state.display_name}({to_code})"
                ),
                "allowed_transitions": allowed,
            }
        return {
            "valid": True,
            "from_state": from_code,
            "to_state": to_code,
        }


# ============================================================================
# plantyp → ITSM 下游单据路由
# ============================================================================

# 延迟导入，避免循环依赖
_PLANTYP_SERVICE_MAP: dict[str, tuple[str, str]] = {
    "00": ("MaintenanceOpenService", "new_opening_id"),  # 新机开通 → TIT13
    "10": ("DeviceChangeService", "device_change_id"),  # 设备变更 → TIT16
    "20": ("MaintenanceRenovateService", "renew_id"),  # 旧机翻新 → TIT15
    "30": ("RecycleTaskService", "recycle_id"),  # 取机回收 → TIT20
    "40": ("StoreCloseService", "store_close_id"),  # 门店关闭 → TIT18
}

# plantyp 到下游 ITSM Repository 的映射（用于 void 级联操作）
_PLANTYP_REPO_MAP: dict[str, str] = {
    "00": "MaintenanceOpenRepository",
    "10": "DeviceChangeRepository",
    "20": "MaintenanceRenovateRepository",
    "30": "RecycleTaskRepository",
    "40": "StoreCloseRepository",
}


def _get_downstream_info(plantyp: str) -> tuple[str, str] | None:
    """根据 plantyp 获取 (Service类名, 主键字段名) 或 None。"""
    return _PLANTYP_SERVICE_MAP.get(plantyp)


def _call_downstream_service(plantyp: str, data: dict[str, Any], creator: str) -> dict[str, Any]:
    """调用对应 ITSM Service.create() 创建下游单据草稿。

    返回 {"id": "xxx", "label": "xxx"}，异常时抛出。
    """
    info = _get_downstream_info(plantyp)
    if info is None:
        raise ValueError(f"未知的计划类型 plantyp={plantyp}")

    svc_name, pk_field = info
    # 动态导入 ITSM Service（避免启动时循环依赖）
    from app.services import itsm_service as _itsm

    svc = getattr(_itsm, svc_name)
    result = svc.create(data, creator)
    downstream_id = result.get(pk_field, "")
    return {"id": downstream_id, "label": svc_name, "pk_field": pk_field}


def _build_downstream_payload(record: Any, plantyp: str, creator: str) -> dict[str, Any]:
    """根据预计划记录构建下游 ITSM 单据的创建数据。"""
    base: dict[str, Any] = {}

    if plantyp == "00":  # 新机开通
        base.update(
            {
                "store_id": record.custcd or "",
                "device_id": record.posid or "",
                "from_custcard": record.custcard or "",
                "from_custcd": record.custcd or "",
                "count": 1,
            }
        )
    elif plantyp == "10":  # 磁卡号变更（含三种子类型）
        # CK=仅磁卡号变更, BG=磁卡号+设备变更, BQ=信息变更
        has_card_change = bool((record.new_custcard or "").strip())
        has_device_change = bool((record.new_posid or "").strip())
        if has_device_change:
            change_type = "BG"  # 磁卡号+设备同时变更
        elif has_card_change:
            change_type = "CK"  # 仅磁卡号变更
        else:
            change_type = "BQ"  # 信息变更（地址/电话/联系人等）
        base.update(
            {
                "store_id": record.custcd or "",
                "change_type": change_type,
                "new_store_card": record.new_custcard or "",
                "new_store_id": record.new_custcd or "",
                "device_id": record.new_posid or None,
            }
        )
    elif plantyp == "20":  # 旧机翻新
        base.update(
            {
                "store_id": record.custcd or "",
                "old_device_id": record.posid or "",
            }
        )
    elif plantyp == "30":  # 取机回收
        base.update(
            {
                "cust_cd": record.custcd or "",
                "plan_no": record.planno,
                "recycle_type": plantyp,
            }
        )
    elif plantyp == "40":  # 门店关闭
        base.update(
            {
                "store_id": record.custcd or "",
            }
        )

    return base


def _cascade_void_downstream(plantyp: str, downstream_id: str, operator: str) -> None:
    """级联作废下游 ITSM 单据草稿，已审核/已完成则阻止。"""
    repo_name = _PLANTYP_REPO_MAP.get(plantyp)
    if repo_name is None:
        return

    from app.repositories import itsm_repository as _itsm_repo

    repo = getattr(_itsm_repo, repo_name)
    record = repo.get_by_id(downstream_id)
    if record is None:
        return  # 下游已删除，无需处理

    # 30=RecycleTask 使用 task_status，其他 ITSM 单据使用 current_status
    if plantyp == "30":
        current_status = getattr(record, "task_status", "1")
    else:
        current_status = getattr(record, "current_status", "1")

    # 已终态（已完成/已关闭）不可作废
    if str(current_status) in ("3", "5", "9"):
        raise ValueError(
            f"下游单据 {downstream_id} 已终态（status={current_status}），不可级联作废"
        )

    # 标记作废
    if plantyp == "30":
        setattr(record, "task_status", "9")
    else:
        setattr(record, "current_status", "9")
    setattr(record, "updator", operator)
    setattr(record, "update_time", datetime.now(UTC))


# ============================================================================
# PlanCustService（核心改造）
# ============================================================================


class PlanCustService:
    """预计划服务 —— 按 PB 流程编排：计划中→呼出确认→实施生成下游→出库完成。"""

    @staticmethod
    def get(planno: str) -> dict[str, Any] | None:
        record = PlanCustRepository.get_by_id(planno)
        if record is None:
            return None
        data = record.to_dict()
        if record.custcd:
            cust = db.session.get(Customer, record.custcd)
            data["customer_status"] = cust.customer_status if cust else None
        return data

    @staticmethod
    def list_records(
        plantyp: str | None = None,
        plan_status: str | None = None,
        custcd: str | None = None,
        planno: str | None = None,
        custnm: str | None = None,
        custcard: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        serve_status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PlanCustRepository.list_by_filters(
            plantyp=plantyp,
            plan_status=plan_status,
            custcd=custcd,
            planno=planno,
            custnm=custnm,
            custcard=custcard,
            date_from=date_from,
            date_to=date_to,
            serve_status=serve_status,
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
        """创建预计划（plan_status=00 计划中）。

        仅做两件事：
        1. 磁卡号唯一性检查 + 创建预计划记录
        2. 客户生命周期：创建 TEMP 客户（如果提供了客户信息）
        下游 ITSM 单据在 implement() 阶段才生成。
        """
        # 过滤 Schema 中的非模型字段（call_serve/serve_task 仅在保存时通过 PlanServe 服务处理）
        model_data = {k: v for k, v in data.items() if k not in ("call_serve", "serve_task")}

        # 磁卡号唯一性检查
        custcard = model_data.get("custcard")
        if custcard:
            existing_customer = CustomerService.check_card_exists(custcard)
            if existing_customer:
                return {
                    "success": False,
                    "error": (
                        f"磁卡号 {custcard} 已被客户 "
                        f"{existing_customer.cust_nm or existing_customer.cust_cd} 使用"
                    ),
                }
            existing_plan = PlanCustRepository.find_by_custcard(custcard)
            if existing_plan:
                return {
                    "success": False,
                    "error": f"磁卡号 {custcard} 已存在于预计划 {existing_plan.planno}",
                }

        # 方案 A 预占检查：posid 已选时校验 EID 是否已被其他计划预占
        posid = model_data.get("posid")
        if posid:
            from app.models.master import Eid as _Eid

            eid_rec = db.session.query(_Eid).filter(_Eid.eid == posid).first()
            if eid_rec and eid_rec.reserve_planno:
                return {
                    "success": False,
                    "error": f"EID {posid} 已被预计划 {eid_rec.reserve_planno} 预占",
                }

        # 创建预计划（plan_status=00 计划中）
        record = PlanCustRepository.create(model_data, creator)

        # 呼出（PlanServe）为可选辅助流程，对齐 PB 设计：
        # - PB 中需用户手动点击「请求呼出」按钮 + 勾选复选框才生成呼出单
        # - 不自动创建 PlanServe，仅当用户显式勾选 call_serve 时才创建
        plantyp = data.get("plantyp")

        # PB cbx_serve 勾选:生成 servetyp=1 预计划呼出单,并更新 serve_status=01
        if data.get("call_serve"):
            PlanServeRepository.create(
                {
                    "planno": record.planno,
                    "plantyp": plantyp,
                    "servetyp": "1",
                    "serve_task": data.get("serve_task") or f"预计划呼出-{record.planno}",
                    "commmode": data.get("commmode"),
                },
                creator,
            )
            record.serve_status = "01"

        # 客户生命周期：创建 TEMP 客户
        custcd = data.get("custcd")
        if custcd:
            try:
                CustomerService.create_temp_customer(
                    data={
                        "custcd": custcd,
                        "custnm": data.get("custnm"),
                        "custcard": custcard,
                        "busityp": data.get("busityp"),
                        "address": data.get("address"),
                        "contactor": data.get("contactor"),
                        "phoneno": data.get("phoneno"),
                    },
                    preplan_id=record.planno,
                    creator=creator,
                )
            except Exception as exc:
                db.session.rollback()
                return {"success": False, "error": f"创建临时客户失败: {exc}"}

        # 方案 A 预占：posid 已选时锁定 EID（reserve_planno=planno）
        if posid:
            from app.models.master import Eid as _Eid

            eid_rec = db.session.query(_Eid).filter(_Eid.eid == posid).first()
            if eid_rec:
                eid_rec.reserve_planno = record.planno

        db.session.commit()

        # 库存不足自动触发采购需求(pos_from=00 商用仓库,不限 plantyp)
        PlanCustService._try_trigger_procurement(record, data, creator)

        result = record.to_dict()
        result["success"] = True
        return result

    @staticmethod
    def _try_trigger_procurement(record: Any, data: dict[str, Any], operator: str) -> None:
        """库存不足自动触发采购需求(仅 pos_from=00 商用仓库)。

        供 create() 和 update() 共用。条件放宽为不限 plantyp,
        翻新(20)/关门(40)等选商用仓库时同样需要采购备货。
        """
        pos_from = (data.get("pos_from") or getattr(record, "pos_from", "") or "").strip()
        pos_item = (data.get("pos_item") or getattr(record, "pos_item", "") or "").strip()
        if pos_from != "00" or not pos_item:
            return
        try:
            from app.services.plan_stock_service import PlanStockService

            stock = PlanStockService.check_stock(pos_item)
            if stock.get("total_qty", 0) <= 0:
                proc_result = PlanStockService.trigger_procurement(
                    planno=record.planno,
                    model_cd=pos_item,
                    qty=1,
                    operator=operator,
                )
                if proc_result.get("pcplanid"):
                    logger.info(
                        "预计划 %s 库存不足,已触发采购需求 %s",
                        record.planno,
                        proc_result["pcplanid"],
                    )
        except Exception:
            logger.exception("预计划 %s 触发采购需求失败", record.planno)

    @staticmethod
    def implement(
        planno: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        """实施确认：按 plantyp 生成下游 ITSM 单据 + 写押金 + 客户 TEMP→PENDING。

        前置条件：plan_status 必须为 '02'（分派中）。
        幂等校验：已生成过则拒绝。
        通过 ITSM Repository 直接创建（不经过 Service 的独立 commit），
        保证与客户状态推进在同一事务内。
        """
        record = PlanCustRepository.get_by_id(planno)
        if record is None:
            return {"success": False, "error": "预计划不存在"}

        current = record.plan_status or "00"
        if current != "02":
            return {
                "success": False,
                "error": f"预计划状态为 {current}，需要 02（分派中）才能实施",
            }

        plantyp = record.plantyp
        if not plantyp or plantyp not in _PLANTYP_SERVICE_MAP:
            return {"success": False, "error": f"未知的计划类型 plantyp={plantyp}"}

        # 注：呼出（PlanServe）为可选辅助流程，非 implement() 前置条件（对齐 PB 设计）
        # 幂等检查
        if record.imple_billid:
            return {
                "success": False,
                "error": f"下游单据已生成（{record.imple_billid}），不可重复实施",
            }

        # plantyp 路由 → 通过 ITSM Repository 直接创建（同一事务）
        repo_name = _PLANTYP_REPO_MAP.get(plantyp)
        downstream_id = None
        try:
            from app.repositories import itsm_repository as _itsm_repo

            repo = getattr(_itsm_repo, repo_name)
            payload = _build_downstream_payload(record, plantyp, operator)
            ds_record = repo.create(payload, operator)
            pk_field = _PLANTYP_SERVICE_MAP[plantyp][1]
            downstream_id = getattr(ds_record, pk_field, "")
        except Exception as exc:
            db.session.rollback()
            return {"success": False, "error": f"创建下游单据失败: {exc}"}

        if not downstream_id:
            db.session.rollback()
            return {"success": False, "error": "下游单据创建成功但未获取到ID"}

        # 回写下游单据 ID
        record.imple_billid = downstream_id

        # 押金联动
        deposit_amount = record.deposit
        if deposit_amount and float(deposit_amount) != 0 and record.custcd:
            try:
                from app.services.deposit_service import DepositDetailService

                DepositDetailService.create(
                    {
                        "custcd": record.custcd,
                        "c_type": "预计划押金",
                        "change_a": float(deposit_amount),
                        "new_a": float(deposit_amount),
                        "r_billid": record.planno,
                        "remark": f"预计划 {record.planno} 实施确认",
                    }
                )
            except Exception as exc:
                logger.warning("押金写入失败 planno=%s: %s", planno, exc)

        # 状态流转：02（分派中）→ 04（实施中）
        # 对齐 PB status='04'（分派中/实施中），complete() 和 create_outbound() 前置要求 04
        record.plan_status = "04"

        # 方案 A 自动出库：posid 已选时自动创建 OV=1 出库单（带 posid EID）
        if record.posid:
            try:
                from app.models.master import Eid as _EidAuto

                eid_rec = db.session.query(_EidAuto).filter(_EidAuto.eid == record.posid).first()
                eid_whcd = eid_rec.whcd if eid_rec else ""
                PlanCustService.create_outbound(
                    planno=planno,
                    whcd=eid_whcd or "",
                    operator=operator,
                    eids=[record.posid],
                )
            except Exception as exc:
                logger.warning("方案 A 自动出库失败 planno=%s: %s", planno, exc)

        # 客户：TEMP → PENDING
        if record.custcd:
            CustomerService.promote_to_pending(record.custcd)

        db.session.commit()
        return {
            "success": True,
            "planno": planno,
            "to_status": "04",
            "downstream_id": downstream_id,
        }

    @staticmethod
    def complete(
        planno: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        """完成预计划：设备出库后调用，客户 PENDING→ACTIVE。

        前置条件：plan_status='04'（实施中）。
        """
        record = PlanCustRepository.get_by_id(planno)
        if record is None:
            return {"success": False, "error": "预计划不存在"}

        current = record.plan_status or "00"
        if current != "04":
            return {
                "success": False,
                "error": f"预计划状态为 {current}，需要 04（实施中）才能完成",
            }

        # 状态：04 → 01（计划完成）
        record.plan_status = "01"

        # 客户：PENDING → ACTIVE
        if record.custcd:
            CustomerService.promote_to_active(record.custcd, operator)

        # 客户无效化联动（对齐 usp_plan_confrim cust_useflg 分支）
        PlanCustService._apply_cust_useflg_invalidation(record, operator)

        # 写 tmm43_eid_track type='u'（状态变更：设备已销售 → 计划完成配置生效）
        # 对齐 PB 配置确认步骤，refid=出库单号
        PlanCustService._write_eid_track_on_complete(record, operator)

        db.session.commit()
        return {"success": True, "planno": planno, "to_status": "01"}

    @staticmethod
    def _write_eid_track_on_complete(record: Any, operator: str) -> None:
        """计划完成时写 tmm43_eid_track type='u' 记录。

        从关联的 OV=1 销售出库单明细取 EID 列表，对每个 EID 写一条
        type='u' 记录，refid=出库单号，记录"配置已确认生效"。
        """
        from app.models.warehouse import StockOut, StockOutDetailEid
        from app.repositories.system_repository import SystemRepository

        outbillid = (
            db.session.query(StockOut.outbillid)
            .filter(
                StockOut.refbillid == record.planno,
                StockOut.invtyp == "1",
                StockOut.auditflg == "2",
            )
            .scalar()
        )
        if not outbillid:
            return

        eid_rows = (
            db.session.query(StockOutDetailEid.eid, StockOutDetailEid.itemcd)
            .filter(StockOutDetailEid.outbillid == outbillid)
            .all()
        )
        for row in eid_rows:
            if not row.eid or not row.itemcd:
                continue
            SystemRepository.create_eid_track(
                eid=row.eid,
                itemcd=row.itemcd,
                track_type="u",
                operator=operator,
                refid=outbillid,
                sflg="S",  # 变更前：已销售
                n_sflg="S",  # 变更后：仍为已销售（配置生效不改 sflg）
                remark=f"预计划 {record.planno} 配置确认生效",
            )

    @staticmethod
    def _apply_cust_useflg_invalidation(record: Any, operator: str) -> None:
        """计划完成时按 cust_useflg 处理客户无效化（对齐 PB usp_plan_confrim）。

        - plantyp='10' 磁卡号变更/移机：源门店（new_custcd）无条件失效（无移机时 new_custcd 为空，自动跳过）。
        - plantyp in ('00','20') 开通/翻新移机：勾选 cust_useflg='1' 时，移出源门店（new_custcd）失效。
        - plantyp='30' 取机：勾选 cust_useflg='1' 时，取机门店本身（custcd）失效。
        - plantyp='40' 门店关闭：从下游 StoreClose 单据取 close_type，联动 s_status 与名称前缀。
        """
        plantyp = (record.plantyp or "").strip()
        cust_useflg = (record.cust_useflg or "").strip()
        new_custcd = (record.new_custcd or "").strip()

        if plantyp == "10":
            if new_custcd:
                CustomerService.invalidate_store_customer(new_custcd, operator)
        elif plantyp in ("00", "20"):
            if cust_useflg == "1" and new_custcd:
                CustomerService.invalidate_store_customer(new_custcd, operator)
        elif plantyp == "30":
            if cust_useflg == "1" and record.custcd:
                CustomerService.invalidate_store_customer(record.custcd, operator)
        elif plantyp == "40":
            # 门店关闭：从下游 StoreClose 取 close_type 联动 s_status（对齐 usp_plan_confrim GB 分支）
            downstream_id = (record.imple_billid or "").strip()
            if downstream_id and record.custcd:
                from app.repositories.itsm_repository import StoreCloseRepository

                store_close = StoreCloseRepository.get_by_id(downstream_id)
                close_type = store_close.close_type if store_close else None
                CustomerService.set_store_close_status(record.custcd, close_type, operator)

    @staticmethod
    def update(planno: str, data: dict[str, Any], operator: str = "") -> dict[str, Any] | None:
        """更新预计划 —— 含磁卡号变更自动记录与 Customer 同步。"""
        record = PlanCustRepository.get_by_id(planno)
        if record is None:
            return None

        # 磁卡号变更检测：custcard 字段变化时同步 Customer 表
        old_custcard = record.custcard
        new_custcard = data.get("custcard")
        if new_custcard is not None and new_custcard != old_custcard:
            # 检查新磁卡号是否冲突
            existing = CustomerService.check_card_exists(new_custcard)
            if existing:
                return {
                    "success": False,
                    "error": (
                        f"磁卡号 {new_custcard} 已被客户 "
                        f"{existing.cust_nm or existing.cust_cd} 使用"
                    ),
                }
            # 更新预计划记录
            record.new_custcard = new_custcard
            # 同步 Customer 表
            if record.custcd:
                CustomerService.update_customer_card(record.custcd, new_custcard)

        # 批量 setattr 剩余字段
        PlanCustRepository.update(record, data)
        db.session.commit()

        # 库存不足自动触发采购需求(先保存草稿、后续才选机型场景)
        PlanCustService._try_trigger_procurement(record, data, operator=operator)

        result = record.to_dict()
        result["success"] = True
        return result

    @staticmethod
    def transition(
        planno: str,
        to_status: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        """预计划状态流转 —— 含状态机校验 + 客户生命周期推进。

        业务动作绑定：
        - 00→02（分派中/呼出完成）：客户 TEMP → PENDING
        - 04→01（计划完成/设备出库）：客户 PENDING → ACTIVE
        其他流转仅校验状态机规则。
        """
        record = PlanCustRepository.get_by_id(planno)
        if record is None:
            return {"success": False, "error": "预计划不存在"}

        from_status = record.plan_status or "00"

        # 状态机校验
        validation = PlanStatusMachine.validate_transition(from_status, to_status)
        if not validation.get("valid"):
            return {"success": False, "error": str(validation.get("error", "状态流转校验失败"))}

        # 业务推进
        # 02（分派中/呼出完成）：客户 TEMP → PENDING
        if to_status == "02" and record.custcd:
            # 防并发：有进行中的呼出单（status='00'）时阻止确认（对齐 PB u_plan_befor line 487-491）
            from app.models.sales import PlanServe as _PS

            pending_serve = (
                db.session.query(_PS)
                .filter(_PS.planno == planno, _PS.status == "00")
                .count()
            )
            if pending_serve > 0:
                return {
                    "success": False,
                    "error": "该预计划有未完成的呼出单，请先完成或作废呼出单",
                }
            CustomerService.promote_to_pending(record.custcd)

        # 01（计划完成/设备出库）：客户 PENDING → ACTIVE
        if to_status == "01" and record.custcd:
            CustomerService.promote_to_active(record.custcd, operator)
            # 客户无效化联动（对齐 usp_plan_confrim cust_useflg 分支）
            PlanCustService._apply_cust_useflg_invalidation(record, operator)

        record.plan_status = to_status
        db.session.commit()
        return {
            "success": True,
            "from_status": from_status,
            "to_status": to_status,
            "allowed_next": PlanStatusMachine.get_allowed_transitions(to_status),
        }

    @staticmethod
    def void(
        planno: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        """作废预计划 —— 级联作废下游草稿 + 客户失效。

        规则：
        - 计划完成(01) 不可作废
        - 下游单据已终态（status=3/5/9）则阻止
        - 下游草稿 → 标记作废
        - 客户 TEMP/PENDING → INVALID
        """
        record = PlanCustRepository.get_by_id(planno)
        if record is None:
            return {"success": False, "error": "预计划不存在"}

        current_status = record.plan_status or "00"

        # 终态不可作废
        if current_status == "01":
            return {"success": False, "error": "已完成的预计划不可作废"}
        if current_status == "09":
            return {"success": False, "error": "预计划已作废"}

        # 级联作废下游 ITSM 草稿
        plantyp = record.plantyp
        # 下游单据 ID（implement() 写入 imple_billid）
        downstream_id = record.imple_billid
        if downstream_id and plantyp and plantyp in _PLANTYP_REPO_MAP:
            try:
                _cascade_void_downstream(plantyp, downstream_id, operator)
            except ValueError as exc:
                return {"success": False, "error": str(exc)}

        # 客户生命周期：TEMP/PENDING → INVALID
        if record.custcd:
            CustomerService.invalidate_customer(record.custcd, operator)

        # 作废预计划自身
        record.plan_status = "09"
        if remark:
            record.plan_require = ((record.plan_require or "") + f" [作废: {remark}]")[:200]

        # 方案 A：作废时释放 EID 预占
        if record.posid:
            from app.models.master import Eid as _EidVoid

            db.session.query(_EidVoid).filter(
                _EidVoid.eid == record.posid,
                _EidVoid.reserve_planno == planno,
            ).update({"reserve_planno": None}, synchronize_session=False)

        db.session.commit()

        return {"success": True, "planno": planno, "to_status": "09"}

    @staticmethod
    def create_outbound(
        planno: str,
        whcd: str,
        operator: str,
        eids: list[str] | None = None,
    ) -> dict[str, object]:
        """生成 OV=1 销售出库草稿 —— 仓库实施部领机时调用。

        前置条件：plan_status='04'（实施中）。
        创建 OV=1 草稿（refbillid=planno），仓库人工审核后出库。

        参数 eids：可选 EID 列表。
          - 方案 A（预绑定）：预计划已选 posid，此处传 [posid] 自动带出库明细
          - 方案 B（发货时绑定）：仓库人选 N 台 EID 传入，写出库明细
          - 不传 eids：创建空草稿，仓库人审核前在出库单页面补充明细
        """
        record = PlanCustRepository.get_by_id(planno)
        if record is None:
            return {"success": False, "error": "预计划不存在"}

        current = record.plan_status or "00"
        if current != "04":
            return {
                "success": False,
                "error": f"预计划状态为 {current}，需要 04（实施中）才能生成出库单",
            }

        # 去重检查
        from app.models.warehouse import StockOut

        existing = (
            db.session.query(StockOut)
            .filter(
                StockOut.refbillid == planno,
                StockOut.invtyp == "1",
                StockOut.auditflg != "V",
            )
            .first()
        )
        if existing:
            return {
                "success": False,
                "error": f"已存在出库单 {existing.outbillid}",
            }

        # 方案 A：预计划已选 posid 且未传 eids，自动带出
        if not eids and record.posid:
            eids = [record.posid]

        # 构造出库 EID 明细
        details_eid: list[dict[str, Any]] = []
        if eids:
            from app.models.master import Eid as EidModel

            for eid in eids:
                eid_rec = db.session.query(EidModel).filter(EidModel.eid == eid).first()
                if eid_rec is None:
                    return {"success": False, "error": f"EID {eid} 不存在"}
                if not eid_rec.itemcd:
                    return {"success": False, "error": f"EID {eid} 无机型信息"}
                details_eid.append(
                    {
                        "eid": eid,
                        "itemcd": eid_rec.itemcd,
                        "outqty": 1,
                    }
                )

        # 创建 OV=1 销售出库草稿
        from app.services.warehouse_service import StockOutService

        out_data: dict[str, Any] = {
            "invtyp": "1",
            "whcd": whcd,
            "refbillid": planno,
            "memo": f"预计划 {planno} 销售出库",
        }
        result = StockOutService.create(
            data=out_data,
            details_eid=details_eid if details_eid else None,
            creator=operator,
        )
        if not result.get("success") and result.get("error"):
            return {"success": False, "error": str(result["error"])}

        outbillid = result.get("outbillid", "")
        # 记录出库单号到预计划
        record.is_outflag = "1"

        db.session.commit()
        return {
            "success": True,
            "planno": planno,
            "outbillid": outbillid,
            "eid_count": len(details_eid),
        }


# ============================================================================
# PlanServeService（呼出单）
# ============================================================================


class PlanServeService:
    """呼出单服务 —— 话务台呼出客户确认安装意向并收集反馈。"""

    @staticmethod
    def get(dtlid: int) -> dict[str, Any] | None:
        record = PlanServeRepository.get_by_id(dtlid)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_by_plan(planno: str) -> list[dict[str, Any]]:
        items = PlanServeRepository.list_by_plan(planno)
        return [item.to_dict() for item in items]

    @staticmethod
    def list_records(
        planno: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PlanServeRepository.list_by_filters(
            planno=planno, status=status, page=page, per_page=per_page
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = PlanServeRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def transition(dtlid: int, to_status: str, operator: str) -> dict[str, object]:
        """呼出单状态流转：00待呼出→01已呼出→09作废。"""
        record = PlanServeRepository.get_by_id(dtlid)
        if record is None:
            return {"success": False, "error": "呼出单不存在"}

        allowed: dict[str, list[str]] = {
            "00": ["01", "09"],
            "01": ["09"],
        }
        current = record.status or "00"
        if to_status not in allowed.get(current, []):
            return {
                "success": False,
                "error": f"不允许从 {current} 流转到 {to_status}",
            }

        PlanServeRepository.update_status(record, to_status)
        db.session.commit()
        return {"success": True, "dtlid": dtlid, "to_status": to_status}


# ============================================================================
# SalesBillService（保持不变）
# ============================================================================


class SalesBillService:
    """销售单据服务。"""

    @staticmethod
    def get(slbillid: str) -> dict[str, Any] | None:
        record = SalesBillRepository.get_by_id(slbillid)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_records(
        sltyp: str | None = None,
        custcd: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = SalesBillRepository.list_by_filters(
            sltyp=sltyp, custcd=custcd, auditflg=auditflg, page=page, per_page=per_page
        )
        enriched = _enrich_class_nm([item.to_dict() for item in items])
        return {
            "items": enriched,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = SalesBillRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def audit(slbillid: str, auditor: str) -> dict[str, object]:
        record = SalesBillRepository.get_by_id(slbillid)
        if record is None:
            return {"success": False, "error": "销售单不存在"}
        if record.auditflg == "1":
            return {"success": False, "error": "已审核"}
        SalesBillRepository.audit(record, auditor)
        db.session.commit()
        return {"success": True, "slbillid": record.slbillid}


# ============================================================================
# SalesExtendService（保持不变）
# ============================================================================


class SalesExtendService:
    """延期服务。"""

    @staticmethod
    def get(opbillid: str) -> dict[str, Any] | None:
        record = SalesExtendRepository.get_by_id(opbillid)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        return result

    @staticmethod
    def list_records(
        custcd: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = SalesExtendRepository.list_by_filters(
            custcd=custcd, auditflg=auditflg, page=page, per_page=per_page
        )
        enriched = _enrich_class_nm([item.to_dict() for item in items])
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
        record = SalesExtendRepository.create(data, creator)
        for detail_data in details:
            SalesExtendRepository.add_detail(opbillid=record.opbillid, data=detail_data)
        db.session.commit()
        return record.to_dict()
