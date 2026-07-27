"""qc result add draft type

Revision ID: 20260613_qc_draft_type
Revises: 20260612_tms05
Create Date: 2026-06-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260613_qc_draft_type"
down_revision: Union[str, None] = "20260612_tms05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tqc10_result",
        sa.Column("draft_type", sa.String(1), nullable=True, server_default="", comment="草稿类型：S=暂存 C=提交完成"),
    )


def downgrade() -> None:
    op.drop_column("tqc10_result", "draft_type")
