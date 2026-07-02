"""update_ov_iv_dict_add_production_refurbish

Revision ID: 01baab307ccd
Revises: e5f6a7b8c9d0
Create Date: 2026-06-01 18:15:57.925840

变更:
  - OV=8  "其他出库" → "生产出库"
  - OV=10 新增 "翻新出库"
  - IV=8  "其他入库" → "生产入库"
  - 删除 IV=C, IV=S（PB历史遗留，与"其他入库"重复）
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = '01baab307ccd'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc)


def upgrade():
    conn = op.get_bind()

    # OV=8: 其他出库 → 生产出库
    conn.execute(
        sa.text(
            "UPDATE tmm31_syscodes SET code_nm = '生产出库', updated_at = :now "
            "WHERE code_typ = 'OV' AND code_cd = '8'"
        ),
        {"now": NOW},
    )

    # OV=10: 新增翻新出库
    conn.execute(
        sa.text(
            "INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, created_at, updated_at) "
            "VALUES ('OV', '10', '翻新出库', '1', :now, :now) "
            "ON CONFLICT (code_typ, code_cd) DO NOTHING"
        ),
        {"now": NOW},
    )

    # IV=8: 其他入库 → 生产入库
    conn.execute(
        sa.text(
            "UPDATE tmm31_syscodes SET code_nm = '生产入库', updated_at = :now "
            "WHERE code_typ = 'IV' AND code_cd = '8'"
        ),
        {"now": NOW},
    )

    # 清理 PB 历史遗留的重复 IV 条目 (C, S)
    conn.execute(
        sa.text(
            "DELETE FROM tmm31_syscodes WHERE code_typ = 'IV' AND code_cd IN ('C', 'S')"
        ),
    )


def downgrade():
    conn = op.get_bind()

    # 恢复 IV=C, IV=S
    conn.execute(
        sa.text(
            "INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, created_at, updated_at) "
            "VALUES ('IV', 'C', '其他入库', '1', :now, :now), "
            "       ('IV', 'S', '其他入库', '1', :now, :now) "
            "ON CONFLICT (code_typ, code_cd) DO NOTHING"
        ),
        {"now": NOW},
    )

    # IV=8: 恢复 "其他入库"
    conn.execute(
        sa.text(
            "UPDATE tmm31_syscodes SET code_nm = '其他入库', updated_at = :now "
            "WHERE code_typ = 'IV' AND code_cd = '8'"
        ),
        {"now": NOW},
    )

    # OV=10: 删除翻新出库
    conn.execute(
        sa.text(
            "DELETE FROM tmm31_syscodes WHERE code_typ = 'OV' AND code_cd = '10'"
        ),
    )

    # OV=8: 恢复 "其他出库"
    conn.execute(
        sa.text(
            "UPDATE tmm31_syscodes SET code_nm = '其他出库', updated_at = :now "
            "WHERE code_typ = 'OV' AND code_cd = '8'"
        ),
        {"now": NOW},
    )
