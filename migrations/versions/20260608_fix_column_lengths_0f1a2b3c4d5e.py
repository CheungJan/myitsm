"""fix: 列宽修正 — status/refbillid/qcbillid 拓宽 + QC memo

Revision ID: 0f1a2b3c4d5e
Revises: 60182b33ded1
Create Date: 2026-06-08

变更清单:
  1. tms01_work_order.status    VARCHAR(10) → VARCHAR(20)  (IN_PROGRESS=11字符)
  2. tms03_work_process.status  VARCHAR(10) → VARCHAR(20)
  3. twh13_in.refbillid         VARCHAR(8)  → VARCHAR(30)  (工单号14字符)
  4. twh15_out.refbillid        VARCHAR(8)  → VARCHAR(30)
  5. twh12_detaildt.refbillid   VARCHAR(8)  → VARCHAR(30)
  6. tqc10_result.refbillid     VARCHAR(8)  → VARCHAR(30)
  7. tpc03_pcplanstatus.refbillid VARCHAR(8)  → VARCHAR(30)
  8. tqc10_result.qcbillid      VARCHAR(8)  → VARCHAR(12)  (QC+YYMMDD+3位序号=11字符)
  9. tqc11_resultdt.qcbillid    VARCHAR(8)  → VARCHAR(12)
 10. tqc11_resulteid.qcbillid   VARCHAR(8)  → VARCHAR(12)
 11. tqc10_result.memo          新增 VARCHAR(200)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0f1a2b3c4d5e"
down_revision: Union[str, None] = "60182b33ded1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1-2. MES 工单状态列
    op.alter_column("tms01_work_order", "status",
                    existing_type=sa.String(10), type_=sa.String(20))
    op.alter_column("tms03_work_process", "status",
                    existing_type=sa.String(10), type_=sa.String(20))

    # 3-7. 出入库/QC/采购 关联单号列
    for tbl in ("twh13_in", "twh15_out", "twh12_detaildt",
                "tqc10_result", "tpc03_pcplanstatus"):
        op.alter_column(tbl, "refbillid",
                        existing_type=sa.String(8), type_=sa.String(30))

    # 8-10. QC 单号列
    for tbl in ("tqc10_result", "tqc11_resultdt", "tqc11_resulteid"):
        op.alter_column(tbl, "qcbillid",
                        existing_type=sa.String(8), type_=sa.String(12))

    # 11. QC 备注
    op.add_column("tqc10_result",
                  sa.Column("memo", sa.String(200), comment="备注"))

    # 14. QC明细加来源入库单号追溯字段
    for tbl in ("tqc11_resultdt", "tqc11_resulteid"):
        op.add_column(tbl,
                      sa.Column("ref_rgstbillid", sa.String(30), comment="来源入库单号"))

    # 12. 出库明细加来源入库单号追溯
    for tbl in ("twh16_outdtprd", "twh16_outdteid"):
        op.add_column(tbl,
                      sa.Column("ref_inbillid", sa.String(8), comment="来源入库单号（质检出库追溯）"))

    # 13. 入库明细 ref_rgstbillid 放宽（QC 单号可达12字符）
    op.alter_column("twh14_checkindt", "ref_rgstbillid",
                    existing_type=sa.String(8), type_=sa.String(30))


def downgrade() -> None:
    # 13
    op.alter_column("twh14_checkindt", "ref_rgstbillid",
                    existing_type=sa.String(30), type_=sa.String(8))

    # 14
    for tbl in ("tqc11_resultdt", "tqc11_resulteid"):
        op.drop_column(tbl, "ref_rgstbillid")

    # 12
    for tbl in ("twh16_outdtprd", "twh16_outdteid"):
        op.drop_column(tbl, "ref_inbillid")

    # 11
    op.drop_column("tqc10_result", "memo")

    # 8-10
    for tbl in ("tqc10_result", "tqc11_resultdt", "tqc11_resulteid"):
        op.alter_column(tbl, "qcbillid",
                        existing_type=sa.String(12), type_=sa.String(8))

    # 3-7
    for tbl in ("twh13_in", "twh15_out", "twh12_detaildt",
                "tqc10_result", "tpc03_pcplanstatus"):
        op.alter_column(tbl, "refbillid",
                        existing_type=sa.String(30), type_=sa.String(8))

    # 1-2
    op.alter_column("tms01_work_order", "status",
                    existing_type=sa.String(20), type_=sa.String(10))
    op.alter_column("tms03_work_process", "status",
                    existing_type=sa.String(20), type_=sa.String(10))

