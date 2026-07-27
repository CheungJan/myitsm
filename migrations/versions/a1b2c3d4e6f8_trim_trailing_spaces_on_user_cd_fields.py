"""trim_trailing_spaces_on_user_cd_fields

Revision ID: a1b2c3d4e6f8
Revises: f1a2b3c4d5e7
Create Date: 2026-07-05 17:50:00

变更:
  - 清理 PB 遗留定长 CHAR 字段写入时被填充的尾空格
  - 涉及表与字段:
    - plan_serve.genercd / plan_serve.opercd
    - tmm40_label.opercd
    - tmm44_pos_r_eid.opercd
  - 这些字段在新系统使用 VARCHAR 存储，但历史数据从 PB 迁移时保留了 CHAR 尾空格
  - 清理后 genercd/opercd 可直接与 tmc13_users.user_cd 精确匹配
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e6f8'
down_revision = 'f1a2b3c4d5e7'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # plan_serve.genercd
    conn.execute(sa.text(
        "UPDATE plan_serve SET genercd = btrim(genercd) "
        "WHERE genercd IS NOT NULL AND genercd != btrim(genercd)"
    ))
    # plan_serve.opercd
    conn.execute(sa.text(
        "UPDATE plan_serve SET opercd = btrim(opercd) "
        "WHERE opercd IS NOT NULL AND opercd != btrim(opercd)"
    ))
    # tmm40_label.opercd
    conn.execute(sa.text(
        "UPDATE tmm40_label SET opercd = btrim(opercd) "
        "WHERE opercd IS NOT NULL AND opercd != btrim(opercd)"
    ))
    # tmm44_pos_r_eid.opercd
    conn.execute(sa.text(
        "UPDATE tmm44_pos_r_eid SET opercd = btrim(opercd) "
        "WHERE opercd IS NOT NULL AND opercd != btrim(opercd)"
    ))


def downgrade():
    # 尾空格清理不可逆（原始 CHAR 长度信息已丢失），downgrade 为空操作
    pass
