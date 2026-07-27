"""add notification retry_count

Revision ID: d2b3c4d5e6f7
Revises: c1a2b3c4d5e6
Create Date: 2026-07-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d2b3c4d5e6f7"
down_revision = "c1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """通知记录表加重试次数字段。"""
    op.add_column(
        "tntf02_notification",
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=True,
            server_default="0",
            comment="重试次数",
        ),
    )


def downgrade() -> None:
    """回滚：移除 retry_count 字段。"""
    op.drop_column("tntf02_notification", "retry_count")
