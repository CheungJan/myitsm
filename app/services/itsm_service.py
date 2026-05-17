"""ITSM 核心业务服务层（状态机集成）。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.extensions import db
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
        return {
            "items": [item.to_dict() for item in items],
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
            db.session.commit()
        return result


class MaintenanceOpenService(_BaseMaintenanceService):
    """新机开通单业务服务。"""

    @staticmethod
    def get(opening_id: str) -> dict[str, Any] | None:
        record = MaintenanceOpenRepository.get_by_id(opening_id)
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
            db.session.commit()
        return result


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
            db.session.commit()
        return result


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
            if to_status == "5" and record.change_type == "CK":
                DeviceChangeRepository.save_customer_history(
                    {
                        "cust_cd": record.store_id or "",
                        "change_type": "CK",
                        "old_value": record.new_store_card,
                        "new_value": record.new_store_card,
                        "oper_cd": operator,
                    }
                )
            db.session.commit()

        return result


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
            db.session.commit()
        return result


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
        db.session.commit()
        return {"success": True, "from_status": from_status, "to_status": to_status}

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
        return {
            "items": [item.to_dict() for item in items],
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
        result = self._do_transition(
            record, to_status, operator, remark, pk_field="maintenance_id"
        )
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
        return {
            "items": [item.to_dict() for item in items],
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
            FreeReplaceRepository.add_detail(
                renew_id=record.renew_id, data=detail_data
            )
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

        result = self._do_transition(
            record, to_status, operator, remark, pk_field="renew_id"
        )

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
