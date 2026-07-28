"""migrate_commode_to_syscodes_cm

Revision ID: f1a2b3c4d5e7
Revises: 12aa5457cd86
Create Date: 2026-07-05 17:00:00

变更:
  - 将 tmm47_commode 通讯方式数据迁移到 tmm31_syscodes (code_typ='CM')
  - 在 tmm31_syscodes 注册 CM 类型 (code_typ='SY', code_cd='CM')
  - 保留 tmm47_commode 表结构（暂不删除，后续清理）
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e7'
down_revision = '12aa5457cd86'
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc)


def upgrade():
    conn = op.get_bind()

    # 1. 注册 CM 类型到 SY（系统字典类型注册表）
    conn.execute(
        sa.text(
            "INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, created_at, updated_at) "
            "VALUES ('SY', 'CM', '通讯方式', '1', 0, :now, :now) "
            "ON CONFLICT (code_typ, code_cd) DO NOTHING"
        ),
        {"now": NOW},
    )

    # 2. 从 tmm47_commode 迁移数据到 tmm31_syscodes (code_typ='CM')
    #    字段映射: cmm_cd → code_cd, cmm_nm → code_nm, useflg → useflg
    rows = conn.execute(
        sa.text("SELECT cmm_cd, cmm_nm, useflg FROM tmm47_commode")
    ).fetchall()

    for cmm_cd, cmm_nm, useflg in rows:
        if not cmm_cd:
            continue
        conn.execute(
            sa.text(
                "INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, created_at, updated_at) "
                "VALUES ('CM', :cd, :nm, :flg, 0, :now, :now) "
                "ON CONFLICT (code_typ, code_cd) DO UPDATE SET "
                "  code_nm = EXCLUDED.code_nm, useflg = EXCLUDED.useflg, updated_at = EXCLUDED.updated_at"
            ),
            {"cd": cmm_cd, "nm": cmm_nm or '', "flg": useflg or '1', "now": NOW},
        )


def downgrade():
    conn = op.get_bind()

    # 删除 CM 类型下的所有编码
    conn.execute(
        sa.text("DELETE FROM tmm31_syscodes WHERE code_typ = 'CM'")
    )

    # 删除 SY 中的 CM 类型注册
    conn.execute(
        sa.text("DELETE FROM tmm31_syscodes WHERE code_typ = 'SY' AND code_cd = 'CM'")
    )
