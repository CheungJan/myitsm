"""add performance indexes for asset query and BOM resolution

Revision ID: 3b35c25a5736
Revises: db6aef9f5043
Create Date: 2026-05-13 16:02:10.012250

"""

from alembic import op

revision = "3b35c25a5736"
down_revision = "db6aef9f5043"
branch_labels = None
depends_on = None


def upgrade():
    # BOM 配件归属解析：按 EID 查父设备
    op.create_index("idx_pos_r_eid_eid", "tmm44_pos_r_eid", ["eid"])
    # 资产台账位置筛选：useflg + eid 复合索引
    op.create_index("idx_pos_r_eid_useflg", "tmm44_pos_r_eid", ["useflg", "eid"])
    op.create_index("idx_cust_pos_rl_eid_useflg", "tmm35_cust_pos_rl", ["eid", "useflg"])


def downgrade():
    op.drop_index("idx_cust_pos_rl_eid_useflg", table_name="tmm35_cust_pos_rl")
    op.drop_index("idx_pos_r_eid_useflg", table_name="tmm44_pos_r_eid")
    op.drop_index("idx_pos_r_eid_eid", table_name="tmm44_pos_r_eid")
