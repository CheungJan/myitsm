"""eid add reserve_planno for plan A.

Revision ID: c1a2b3d4e5f6
Revises: b181717d589f
Create Date: 2026-07-02

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c1a2b3d4e5f6"
down_revision = "b181717d589f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """tmm43_eid 加 reserve_planno 字段（方案 A 预占）。"""
    op.add_column(
        "tmm43_eid",
        sa.Column(
            "reserve_planno", sa.String(20), nullable=True, comment="预占预计划号（方案A专属）"
        ),
    )


def downgrade() -> None:
    """回滚：删除 reserve_planno 字段。"""
    op.drop_column("tmm43_eid", "reserve_planno")
