"""create tms05 replace record

Revision ID: 20260612_tms05
Revises: 20260612_bom_redundancy
Create Date: 2026-06-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260612_tms05"
down_revision: Union[str, None] = "20260612_bom_redundancy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tms05_replace_record",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True, comment="主键"),
        sa.Column("wo_id", sa.String(20), nullable=False, comment="工单号"),
        sa.Column("old_eid", sa.String(20), comment="旧物料序列号"),
        sa.Column("new_eid", sa.String(20), comment="新物料序列号"),
        sa.Column("itemcd", sa.String(12), comment="物料编码"),
        sa.Column("replace_date", sa.TIMESTAMP, server_default=sa.func.current_timestamp(), comment="更换时间"),
        sa.Column("opercd", sa.String(10), comment="操作人"),
        sa.Column("memo", sa.String(200), comment="备注"),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_tms05_wo", "tms05_replace_record", ["wo_id"])


def downgrade() -> None:
    op.drop_index("idx_tms05_wo", "tms05_replace_record")
    op.drop_table("tms05_replace_record")
