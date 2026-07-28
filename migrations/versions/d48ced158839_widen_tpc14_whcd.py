"""widen tpc14_pcbill.whcd for multi-warehouse support

Revision ID: d48ced158839
Revises: 9b23a7c55f0f
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa

revision = "d48ced158839"
down_revision = "9b23a7c55f0f"


def upgrade():
    op.alter_column("tpc14_pcbill", "whcd",
                    existing_type=sa.String(2),
                    type_=sa.String(50),
                    existing_nullable=True)


def downgrade():
    op.alter_column("tpc14_pcbill", "whcd",
                    existing_type=sa.String(50),
                    type_=sa.String(2),
                    existing_nullable=True)
