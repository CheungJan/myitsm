"""plan_serve.planno nullable for legacy data

Revision ID: 65634e3c3765
Revises: ecc3d58dd8ae
Create Date: 2026-06-23

"""
from alembic import op
import sqlalchemy as sa


revision = '65634e3c3765'
down_revision = 'ecc3d58dd8ae'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('plan_serve', schema=None) as batch_op:
        batch_op.alter_column(
            'planno',
            existing_type=sa.String(length=10),
            nullable=True,
        )


def downgrade():
    with op.batch_alter_table('plan_serve', schema=None) as batch_op:
        batch_op.alter_column(
            'planno',
            existing_type=sa.String(length=10),
            nullable=False,
        )
