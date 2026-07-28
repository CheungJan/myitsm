"""warehouse P0: TWH15 add refbillid

Revision ID: a1b2c3d4e5f6
Revises: 4ed81cdc5be5
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "4ed81cdc5be5"


def upgrade():
    op.add_column("twh15_out", sa.Column("refbillid", sa.String(8), nullable=True, comment="关联单据号"))


def downgrade():
    op.drop_column("twh15_out", "refbillid")
