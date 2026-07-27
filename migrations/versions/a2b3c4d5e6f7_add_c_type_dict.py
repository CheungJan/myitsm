"""add_c_type_dict

Revision ID: a2b3c4d5e6f7
Revises: d1e2f3a4b5c6
Create Date: 2026-07-21 14:05:00

变更:
  - 在 tmm31_syscodes 注册 C_TYPE 类型 (code_typ='SY', code_cd='C_TYPE')
  - 插入 C_TYPE 操作类型字典数据（TIT25_ACCESSORIES_UPDATE.c_type 使用）
  - 字典值：1=维修 / 2=购买 / 3=纯服务费 / 4=整机更换 / 5=耗材/线材
  - 配合事项 C1 TIT25 模型扩展：c_type 枚举从 1/2/4 扩展为 1-5
  - 与 PAY_SVC/PAY_CONS 级联：c_type=3 → PAY_SVC，c_type=5 → PAY_CONS
  - 注：code_typ 字段 VARCHAR(10)，C_TYPE（6 字符）符合限制
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = 'a2b3c4d5e6f7'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc)

# C_TYPE 字典数据：TIT25_ACCESSORIES_UPDATE 操作类型
C_TYPE_ITEMS = [
    ("1", "维修", "保内换件，payje=price 同步", 1),
    ("2", "购买", "客户购买配件，payje=price 同步", 2),
    ("3", "纯服务费", "上门费/检测费/软件服务费，payje 手填+paytype 走 PAY_SVC 字典", 3),
    ("4", "整机更换", "换整机，payje=price 同步", 4),
    ("5", "耗材/线材", "线材/枪线/耗材等，payje 手填+paytype 走 PAY_CONS 字典", 5),
]


def upgrade():
    conn = op.get_bind()

    # 1. 注册 C_TYPE 类型到 SY（系统字典类型注册表）
    conn.execute(
        sa.text(
            "INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, created_at, updated_at) "
            "VALUES ('SY', 'C_TYPE', '操作类型', '1', 0, :now, :now) "
            "ON CONFLICT (code_typ, code_cd) DO NOTHING"
        ),
        {"now": NOW},
    )

    # 2. 插入 C_TYPE 字典明细
    for code_cd, code_nm, memo, sort_no in C_TYPE_ITEMS:
        conn.execute(
            sa.text(
                "INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, memo, created_at, updated_at) "
                "VALUES ('C_TYPE', :cd, :nm, '1', :sort_no, :memo, :now, :now) "
                "ON CONFLICT (code_typ, code_cd) DO UPDATE SET "
                "  code_nm = EXCLUDED.code_nm, useflg = '1', sort_no = EXCLUDED.sort_no, "
                "  memo = EXCLUDED.memo, updated_at = EXCLUDED.updated_at"
            ),
            {"cd": code_cd, "nm": code_nm, "sort_no": sort_no, "memo": memo, "now": NOW},
        )


def downgrade():
    conn = op.get_bind()

    # 删除 C_TYPE 类型下的所有编码
    conn.execute(
        sa.text("DELETE FROM tmm31_syscodes WHERE code_typ = 'C_TYPE'")
    )

    # 删除 SY 中的 C_TYPE 类型注册
    conn.execute(
        sa.text("DELETE FROM tmm31_syscodes WHERE code_typ = 'SY' AND code_cd = 'C_TYPE'")
    )
