"""清理 TPC14 旧字段

删除被替代的旧字段：
- refbillid → 已被 ref_rgstbillid 替代
- pcamt → 已被 total_settle_amt 替代

Revision ID: 9b23a7c55f0f
Revises: ab9724f22565
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa

revision = "9b23a7c55f0f"
down_revision = "ab9724f22565"


def upgrade():
    op.drop_column("tpc14_pcbill", "refbillid")
    op.drop_column("tpc14_pcbill", "pcamt")


def downgrade():
    op.add_column("tpc14_pcbill", sa.Column("refbillid", sa.String(8), nullable=True))
    op.add_column("tpc14_pcbill", sa.Column("pcamt", sa.Numeric(16, 4), nullable=True))
