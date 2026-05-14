"""widen tmm41_bom and tmm42_bomdt bomcd to VARCHAR(20)

Revision ID: bb4e815d5148
Revises: 0d573d25785f
Create Date: 2026-05-14 23:15:00.000000

"""

from alembic import op

revision = "bb4e815d5148"
down_revision = "0d573d25785f"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE tmm41_bom ALTER COLUMN bomcd TYPE VARCHAR(20)")
    op.execute("ALTER TABLE tmm42_bomdt ALTER COLUMN bomcd TYPE VARCHAR(20)")


def downgrade():
    op.execute("ALTER TABLE tmm41_bom ALTER COLUMN bomcd TYPE VARCHAR(6)")
    op.execute("ALTER TABLE tmm42_bomdt ALTER COLUMN bomcd TYPE VARCHAR(6)")
