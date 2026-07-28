"""add ref_planno to twh16_outdteid and twh16_outdtprd for batch outbound

Revision ID: a1b2c3d4e5f6
Revises: e5f1a2b3c4d7
Create Date: 2026-07-06

批量出库方案B：出库明细行记来源预计划号 ref_planno。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7c8d9e0f1a2"
down_revision = "e5f1a2b3c4d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # twh16_outdteid 新增 ref_planno
    op.add_column(
        "twh16_outdteid",
        sa.Column("ref_planno", sa.String(12), nullable=True, comment="来源预计划号（批量出库方案B）"),
    )
    # twh16_outdtprd 新增 ref_planno
    op.add_column(
        "twh16_outdtprd",
        sa.Column("ref_planno", sa.String(12), nullable=True, comment="来源预计划号（批量出库方案B）"),
    )


def downgrade() -> None:
    op.drop_column("twh16_outdtprd", "ref_planno")
    op.drop_column("twh16_outdteid", "ref_planno")
