"""add_closure_reason_dict

Revision ID: c1d2e3f4a5b6
Revises: f6a7b8c9d0e1
Create Date: 2026-07-20 21:40:00

变更:
  - 在 tmm31_syscodes 注册 CLO_REASON 类型 (code_typ='SY', code_cd='CLO_REASON')
  - 插入 CLO_REASON 关闭原因字典数据（仅 d2d_result='3' 关闭时使用）
  - 字典值：1=正常解决 / 2=客户拒修 / 3=非设备问题 / 4=重复报修 / 5=转其他团队
  - 配合事项 18 离店解决四要素结构化：d2d_result 用 ZT 码值，closure_reason 区分关闭原因
  - 行业参考：ITSM/ITIL Closure Category、Salesforce Case Reason、ServiceNow Close Code
  - 注：code_typ 字段 VARCHAR(10)，故用 CLO_REASON（9 字符）而非 CLOSURE_REASON（14 字符）
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc)

# CLO_REASON 字典数据：关闭原因（code_typ 列 VARCHAR(10)，用 CLO_REASON 9 字符）
CLOSURE_REASON_ITEMS = [
    ("1", "正常解决", "工程师现场解决关闭", 1),
    ("2", "客户拒修", "客户拒绝维修关闭", 2),
    ("3", "非设备问题", "经排查非设备故障关闭", 3),
    ("4", "重复报修", "重复报修关闭", 4),
    ("5", "转其他团队", "转其他团队处理关闭", 5),
]


def upgrade():
    conn = op.get_bind()

    # 1. 注册 CLO_REASON 类型到 SY（系统字典类型注册表）
    conn.execute(
        sa.text(
            "INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, created_at, updated_at) "
            "VALUES ('SY', 'CLO_REASON', '关闭原因', '1', 0, :now, :now) "
            "ON CONFLICT (code_typ, code_cd) DO NOTHING"
        ),
        {"now": NOW},
    )

    # 2. 插入 CLO_REASON 字典明细
    for code_cd, code_nm, memo, sort_no in CLOSURE_REASON_ITEMS:
        conn.execute(
            sa.text(
                "INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, memo, created_at, updated_at) "
                "VALUES ('CLO_REASON', :cd, :nm, '1', :sort_no, :memo, :now, :now) "
                "ON CONFLICT (code_typ, code_cd) DO UPDATE SET "
                "  code_nm = EXCLUDED.code_nm, useflg = '1', sort_no = EXCLUDED.sort_no, "
                "  memo = EXCLUDED.memo, updated_at = EXCLUDED.updated_at"
            ),
            {"cd": code_cd, "nm": code_nm, "sort_no": sort_no, "memo": memo, "now": NOW},
        )


def downgrade():
    conn = op.get_bind()

    # 删除 CLO_REASON 类型下的所有编码
    conn.execute(
        sa.text("DELETE FROM tmm31_syscodes WHERE code_typ = 'CLO_REASON'")
    )

    # 删除 SY 中的 CLO_REASON 类型注册
    conn.execute(
        sa.text("DELETE FROM tmm31_syscodes WHERE code_typ = 'SY' AND code_cd = 'CLO_REASON'")
    )
