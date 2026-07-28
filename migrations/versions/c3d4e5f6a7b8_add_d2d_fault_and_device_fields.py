"""add_d2d_fault_and_device_fields

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-20 22:05:00

变更:
  - tit23_maintenance_d2d 新增故障代码与设备/配件追溯字段：
    - gzdm          故障代码（8位，= tit04_archivecode.arch_cd 值，PB 为虚拟列不落库，重构改为落库以支持单次上门故障追溯）
    - device_id     本次处理设备（PB 无此字段，重构新增以支持设备追溯）
    - accessories_id 本次处理配件（PB 无此字段，重构新增以支持配件追溯）
  - 配合事项 1 d2d 故障代码存储方案 B：d2d 只落 gzdm，大类/小类查询时从 gzdm 前 2 位派生或 join tit04_archivecode
  - 与 PB 差异：PB d2d 表 gzdm 为 char(0) 虚拟列不落库，重构改为落库支持单次上门故障追溯
  - gzdl/gzxl 不落库：可从 gzdm 前 2 位派生（= tit04_archivecode.fault_type），避免冗余存储
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # tit23_maintenance_d2d 新增故障代码与设备/配件追溯字段
    # gzdl/gzxl 不落库，查询时从 gzdm 前 2 位派生或 join tit04_archivecode 取 fault_type
    op.add_column(
        'tit23_maintenance_d2d',
        sa.Column('gzdm', sa.String(8), nullable=True, comment='故障代码（= tit04_archivecode.arch_cd 值，重构改为落库以支持单次上门故障追溯）'),
    )
    op.add_column(
        'tit23_maintenance_d2d',
        sa.Column('device_id', sa.String(13), nullable=True, comment='本次处理设备（重构新增，支持设备追溯）'),
    )
    op.add_column(
        'tit23_maintenance_d2d',
        sa.Column('accessories_id', sa.String(13), nullable=True, comment='本次处理配件（重构新增，支持配件追溯）'),
    )


def downgrade():
    op.drop_column('tit23_maintenance_d2d', 'accessories_id')
    op.drop_column('tit23_maintenance_d2d', 'device_id')
    op.drop_column('tit23_maintenance_d2d', 'gzdm')
