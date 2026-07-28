"""业务流水独立服务（审核意见 12 采纳）。

对齐 PB gf_insert_business / UF_INSERT_BUSINESS 功能：
- 为子表（d2d/配件/收费/领用/派工等）生成 business_operation_id 序号
- 序号按 maintenance_id 维度递增（per maintenance_id）
- 记录操作日志（operation_name/operator/operate_decription）

重构中 TIT20_BUSINESS_OPERATION 表未建独立模型，business_operation_id 作为
各子表内的序号字段存在。本服务统一封装序号生成逻辑，避免各 Service 重复实现。

使用方式：
    seq = BusinessFlowService.next_seq(maintenance_id)
    # 写入子表 business_operation_id = seq
    BusinessFlowService.log(maintenance_id, seq, "离店登记", operator, "离店: 已解决")
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func

from app.extensions import db


class BusinessFlowService:
    """业务流水服务（统一 business_operation_id 序号生成 + 操作日志）。"""

    @staticmethod
    def next_seq(maintenance_id: str, model_cls: type | None = None) -> int:
        """获取下一个 business_operation_id 序号。

        按 maintenance_id 维度递增。PB 语义：同一维护单内，各子表共享序号空间。

        Args:
            maintenance_id: 维护单ID
            model_cls: 子表模型类（如 MaintenanceD2D/AccessoriesUpdate/MaintenanceDispatch）
                      若指定，则查该表当前最大序号+1；否则查所有子表最大值+1

        Returns:
            下一个序号（int，≥1）
        """
        if not maintenance_id:
            return 1

        max_seq = 0

        if model_cls is not None:
            # 查指定子表最大序号
            row = (
                db.session.query(func.max(model_cls.business_operation_id))
                .filter(model_cls.maintenance_id == maintenance_id)
                .scalar()
            )
            max_seq = int(row or 0)
        else:
            # 查所有子表最大序号（共享序号空间，对齐 PB）
            from app.models.itsm import (
                MaintenanceD2D,
                AccessoriesUpdate,
                MaintenanceDispatch,
                CloseBill,
                MaintenanceRV,
            )
            for cls in (
                MaintenanceD2D,
                AccessoriesUpdate,
                MaintenanceDispatch,
                CloseBill,
                MaintenanceRV,
            ):
                row = (
                    db.session.query(func.max(cls.business_operation_id))
                    .filter(cls.maintenance_id == maintenance_id)
                    .scalar()
                )
                seq = int(row or 0)
                if seq > max_seq:
                    max_seq = seq

        return max_seq + 1

    @staticmethod
    def log(
        maintenance_id: str,
        seq: int,
        operation_name: str,
        operator: str,
        description: str = "",
    ) -> dict[str, Any]:
        """记录业务操作日志（对齐 PB TIT20_BUSINESS_OPERATION）。

        重构中未建独立流水表，日志暂记入 notification 或 audit log。
        后续若建 TIT20_BUSINESS_OPERATION 表，在此插入记录。

        Args:
            maintenance_id: 维护单ID
            seq: business_operation_id 序号
            operation_name: 操作名称（如"离店登记"/"配件更换"/"派工"）
            operator: 操作人
            description: 操作描述

        Returns:
            日志记录 dict（maintenance_id/seq/operation_name/operator/description/timestamp）
        """
        # TODO: 若后续建 tit20_business_operation 表，在此插入记录
        # 当前阶段：返回 dict 供调用方记录到 audit log 或 notification
        return {
            "maintenance_id": maintenance_id,
            "business_operation_id": seq,
            "operation_name": operation_name,
            "operator": operator,
            "operate_decription": description,
            "operate_time": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def append_description(
        maintenance_id: str,
        seq: int,
        model_cls: type,
        append_text: str,
        operator: str,
    ) -> None:
        """追加操作描述（对齐 PB UF_UPDATE_BUSINESS）。

        PB 语义：同一 business_operation_id 的描述可追加，不覆盖。
        重构中子表 description 字段直接更新。

        Args:
            maintenance_id: 维护单ID
            seq: business_operation_id 序号
            model_cls: 子表模型类
            append_text: 追加文本
            operator: 操作人
        """
        record = (
            db.session.query(model_cls)
            .filter(
                model_cls.maintenance_id == maintenance_id,
                model_cls.business_operation_id == seq,
            )
            .first()
        )
        if record is None:
            return
        current = getattr(record, "description", "") or ""
        if append_text and append_text not in current:
            record.description = (current + append_text)[:500]
            record.update_time = datetime.now(timezone.utc)
            record.updator = operator
