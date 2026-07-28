"""TIT25 配件更新表加乐观锁 version 字段

审核意见 7 采纳：同一维护单两个工程师同时换件写 TIT25，或一人离店写 d2d
同时另一人写 TIT25，没有乐观锁或行级锁策略。新增 version 字段实现乐观锁。

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-07-21
"""

from alembic import op
import sqlalchemy as sa


revision = "b3c4d5e6f7a8"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """新增 tit25_accessories_update.version 字段（乐观锁）。"""
    op.add_column(
        "tit25_accessories_update",
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="乐观锁版本号（每次更新+1，并发控制）",
        ),
    )


def downgrade() -> None:
    """回滚：删除 version 字段。"""
    op.drop_column("tit25_accessories_update", "version")
