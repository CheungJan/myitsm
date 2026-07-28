"""fix tmm46_area.useflg NULL → '1'

Revision ID: b9c8d7e6f5a4
Revises: 07830727e68e
Create Date: 2026-07-14

修复 tmm46_area.useflg 全部为 NULL 的问题，统一有效标志为 '1'，
让区域列表/下拉口径一致，后续可安全用 useflg='1' 过滤。
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b9c8d7e6f5a4"
down_revision = "07830727e68e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """将 tmm46_area.useflg 为 NULL 的记录更新为 '1'。"""
    op.execute(
        sa.text(
            "UPDATE tmm46_area SET useflg = '1' WHERE useflg IS NULL OR useflg = ''"
        )
    )


def downgrade() -> None:
    """回滚：将 useflg='1' 恢复为 NULL（仅恢复原本为 NULL 的记录无法精确还原）。

    注意：此回滚为近似操作，假设升级前所有记录均为 NULL。
    """
    op.execute(
        sa.text(
            "UPDATE tmm46_area SET useflg = NULL WHERE useflg = '1'"
        )
    )
