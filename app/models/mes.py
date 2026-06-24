"""
生产制造管理（MES Lite）模型（Tier-3 G7）。

涵盖生产工单、工序管理、物料消耗核算。

对应新增数据库表：
  生产工单：TMS01_WORK_ORDER
  工序定义：TMS02_PROCESS_DEF
  工单工序：TMS03_WORK_PROCESS
  物料消耗：TMS04_MATERIAL_CONSUME
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# 生产工单
# ---------------------------------------------------------------------------


class WorkOrder(BaseModel):
    """生产工单（TMS01_WORK_ORDER）。"""

    __tablename__ = "tms01_work_order"

    wo_id = db.Column(db.String(20), primary_key=True, comment="工单编号")
    item_cd = db.Column(db.String(20), nullable=False, comment="产品编码")
    plan_qty = db.Column(db.Integer, nullable=False, comment="计划数量")
    actual_qty = db.Column(db.Integer, default=0, comment="实际完成数量")
    plan_start = db.Column(db.Date, comment="计划开始日期")
    plan_end = db.Column(db.Date, comment="计划完成日期")
    actual_start = db.Column(db.Date, comment="实际开始日期")
    actual_end = db.Column(db.Date, comment="实际完成日期")
    status = db.Column(
        db.String(20),
        default="DRAFT",
        comment="状态（DRAFT/RELEASED/PICKING/IN_PROGRESS/QC_PENDING/COMPLETED/CANCELLED）",
    )
    wo_type = db.Column(db.String(10), default="PRODUCTION", comment="工单类型: PRODUCTION=生产 RENOVATION=翻新")
    priority = db.Column(db.String(10), default="NORMAL", comment="优先级")
    warehouse_cd = db.Column(db.String(20), comment="成品入库仓库")
    pick_whcd = db.Column(db.String(20), comment="领料出库仓库")
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")

    processes = db.relationship("WorkProcess", back_populates="work_order", lazy="dynamic")


# ---------------------------------------------------------------------------
# 工序定义
# ---------------------------------------------------------------------------


class ProcessDef(BaseModel):
    """工序定义（TMS02_PROCESS_DEF）。"""

    __tablename__ = "tms02_process_def"

    process_cd = db.Column(db.String(20), primary_key=True, comment="工序编码")
    process_nm = db.Column(db.String(100), nullable=False, comment="工序名称")
    process_type = db.Column(
        db.String(10),
        comment="工序类型（ASSEMBLY/TEST/PACKAGE/OTHER）",
    )
    std_hours = db.Column(db.Numeric(6, 2), comment="标准工时（小时）")
    sort_no = db.Column(db.Integer, default=0, comment="排序号")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")


# ---------------------------------------------------------------------------
# 工单工序
# ---------------------------------------------------------------------------


class WorkProcess(BaseModel):
    """工单工序（TMS03_WORK_PROCESS）。"""

    __tablename__ = "tms03_work_process"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wo_id = db.Column(
        db.String(20),
        db.ForeignKey("tms01_work_order.wo_id"),
        nullable=False,
        comment="工单编号",
    )
    process_cd = db.Column(db.String(20), nullable=False, comment="工序编码")
    seq_no = db.Column(db.Integer, nullable=False, comment="工序序号")
    plan_qty = db.Column(db.Integer, comment="计划数量")
    actual_qty = db.Column(db.Integer, default=0, comment="完成数量")
    defect_qty = db.Column(db.Integer, default=0, comment="不良品数量")
    status = db.Column(
        db.String(20),
        default="PENDING",
        comment="状态（PENDING/IN_PROGRESS/COMPLETED/SKIPPED）",
    )
    start_time = db.Column(db.DateTime, comment="开始时间")
    end_time = db.Column(db.DateTime, comment="结束时间")
    worker_cd = db.Column(db.String(20), comment="操作工")
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")

    work_order = db.relationship("WorkOrder", back_populates="processes")


# ---------------------------------------------------------------------------
# 物料消耗
# ---------------------------------------------------------------------------


class ConsumeType:
    """物料消耗类型常量（与 tmm31_syscodes CT 字典同步）。"""

    PLAN = "1"       # 定额领料
    REPLENISH = "2"  # 不良补料
    SCRAP = "3"      # 报废出库
    REPAIR = "4"     # 返修出库
    RETURN = "5"     # 退料入库
    RETURN_OUT = "6"  # 退货出库


class MaterialConsume(BaseModel):
    """物料消耗记录（TMS04_MATERIAL_CONSUME）。"""

    __tablename__ = "tms04_material_consume"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wo_id = db.Column(db.String(20), nullable=False, comment="工单编号")
    process_cd = db.Column(db.String(20), comment="工序编码")
    item_cd = db.Column(db.String(20), nullable=False, comment="物料编码")
    plan_qty = db.Column(db.Numeric(10, 2), comment="计划用量")
    actual_qty = db.Column(db.Numeric(10, 2), comment="实际用量")
    unit = db.Column(db.String(10), comment="单位")
    warehouse_cd = db.Column(db.String(20), comment="领料仓库")
    consume_date = db.Column(db.Date, comment="领料日期")
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")

    # 扩展字段：消耗类型与来源关联
    consume_type = db.Column(
        db.String(2),
        default="1",
        comment="消耗类型：1定额 2补料 3报废 4返修 5退换"
    )
    ref_bill_type = db.Column(db.String(2), comment="来源单据类型：OV出库/IV入库")
    ref_bill_id = db.Column(db.String(20), comment="来源单据号")
    ref_qc_id = db.Column(db.String(12), comment="关联质检单号")

    # 成本字段（允许为空，后续填入）
    unit_cost = db.Column(db.Numeric(12, 4), comment="单价（采购价/标准成本）")
    total_cost = db.Column(db.Numeric(14, 2), comment="总成本（actual_qty * unit_cost）")


class ReplaceRecord(BaseModel):
    """物料更换记录（TMS05_REPLACE_RECORD）。"""

    __tablename__ = "tms05_replace_record"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    wo_id = db.Column(db.String(20), nullable=False, comment="工单号")
    old_eid = db.Column(db.String(20), comment="旧物料序列号（批次物料可为空）")
    new_eid = db.Column(db.String(20), comment="新物料序列号（批次物料可为空，FQC合格后生成）")
    itemcd = db.Column(db.String(12), nullable=True, comment="物料编码")
    old_batch_no = db.Column(db.String(20), comment="旧批次号（批次物料使用）")
    new_batch_no = db.Column(db.String(20), comment="新批次号（批次物料使用）")
    replace_date = db.Column(db.TIMESTAMP, comment="更换时间")
    opercd = db.Column(db.String(10), comment="操作人")
    memo = db.Column(db.String(200), comment="备注")

    __table_args__ = (
        db.Index("idx_tms05_wo", "wo_id"),
    )
