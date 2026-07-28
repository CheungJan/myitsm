"""出库明细增加行级结案字段closed_flg_reason_by_at

Revision ID: 60182b33ded1
Revises: a58d822bc65c
Create Date: 2026-06-04 17:49:45.234254

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '60182b33ded1'
down_revision = 'a58d822bc65c'
branch_labels = None
depends_on = None


def upgrade():
    # 出库明细EID表增加行级结案字段
    with op.batch_alter_table('twh16_outdteid', schema=None) as batch_op:
        batch_op.add_column(sa.Column('closed_flg', sa.String(length=1), nullable=True, comment='结案标志 0=未结案 1=已结案'))
        batch_op.add_column(sa.Column('closed_reason', sa.String(length=100), nullable=True, comment='结案原因'))
        batch_op.add_column(sa.Column('closed_by', sa.String(length=6), nullable=True, comment='结案操作人'))
        batch_op.add_column(sa.Column('closed_at', sa.DateTime(), nullable=True, comment='结案时间'))

    # 出库明细PRD表增加行级结案字段
    with op.batch_alter_table('twh16_outdtprd', schema=None) as batch_op:
        batch_op.add_column(sa.Column('closed_flg', sa.String(length=1), nullable=True, comment='结案标志 0=未结案 1=已结案'))
        batch_op.add_column(sa.Column('closed_reason', sa.String(length=100), nullable=True, comment='结案原因'))
        batch_op.add_column(sa.Column('closed_by', sa.String(length=6), nullable=True, comment='结案操作人'))
        batch_op.add_column(sa.Column('closed_at', sa.DateTime(), nullable=True, comment='结案时间'))

    # 设置已有数据默认值为 '0'（未结案）
    op.execute("UPDATE twh16_outdteid SET closed_flg = '0' WHERE closed_flg IS NULL")
    op.execute("UPDATE twh16_outdtprd SET closed_flg = '0' WHERE closed_flg IS NULL")


def downgrade():
    with op.batch_alter_table('twh16_outdtprd', schema=None) as batch_op:
        batch_op.drop_column('closed_at')
        batch_op.drop_column('closed_by')
        batch_op.drop_column('closed_reason')
        batch_op.drop_column('closed_flg')

    with op.batch_alter_table('twh16_outdteid', schema=None) as batch_op:
        batch_op.drop_column('closed_at')
        batch_op.drop_column('closed_by')
        batch_op.drop_column('closed_reason')
        batch_op.drop_column('closed_flg')
