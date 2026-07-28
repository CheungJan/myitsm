"""warehouse P1: TWH14 add ref_rgstbillid + ref_rgstlineno

Revision ID: 39a1b0584ba2
Revises: a1b2c3d4e5f6
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa

revision = "39a1b0584ba2"
down_revision = "a1b2c3d4e5f6"


def upgrade():
    op.add_column("twh14_checkindt", sa.Column("ref_rgstbillid", sa.String(8), nullable=True, comment="来源订单号"))
    op.add_column("twh14_checkindt", sa.Column("ref_rgstlineno", sa.Integer, nullable=True, comment="来源订单行号"))


def downgrade():
    op.drop_column("twh14_checkindt", "ref_rgstlineno")
    op.drop_column("twh14_checkindt", "ref_rgstbillid")
