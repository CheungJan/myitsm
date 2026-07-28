"""merge heads 60182b33ded1 e3c4d5e6f7a8 3a45f7e78bab 45b94b99793b

Revision ID: a1b3c5d7e9f0
Revises: 60182b33ded1, e3c4d5e6f7a8, 3a45f7e78bab, 45b94b99793b
Create Date: 2026-07-17

合并多分支头，便于后续通知模板/派工规则字段扩展迁移。
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b3c5d7e9f0"
down_revision = ("60182b33ded1", "e3c4d5e6f7a8", "3a45f7e78bab", "45b94b99793b")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """合并多分支头，无 DDL。"""
    pass


def downgrade() -> None:
    """回滚：无操作。"""
    pass
