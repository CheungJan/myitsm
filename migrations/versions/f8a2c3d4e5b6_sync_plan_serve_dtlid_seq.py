"""sync plan_serve_dtlid_seq to max(dtlid)

Revision ID: f8a2c3d4e5b6
Revises: eb79e751c8ce
Create Date: 2026-07-04

修复：plan_serve 表从 PB 迁移后历史数据 dtlid 已到 10776，
但 PostgreSQL SERIAL 序列仍从 1 开始，导致新创建呼出单 dtlid=1
与历史记录冲突。本迁移将序列 setval 到 max(dtlid)，确保新记录
从 max+1 开始自增。
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "f8a2c3d4e5b6"
down_revision = "c7c7a3e701f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """将 plan_serve_dtlid_seq 同步到 max(dtlid)。"""
    op.execute(
        "SELECT setval('plan_serve_dtlid_seq', "
        "COALESCE((SELECT MAX(dtlid) FROM plan_serve), 1));"
    )


def downgrade() -> None:
    """回滚无需操作（序列值不回退）。"""
    pass
