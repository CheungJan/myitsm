"""add_d2d_four_elements_fields

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-20 21:42:00

变更:
  - tit23_maintenance_d2d 新增离店解决四要素结构化字段：
    - d2d_phenomenon   实际现象（String(200)）
    - d2d_reason       原因（String(200)）
    - d2d_handling     处理过程工程师手输补充（String(500)）
    - d2d_result       结果，直接用 ZT 字典码值 5/4/6/7/3（String(2)）
    - closure_reason   关闭原因，仅 d2d_result='3' 时填，CLOSURE_REASON 字典（String(1)）
    - d2d_note         其他补充（String(200)）
  - 配合事项 18 离店解决四要素结构化
  - d2d_result 直接赋值主表 current_status（与 PB 语义一致）
  - jjbz 字段废弃但保留（PB 数据迁移兼容），不再写入新数据
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade():
    # tit23_maintenance_d2d 新增四要素结构化字段
    op.add_column(
        'tit23_maintenance_d2d',
        sa.Column('d2d_phenomenon', sa.String(200), nullable=True, comment='实际现象'),
    )
    op.add_column(
        'tit23_maintenance_d2d',
        sa.Column('d2d_reason', sa.String(200), nullable=True, comment='原因'),
    )
    op.add_column(
        'tit23_maintenance_d2d',
        sa.Column('d2d_handling', sa.String(500), nullable=True, comment='处理过程（工程师手输补充）'),
    )
    op.add_column(
        'tit23_maintenance_d2d',
        sa.Column('d2d_result', sa.String(2), nullable=True, comment='结果（ZT 字典码值：5已解决/4未解决/6转修/7待配件/3关闭）'),
    )
    op.add_column(
        'tit23_maintenance_d2d',
        sa.Column('closure_reason', sa.String(1), nullable=True, comment='关闭原因（仅 d2d_result=3 时填，CLOSURE_REASON 字典）'),
    )
    op.add_column(
        'tit23_maintenance_d2d',
        sa.Column('d2d_note', sa.String(200), nullable=True, comment='其他补充'),
    )


def downgrade():
    op.drop_column('tit23_maintenance_d2d', 'd2d_note')
    op.drop_column('tit23_maintenance_d2d', 'closure_reason')
    op.drop_column('tit23_maintenance_d2d', 'd2d_result')
    op.drop_column('tit23_maintenance_d2d', 'd2d_handling')
    op.drop_column('tit23_maintenance_d2d', 'd2d_reason')
    op.drop_column('tit23_maintenance_d2d', 'd2d_phenomenon')
