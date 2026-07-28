"""widen plan_cust.is_outflag String(2)->String(4) for N/A tri-state

Revision ID: e5f1a2b3c4d7
Revises: a1b2c3d4e6f8
Create Date: 2026-07-06
"""
from alembic import op
import sqlalchemy as sa

revision = "e5f1a2b3c4d7"
down_revision = "a1b2c3d4e6f8"


def upgrade():
    # is_outflag 三态语义（N/A=非商用仓库不适用/0=待出库/1=OV=1出库单已审核）
    # 'N/A' 为 3 字符，原 String(2) 无法容纳，拓宽为 String(4)
    op.alter_column("plan_cust", "is_outflag",
                    existing_type=sa.String(2),
                    type_=sa.String(4),
                    existing_nullable=True)


def downgrade():
    op.alter_column("plan_cust", "is_outflag",
                    existing_type=sa.String(4),
                    type_=sa.String(2),
                    existing_nullable=True)
