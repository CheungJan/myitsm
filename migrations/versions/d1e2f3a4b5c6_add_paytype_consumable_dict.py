"""add_paytype_consumable_dict

Revision ID: d1e2f3a4b5c6
Revises: f1a2b3c4d5e6
Create Date: 2026-07-20 22:10:00

变更:
  - 在 tmm31_syscodes 注册 PAYTYPE_CONSUMABLE 类型 (code_typ='SY', code_cd='PAYTYPE_CONSUMABLE')
  - 插入 PAYTYPE_CONSUMABLE 耗材收费类型字典数据（c_type='5' 耗材/线材场景使用）
  - 字典值：01=线材 / 02=枪线 / 03=扫描枪线 / 04=耗材 / 05=3G电源 / 06=打印机电源 / 07=其他
  - 配合事项 C6 收费类型字典化：PAY_SVC（纯服务费）+ PAYTYPE_CONSUMABLE（耗材/线材）
  - 前端 c_type=5 时下拉选择，不再自由输入
  - 注：code_typ 字段 VARCHAR(10)，故用 PAYTYPE_CONSUMABLE（17 字符）会超长，改用 PAY_CONS（7 字符）
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc)

# PAY_CONS 字典数据：耗材/线材收费类型（c_type=5 时使用）
# 注：字典类型注册用 PAY_CONS（7 字符，code_typ VARCHAR(10) 限制），业务字段 paytype 仍存字典码值
PAY_CONS_ITEMS = [
    ("01", "线材", "通用线材", 1),
    ("02", "枪线", "扫描枪连接线", 2),
    ("03", "扫描枪线", "扫描枪专用线", 3),
    ("04", "耗材", "通用耗材", 4),
    ("05", "3G电源", "3G 设备电源", 5),
    ("06", "打印机电源", "打印机电源适配器", 6),
    ("07", "其他", "其他耗材/线材", 7),
]


def upgrade():
    conn = op.get_bind()

    # 1. 注册 PAY_CONS 类型到 SY（系统字典类型注册表）
    # 注：code_typ VARCHAR(10)，PAYTYPE_CONSUMABLE 超长，用 PAY_CONS
    conn.execute(
        sa.text(
            "INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, memo, created_at, updated_at) "
            "VALUES ('SY', 'PAY_CONS', '耗材收费类型', '1', 0, 'c_type=5 耗材/线材收费类型字典', :now, :now) "
            "ON CONFLICT (code_typ, code_cd) DO NOTHING"
        ),
        {"now": NOW},
    )

    # 2. 插入 PAY_CONS 字典明细
    for code_cd, code_nm, memo, sort_no in PAY_CONS_ITEMS:
        conn.execute(
            sa.text(
                "INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, memo, created_at, updated_at) "
                "VALUES ('PAY_CONS', :cd, :nm, '1', :sort_no, :memo, :now, :now) "
                "ON CONFLICT (code_typ, code_cd) DO UPDATE SET "
                "  code_nm = EXCLUDED.code_nm, useflg = '1', sort_no = EXCLUDED.sort_no, "
                "  memo = EXCLUDED.memo, updated_at = EXCLUDED.updated_at"
            ),
            {"cd": code_cd, "nm": code_nm, "sort_no": sort_no, "memo": memo, "now": NOW},
        )


def downgrade():
    conn = op.get_bind()

    # 删除 PAY_CONS 类型下的所有编码
    conn.execute(
        sa.text("DELETE FROM tmm31_syscodes WHERE code_typ = 'PAY_CONS'")
    )

    # 删除 SY 中的 PAY_CONS 类型注册
    conn.execute(
        sa.text("DELETE FROM tmm31_syscodes WHERE code_typ = 'SY' AND code_cd = 'PAY_CONS'")
    )
