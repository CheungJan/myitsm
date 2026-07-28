"""warehouse: TWH14 add eid/seid for post-QC inbound tracking

Revision ID: e5f6a7b8c9d0
Revises: 39a1b0584ba2
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa

revision = "e5f6a7b8c9d0"
down_revision = "39a1b0584ba2"


def upgrade():
    op.add_column("twh14_checkindt", sa.Column("eid", sa.String(13), nullable=True, comment="设备EID（质检后）"))
    op.add_column("twh14_checkindt", sa.Column("seid", sa.String(30), nullable=True, comment="序列号（质检后）"))


def downgrade():
    op.drop_column("twh14_checkindt", "seid")
    op.drop_column("twh14_checkindt", "eid")
