"""销售管理业务服务层。

优化方案1/3/4：预计划 plantyp 路由自动生成下游 ITSM 单据 +
客户生命周期管理 + 作废级联事务保护。
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.extensions import db
from app.models.master import CustClass
from app.repositories.sales_repository import (
    PlanCustRepository,
    SalesBillRepository,
    SalesExtendRepository,
)
from app.services.customer_service import CustomerService


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
    """预计划状态码（对齐 PB plan_cust.status 字段，2位码）。

    PB 原值分布：00=计划中 01=已确认 02=实施中 04=已完成 09=作废。
    plan_cust.plan_status 在 PB 中存储呼出结果(N/Y/O)，我们统一简化：
    plan_status 即工作流状态，呼出结果放 PLAN_SERVE.serve_back。
    """

    PLANNING = "00"  # 计划中（初始）
    CONFIRMED = "01"  # 已确认（呼出完成）
    IMPLEMENTING = "02"  # 实施中（实施计划已制定）
    COMPLETED = "04"  # 已完成（设备出库 + 客户转正）
    VOIDED = "09"  # 已作废

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
            "01": "已确认",
            "02": "实施中",
            "04": "已完成",
            "09": "已作废",
        }
        return names.get(self.value, self.value)


class PlanStatusMachine:
    """预计划状态机 —— 对齐 PB 实际状态流转。"""

    TRANSITIONS: dict[PlanStatus, list[PlanStatus]] = {
        PlanStatus.PLANNING: [PlanStatus.CONFIRMED, PlanStatus.VOIDED],
        PlanStatus.CONFIRMED: [PlanStatus.IMPLEMENTING, PlanStatus.VOIDED],
        PlanStatus.IMPLEMENTING: [PlanStatus.COMPLETED, PlanStatus.VOIDED],
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
                "open_type": record.busityp or "1",
                "from_custcard": record.custcard or "",
                "from_custcd": record.custcd or "",
                "count": 1,
            }
        )
    elif plantyp == "10":  # 设备变更
        base.update(
            {
                "store_id": record.custcd or "",
                "change_type": "BG",
                "new_store_card": record.new_custcard or "",
                "new_store_id": record.new_custcd or "",
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
        return record.to_dict()

    @staticmethod
    def list_records(
        plantyp: str | None = None,
        plan_status: str | None = None,
        custcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PlanCustRepository.list_by_filters(
            plantyp=plantyp,
            plan_status=plan_status,
            custcd=custcd,
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
        # 磁卡号唯一性检查
        custcard = data.get("custcard")
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

        # 创建预计划（plan_status=00 计划中）
        record = PlanCustRepository.create(data, creator)

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

        db.session.commit()
        result = record.to_dict()
        result["success"] = True
        return result

    @staticmethod
    def implement(
        planno: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        """实施确认：按 plantyp 生成下游 ITSM 单据 + 写押金 + 客户 TEMP→PENDING。

        前置条件：plan_status 必须为 '01'（已确认/呼出完成）。
        幂等校验：已生成过则拒绝。
        """
        record = PlanCustRepository.get_by_id(planno)
        if record is None:
            return {"success": False, "error": "预计划不存在"}

        current = record.plan_status or "00"
        if current != "01":
            return {
                "success": False,
                "error": f"预计划状态为 {current}，需要 01（已确认）才能实施",
            }

        plantyp = record.plantyp
        if not plantyp or plantyp not in _PLANTYP_SERVICE_MAP:
            return {"success": False, "error": f"未知的计划类型 plantyp={plantyp}"}

        # 幂等检查
        if record.imple_status:
            return {
                "success": False,
                "error": f"下游单据已生成（{record.imple_status}），不可重复实施",
            }

        # plantyp 路由 → 生成下游 ITSM 单据
        downstream_id = None
        try:
            payload = _build_downstream_payload(record, plantyp, operator)
            ds_result = _call_downstream_service(plantyp, payload, operator)
            downstream_id = ds_result.get("id")
        except Exception as exc:
            db.session.rollback()
            return {"success": False, "error": f"创建下游单据失败: {exc}"}

        # 回写下游单据 ID 到预计划
        record.imple_status = downstream_id

        # 状态流转：01（已确认）→ 02（实施中）
        record.plan_status = "02"

        # 客户：TEMP → PENDING
        if record.custcd:
            CustomerService.promote_to_pending(record.custcd)

        db.session.commit()
        return {
            "success": True,
            "planno": planno,
            "to_status": "02",
            "downstream_id": downstream_id,
        }

    @staticmethod
    def complete(
        planno: str,
        operator: str,
        remark: str | None = None,
    ) -> dict[str, object]:
        """完成预计划：设备出库后调用，客户 PENDING→ACTIVE。

        前置条件：plan_status='02'（实施中）。
        """
        record = PlanCustRepository.get_by_id(planno)
        if record is None:
            return {"success": False, "error": "预计划不存在"}

        current = record.plan_status or "00"
        if current != "02":
            return {
                "success": False,
                "error": f"预计划状态为 {current}，需要 02（实施中）才能完成",
            }

        # 状态：02 → 04
        record.plan_status = "04"

        # 客户：PENDING → ACTIVE
        if record.custcd:
            CustomerService.promote_to_active(record.custcd, operator)

        db.session.commit()
        return {"success": True, "planno": planno, "to_status": "04"}

    @staticmethod
    def update(planno: str, data: dict[str, Any]) -> dict[str, Any] | None:
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
        - 00→01（呼出完成）：客户 TEMP → PENDING
        - 02→04（设备出库）：客户 PENDING → ACTIVE
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
        # 01（已确认/呼出完成）：客户 TEMP → PENDING
        if to_status == "01" and record.custcd:
            CustomerService.promote_to_pending(record.custcd)

        # 04（已完成/设备出库）：客户 PENDING → ACTIVE
        if to_status == "04" and record.custcd:
            CustomerService.promote_to_active(record.custcd, operator)

        record.plan_status = to_status
        db.session.commit()
        return {
            "success": True,
            "from_status": from_status,
            "to_status": to_status,
            "allowed_next": PlanStatusMachine.get_allowed_transitions(to_status),
        }
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
        - COMPLETED(03) 不可作废，IMPLEMENTING(02) 需先回退
        - 下游单据已终态（status=3/5/9）则阻止
        - 下游草稿 → 标记作废
        - 客户 TEMP/PENDING → INVALID
        """
        record = PlanCustRepository.get_by_id(planno)
        if record is None:
            return {"success": False, "error": "预计划不存在"}

        current_status = record.plan_status or "00"

        # 终态不可作废
        if current_status == "04":
            return {"success": False, "error": "已完成的预计划不可作废"}
        if current_status == "09":
            return {"success": False, "error": "预计划已作废"}

        # 级联作废下游 ITSM 草稿
        plantyp = record.plantyp
        # 下游单据 ID 存储在 imple_status 字段中（由 create 时写入）
        downstream_id = record.imple_status
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
        db.session.commit()

        return {"success": True, "planno": planno, "to_status": "09"}


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
