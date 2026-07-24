"""add_paytype_svc_dict

Revision ID: d4e5f6a7b8c9
Revises: c3d5e7f9a1b2
Create Date: 2026-07-20 16:30:00

变更:
  - 在 tmm31_syscodes 注册 PAY_SVC 类型 (code_typ='SY', code_cd='PAY_SVC')
  - 插入 PAY_SVC 服务费类型字典数据（非更换收费场景使用，c_type=3）
  - 字典值：01=上门费 / 02=检测费 / 03=软件服务费 / 04=其他
  - 配件场景（c_type=1/2/4）不需要此字典，物料分类由 tmm12_items.consume/itemtyp 决定
  - 注：code_typ 字段 VARCHAR(10)，故用 PAY_SVC（7 字符）而非 PAYTYPE_SVC（12 字符）
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d5e7f9a1b2'
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc)

# PAY_SVC 字典数据：非更换服务费类型
PAY_SVC_ITEMS = [
    ("01", "上门费", "上门服务基础费用", 1),
    ("02", "检测费", "设备检测诊断费用", 2),
    ("03", "软件服务费", "软件安装/升级/维护费用", 3),
    ("04", "其他", "其他非更换服务费用", 4),
]


def upgrade():
    conn = op.get_bind()

    # 1. 注册 PAY_SVC 类型到 SY（系统字典类型注册表）
    conn.execute(
        sa.text(
            "INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, created_at, updated_at) "
            "VALUES ('SY', 'PAY_SVC', '服务费类型', '1', 0, :now, :now) "
            "ON CONFLICT (code_typ, code_cd) DO NOTHING"
        ),
        {"now": NOW},
    )

    # 2. 插入 PAY_SVC 字典明细
    for code_cd, code_nm, memo, sort_no in PAY_SVC_ITEMS:
        conn.execute(
            sa.text(
                "INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, memo, created_at, updated_at) "
                "VALUES ('PAY_SVC', :cd, :nm, '1', :sort_no, :memo, :now, :now) "
                "ON CONFLICT (code_typ, code_cd) DO UPDATE SET "
                "  code_nm = EXCLUDED.code_nm, useflg = '1', sort_no = EXCLUDED.sort_no, "
                "  memo = EXCLUDED.memo, updated_at = EXCLUDED.updated_at"
            ),
            {"cd": code_cd, "nm": code_nm, "sort_no": sort_no, "memo": memo, "now": NOW},
        )


def downgrade():
    conn = op.get_bind()

    # 删除 PAY_SVC 类型下的所有编码
    conn.execute(
        sa.text("DELETE FROM tmm31_syscodes WHERE code_typ = 'PAY_SVC'")
    )

    # 删除 SY 中的 PAY_SVC 类型注册
    conn.execute(
        sa.text("DELETE FROM tmm31_syscodes WHERE code_typ = 'SY' AND code_cd = 'PAY_SVC'")
    )
