"""merge qc draft type

Revision ID: c7957b16fbcb
Revises: 20260613_qc_draft_type, 3a45f7e78bab
Create Date: 2026-06-13 15:46:25.331563

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7957b16fbcb'
down_revision = ('20260613_qc_draft_type', '3a45f7e78bab')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
