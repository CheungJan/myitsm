"""add_tit25_charge_fields

Revision ID: f1a2b3c4d5e6
Revises: c3d4e5f6a7b8
Create Date: 2026-07-20 22:07:00

变更:
  - tit25_accessories_update 新增收费维度字段（合并 TIT26 功能）：
    - payje     收款金额（Numeric(10,3)，c_type=3/5 时填，c_type=1/2/4 时与 price 同步）
    - paytype   收费类型（String(20)，c_type=3 纯服务费时用 PAY_SVC 字典，c_type=5 耗材时用 PAY_CONS 字典）
    - paydate   收款日期（DateTime）
    - memo      备注（String(200)）
  - 配合事项 9 审核标志统一 + 事项 10 price/payje 分开存储 + 事项 C1 TIT25 模型扩展
  - 合并 TIT26_PAYLIST 功能到 TIT25，c_type 扩展为 1维修/2购买/3纯服务费/4整机更换/5耗材线材
  - 历史数据迁移（C3）将 TIT26 按 paytype 分类迁移到 TIT25 c_type=3/5
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    # tit25_accessories_update 新增收费维度字段（合并 TIT26 功能）
    op.add_column(
        'tit25_accessories_update',
        sa.Column('payje', sa.Numeric(10, 3), nullable=True, comment='收款金额（c_type=3/5 时填，c_type=1/2/4 时与 price 同步）'),
    )
    op.add_column(
        'tit25_accessories_update',
        sa.Column('paytype', sa.String(20), nullable=True, comment='收费类型（c_type=3 用 PAY_SVC 字典，c_type=5 用 PAYTYPE_CONSUMABLE 字典）'),
    )
    op.add_column(
        'tit25_accessories_update',
        sa.Column('paydate', sa.DateTime, nullable=True, comment='收款日期'),
    )
    op.add_column(
        'tit25_accessories_update',
        sa.Column('memo', sa.String(200), nullable=True, comment='备注'),
    )


def downgrade():
    op.drop_column('tit25_accessories_update', 'memo')
    op.drop_column('tit25_accessories_update', 'paydate')
    op.drop_column('tit25_accessories_update', 'paytype')
    op.drop_column('tit25_accessories_update', 'payje')
