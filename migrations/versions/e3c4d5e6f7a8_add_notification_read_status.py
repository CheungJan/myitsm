"""add notification read_status/read_time

Revision ID: e3c4d5e6f7a8
Revises: d2b3c4d5e6f7
Create Date: 2026-07-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e3c4d5e6f7a8"
down_revision = "d2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """通知记录表加已读状态/已读时间字段（站内通知专用）。"""
    op.add_column(
        "tntf02_notification",
        sa.Column(
            "read_status",
            sa.String(10),
            nullable=True,
            server_default="unread",
            comment="已读状态: unread/read",
        ),
    )
    op.add_column(
        "tntf02_notification",
        sa.Column(
            "read_time",
            sa.DateTime(),
            nullable=True,
            comment="已读时间",
        ),
    )


def downgrade() -> None:
    """回滚：移除已读字段。"""
    op.drop_column("tntf02_notification", "read_time")
    op.drop_column("tntf02_notification", "read_status")
