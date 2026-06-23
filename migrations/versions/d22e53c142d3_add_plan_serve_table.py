"""add plan_serve table

Revision ID: d22e53c142d3
Revises: c7957b16fbcb
Create Date: 2026-06-22 19:05:49.293603

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd22e53c142d3'
down_revision = 'c7957b16fbcb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('plan_serve',
        sa.Column('dtlid', sa.Integer(), autoincrement=True, nullable=False, comment='明细ID'),
        sa.Column('planno', sa.String(length=10), nullable=True, comment='关联预计划单号（兼容历史NULL）'),
        sa.Column('plantyp', sa.String(length=2), nullable=True, comment='计划类型'),
        sa.Column('servetyp', sa.String(length=2), nullable=True, comment='服务类型'),
        sa.Column('serve_task', sa.String(length=200), nullable=True, comment='服务任务'),
        sa.Column('serve_back', sa.String(length=200), nullable=True, comment='客户反馈/呼出结果'),
        sa.Column('serve_mark', sa.String(length=200), nullable=True, comment='服务备注'),
        sa.Column('commmode', sa.String(length=4), nullable=True, comment='通讯方式'),
        sa.Column('status', sa.String(length=2), nullable=True, comment='状态（00待呼出/01已呼出/09作废）'),
        sa.Column('gendate', sa.DateTime(), nullable=True, comment='创建日期'),
        sa.Column('genercd', sa.String(length=6), nullable=True, comment='创建操作员'),
        sa.Column('opdate', sa.DateTime(), nullable=True, comment='最后操作日期'),
        sa.Column('opercd', sa.String(length=6), nullable=True, comment='最后操作员'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint('dtlid')
    )


def downgrade():
    op.drop_table('plan_serve')
