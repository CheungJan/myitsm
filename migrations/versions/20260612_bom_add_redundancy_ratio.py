"""bom add redundancy ratio

Revision ID: 20260612_bom_redundancy
Revises: 20260612_qc_replenish
Create Date: 2026-06-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260612_bom_redundancy"
down_revision: Union[str, None] = "20260612_qc_replenish"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tmm41_bom",
        sa.Column("redundancy_ratio", sa.Numeric(5, 4), nullable=True, server_default="0", comment="补料冗余比例"),
    )


def downgrade() -> None:
    op.drop_column("tmm41_bom", "redundancy_ratio")
