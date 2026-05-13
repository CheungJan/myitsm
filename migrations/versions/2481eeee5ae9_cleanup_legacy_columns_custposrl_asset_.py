"""cleanup legacy columns (CustPosRl asset fields migrated to Eid, PosREid unused col)

Revision ID: 2481eeee5ae9
Revises: 3b35c25a5736
Create Date: 2026-05-13 16:12:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "2481eeee5ae9"
down_revision = "3b35c25a5736"
branch_labels = None
depends_on = None


def upgrade():
    # CustPosRl: P0 将资产字段迁入 Eid，遗留列删除
    with op.batch_alter_table("tmm35_cust_pos_rl", schema=None) as batch_op:
        batch_op.drop_column("asset_type")
        batch_op.drop_column("install_date")
        batch_op.drop_column("recyclable")
        batch_op.drop_column("recycle_status")

    # PosREid: muitem 从未被模型使用，删除
    with op.batch_alter_table("tmm44_pos_r_eid", schema=None) as batch_op:
        batch_op.drop_column("muitem")
        batch_op.alter_column("created_at", nullable=False,
                              existing_server_default=sa.text("now()"))
        batch_op.alter_column("updated_at", nullable=False,
                              existing_server_default=sa.text("now()"))


def downgrade():
    with op.batch_alter_table("tmm44_pos_r_eid", schema=None) as batch_op:
        batch_op.alter_column("updated_at", nullable=True)
        batch_op.alter_column("created_at", nullable=True)
        batch_op.add_column(sa.Column("muitem", sa.VARCHAR(length=20), nullable=True))

    with op.batch_alter_table("tmm35_cust_pos_rl", schema=None) as batch_op:
        batch_op.add_column(sa.Column("recycle_status", sa.VARCHAR(length=10), nullable=True,
                            comment="回收状态"))
        batch_op.add_column(sa.Column("recyclable", sa.BOOLEAN(), nullable=True,
                            comment="可回收标志"))
        batch_op.add_column(sa.Column("install_date", postgresql.TIMESTAMP(), nullable=True,
                            comment="安装日期"))
        batch_op.add_column(sa.Column("asset_type", sa.VARCHAR(length=10), nullable=True,
                            comment="资产类型"))
