"""remap_pb_invtyp_to_new_codes

Revision ID: a58d822bc65c
Revises: 6740347934e6
Create Date: 2026-06-02 16:27:07.472061

变更:
  - twh15_out / twh13_in / twh12_detaildt 的 invtyp 列从 VARCHAR(1) 扩为 VARCHAR(2)
  - PB 历史数据的 invtyp 从 PB 原始编码映射为新系统 OV/IV 编码
  - 截止日期 2026-01-01（新系统上线前），含 opercd='SYS' 的迁移数据
"""
from alembic import op
import sqlalchemy as sa

revision = 'a58d822bc65c'
down_revision = '6740347934e6'
branch_labels = None
depends_on = None

# PB → 新系统映射表
OV_MAP = {
    "1": "6",  # PB退货出库    → OV=6
    "2": "5",  # PB质检出库    → OV=5
    "3": "2",  # PB维护出库    → OV=2
    "4": "8",  # PB生产出库    → OV=8
    "5": "9",  # PB返修出库    → OV=9
    "6": "4",  # PB借出出库    → OV=4
    "7": "3",  # PB调拨出库    → OV=3
    "8": "1",  # PB销售出库    → OV=1
    "9": "8",  # PB其他出库    → OV=8
}

IV_MAP = {
    "1": "1",   # PB采购入库    → IV=1
    "2": "11",  # PB质检入库    → IV=11
    "3": "3",   # PB维护入库    → IV=3
    "4": "8",   # PB生产入库    → IV=8
    "5": "9",   # PB返修入库    → IV=9
    "6": "5",   # PB借出归还    → IV=5
    "7": "4",   # PB调拨入库    → IV=4
    "8": "2",   # PB销售退货    → IV=2
    "9": "7",   # PB回收入库    → IV=7
    "C": "7",   # PB遗留        → IV=7
    "S": "7",   # PB遗留        → IV=7
}


def upgrade():
    conn = op.get_bind()

    # 1. 加宽列
    op.alter_column("twh15_out", "invtyp", type_=sa.String(2), existing_type=sa.String(1))
    op.alter_column("twh13_in", "invtyp", type_=sa.String(2), existing_type=sa.String(1))
    op.alter_column("twh12_detaildt", "invtyp", type_=sa.String(2), existing_type=sa.String(1))

    # 2. 出库单: PB编码 → 新编码
    for old, new in OV_MAP.items():
        conn.execute(
            sa.text(
                "UPDATE twh15_out SET invtyp = :new "
                "WHERE invtyp = :old AND gendate < '2026-01-01'"
            ),
            {"old": old, "new": new},
        )

    # 3. 入库单: PB编码 → 新编码
    for old, new in IV_MAP.items():
        conn.execute(
            sa.text(
                "UPDATE twh13_in SET invtyp = :new "
                "WHERE invtyp = :old AND gendate < '2026-01-01'"
            ),
            {"old": old, "new": new},
        )


def downgrade():
    conn = op.get_bind()

    # 反向映射
    ov_rev = {v: k for k, v in OV_MAP.items()}
    iv_rev = {v: k for k, v in IV_MAP.items()}

    for new, old in ov_rev.items():
        conn.execute(
            sa.text(
                "UPDATE twh15_out SET invtyp = :old "
                "WHERE invtyp = :new AND gendate < '2026-01-01'"
            ),
            {"old": old, "new": new},
        )

    for new, old in iv_rev.items():
        conn.execute(
            sa.text(
                "UPDATE twh13_in SET invtyp = :old "
                "WHERE invtyp = :new AND gendate < '2026-01-01'"
            ),
            {"old": old, "new": new},
        )

    # 缩窄列（如果新编码中有 '10','11' 需先清掉，否则会失败）
    op.alter_column("twh12_detaildt", "invtyp", type_=sa.String(1), existing_type=sa.String(2))
    op.alter_column("twh13_in", "invtyp", type_=sa.String(1), existing_type=sa.String(2))
    op.alter_column("twh15_out", "invtyp", type_=sa.String(1), existing_type=sa.String(2))
