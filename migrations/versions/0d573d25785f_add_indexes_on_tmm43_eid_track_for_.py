"""add indexes on tmm43_eid_track for track history and plan_refid queries

Revision ID: 0d573d25785f
Revises: 2481eeee5ae9
Create Date: 2026-05-13 17:30:00.000000

"""

from alembic import op

revision = "0d573d25785f"
down_revision = "2481eeee5ae9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("idx_eid_track_eid_itemcd", "tmm43_eid_track", ["eid", "itemcd"])
    op.create_index("idx_eid_track_type_eid", "tmm43_eid_track", ["type", "eid"])


def downgrade():
    op.drop_index("idx_eid_track_type_eid", table_name="tmm43_eid_track")
    op.drop_index("idx_eid_track_eid_itemcd", table_name="tmm43_eid_track")
