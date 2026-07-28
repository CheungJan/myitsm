"""add_opdate_opercd_to_plan_serve

Revision ID: 23f195bfb98e
Revises: 10cc9a90342b
Create Date: 2026-06-23 16:50:21.675901

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '23f195bfb98e'
down_revision = '10cc9a90342b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('plan_serve', schema=None) as batch_op:
        batch_op.add_column(sa.Column('opdate', sa.DateTime(), nullable=True, comment='最后操作日期'))
        batch_op.add_column(sa.Column('opercd', sa.String(length=6), nullable=True, comment='最后操作员'))


def downgrade():
    with op.batch_alter_table('plan_serve', schema=None) as batch_op:
        batch_op.drop_column('opercd')
        batch_op.drop_column('opdate')
