"""plan_serve add server_default to created_at updated_at

Revision ID: ecc3d58dd8ae
Revises: 23f195bfb98e
Create Date: 2026-06-23

"""
from alembic import op
import sqlalchemy as sa


revision = 'ecc3d58dd8ae'
down_revision = '23f195bfb98e'
branch_labels = None
depends_on = None


def upgrade():
    # created_at 增加数据库级默认值，修复 DBeaver 批量导入 NULL 报错
    with op.batch_alter_table('plan_serve', schema=None) as batch_op:
        batch_op.alter_column(
            'created_at',
            existing_type=sa.DateTime(),
            server_default=sa.text("NOW()"),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'updated_at',
            existing_type=sa.DateTime(),
            server_default=sa.text("NOW()"),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table('plan_serve', schema=None) as batch_op:
        batch_op.alter_column(
            'created_at',
            existing_type=sa.DateTime(),
            server_default=None,
            existing_nullable=False,
        )
        batch_op.alter_column(
            'updated_at',
            existing_type=sa.DateTime(),
            server_default=None,
            existing_nullable=False,
        )
