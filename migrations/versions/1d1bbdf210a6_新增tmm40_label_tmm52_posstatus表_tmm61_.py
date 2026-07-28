"""新增tmm40_label+tmm52_posstatus表+tmm61_deposit审核字段

Revision ID: 1d1bbdf210a6
Revises: bb4e815d5148
Create Date: 2026-05-16 23:02:54.751199

"""
from alembic import op

revision = '1d1bbdf210a6'
down_revision = 'bb4e815d5148'
branch_labels = None
depends_on = None


def upgrade():
    # tmm61_deposit 审核字段（已手动 ALTER TABLE，此处仅标记迁移完成）
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name='tmm61_deposit' AND column_name='auditflg') THEN
                ALTER TABLE tmm61_deposit ADD COLUMN auditflg VARCHAR(1) DEFAULT '0';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name='tmm61_deposit' AND column_name='auditman') THEN
                ALTER TABLE tmm61_deposit ADD COLUMN auditman VARCHAR(6);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name='tmm61_deposit' AND column_name='auditdate') THEN
                ALTER TABLE tmm61_deposit ADD COLUMN auditdate TIMESTAMP;
            END IF;
        END $$;
    """)


def downgrade():
    op.execute("""
        ALTER TABLE tmm61_deposit DROP COLUMN IF EXISTS auditdate;
        ALTER TABLE tmm61_deposit DROP COLUMN IF EXISTS auditman;
        ALTER TABLE tmm61_deposit DROP COLUMN IF EXISTS auditflg;
    """)
