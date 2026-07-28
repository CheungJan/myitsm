"""扩展 TMS04 物料消耗表 - 添加消耗类型、来源关联、成本字段

Revision ID: 20260612_extend_tms04
Revises: 0f1a2b3c4d5e
Create Date: 2026-06-12

变更清单:
  1. tms04_material_consume.consume_type    新增 VARCHAR(2) 默认 '1'（1定额 2补料 3报废 4返修 5退换）
  2. tms04_material_consume.ref_bill_type   新增 VARCHAR(2)（OV出库/IV入库）
  3. tms04_material_consume.ref_bill_id      新增 VARCHAR(20)（来源单据号）
  4. tms04_material_consume.ref_qc_id       新增 VARCHAR(12)（关联质检单号）
  5. tms04_material_consume.unit_cost       新增 NUMERIC(12,4)（单价）
  6. tms04_material_consume.total_cost       新增 NUMERIC(14,2)（总成本）
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260612_extend_tms04"
down_revision: Union[str, None] = "45b94b99793b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级：添加扩展字段"""
    # 消耗类型
    op.add_column(
        'tms04_material_consume',
        sa.Column('consume_type', sa.String(2), nullable=True, server_default='1', comment='消耗类型：1定额 2补料 3报废 4返修 5退换')
    )
    
    # 来源单据关联
    op.add_column(
        'tms04_material_consume',
        sa.Column('ref_bill_type', sa.String(2), nullable=True, comment='来源单据类型：OV出库/IV入库')
    )
    op.add_column(
        'tms04_material_consume',
        sa.Column('ref_bill_id', sa.String(20), nullable=True, comment='来源单据号')
    )
    op.add_column(
        'tms04_material_consume',
        sa.Column('ref_qc_id', sa.String(12), nullable=True, comment='关联质检单号')
    )
    
    # 成本字段
    op.add_column(
        'tms04_material_consume',
        sa.Column('unit_cost', sa.Numeric(12, 4), nullable=True, comment='单价（采购价/标准成本）')
    )
    op.add_column(
        'tms04_material_consume',
        sa.Column('total_cost', sa.Numeric(14, 2), nullable=True, comment='总成本（actual_qty * unit_cost）')
    )


def downgrade() -> None:
    """降级：移除扩展字段"""
    op.drop_column('tms04_material_consume', 'total_cost')
    op.drop_column('tms04_material_consume', 'unit_cost')
    op.drop_column('tms04_material_consume', 'ref_qc_id')
    op.drop_column('tms04_material_consume', 'ref_bill_id')
    op.drop_column('tms04_material_consume', 'ref_bill_type')
    op.drop_column('tms04_material_consume', 'consume_type')
