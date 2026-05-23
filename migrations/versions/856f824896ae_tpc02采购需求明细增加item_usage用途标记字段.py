"""TPC02采购需求明细增加item_usage用途标记字段

Revision ID: 856f824896ae
Revises: 5e2f0e99c995
Create Date: 2026-05-23 16:53:20.340801

"""
from alembic import op
import sqlalchemy as sa


revision = '856f824896ae'
down_revision = '5e2f0e99c995'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tpc02_pcplandt', schema=None) as batch_op:
        batch_op.add_column(sa.Column('item_usage', sa.String(length=20), nullable=True, server_default='sale', comment='用途标记: sale=销售备货, maintenance=维护消耗品, internal=内部使用'))


def downgrade():
    with op.batch_alter_table('tpc02_pcplandt', schema=None) as batch_op:
        batch_op.drop_column('item_usage')
