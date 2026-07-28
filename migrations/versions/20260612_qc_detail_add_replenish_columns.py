"""qc detail add replenish columns

Revision ID: 20260612_qc_replenish
Revises: 20260612_extend_tms04
Create Date: 2026-06-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260612_qc_replenish"
down_revision: Union[str, None] = "20260612_extend_tms04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tqc11_resultdt",
        sa.Column("replenish_status", sa.String(10), nullable=True, server_default="", comment="补料状态"),
    )
    op.add_column(
        "tqc11_resultdt",
        sa.Column("replenish_ov_billid", sa.String(12), nullable=True, server_default="", comment="补料出库单号"),
    )
    op.add_column(
        "tqc11_resulteid",
        sa.Column("replenish_status", sa.String(10), nullable=True, server_default="", comment="补料状态"),
    )
    op.add_column(
        "tqc11_resulteid",
        sa.Column("replenish_ov_billid", sa.String(12), nullable=True, server_default="", comment="补料出库单号"),
    )


def downgrade() -> None:
    op.drop_column("tqc11_resulteid", "replenish_ov_billid")
    op.drop_column("tqc11_resulteid", "replenish_status")
    op.drop_column("tqc11_resultdt", "replenish_ov_billid")
    op.drop_column("tqc11_resultdt", "replenish_status")
