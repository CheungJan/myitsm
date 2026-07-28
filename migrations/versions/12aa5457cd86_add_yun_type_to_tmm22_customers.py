"""add yun_type to tmm22_customers

Revision ID: 12aa5457cd86
Revises: f8a2c3d4e5b6
Create Date: 2026-07-04 20:07:04.010846

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '12aa5457cd86'
down_revision = 'f8a2c3d4e5b6'
branch_labels = None
depends_on = None


def upgrade():
    """添加 yun_type 字段到 tmm22_customers 表，与 plan_cust.yun_type 保持一致"""
    op.add_column('tmm22_customers', sa.Column('yun_type', sa.String(2), comment='所属云类别（与plan_cust.yun_type一致）'))


def downgrade():
    """移除 yun_type 字段"""
    op.drop_column('tmm22_customers', 'yun_type')
