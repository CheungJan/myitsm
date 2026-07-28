"""add imple_billid to plan_cust

Revision ID: 10cc9a90342b
Revises: d22e53c142d3
Create Date: 2026-06-22

"""
from alembic import op
import sqlalchemy as sa


revision = '10cc9a90342b'
down_revision = 'd22e53c142d3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('plan_cust', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'imple_billid', sa.String(length=20), nullable=True,
            comment='下游单据ID（实施确认时写入）'
        ))


def downgrade():
    with op.batch_alter_table('plan_cust', schema=None) as batch_op:
        batch_op.drop_column('imple_billid')
