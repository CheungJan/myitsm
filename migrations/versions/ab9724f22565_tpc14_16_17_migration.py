"""TPC14/16/17迁移 — 结算明细表+字段补全+重命名

Changes:
1. tpc13_registerdt: ADD UNIQUE constraint on (rgstbillid, lineno)
2. tpc14_pcbill: Rename custcd→suppliercd, add new columns
3. tpc14_pcbilldt: NEW TABLE for settlement details
4. tpc16_rpcbill: Rename custcd→suppliercd, add return_reason
5. tpc17_rpcbilldt: Add return_price, return_amt, line_reason

Revision ID: ab9724f22565
Revises: a34751d36973
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa


revision = "ab9724f22565"
down_revision = "a34751d36973"


def upgrade():
    # 1. tpc13_registerdt: Add UNIQUE constraint on (rgstbillid, lineno)
    #    Data verified: no duplicates exist (1152 rows, GROUP BY check passed)
    op.execute("""
        ALTER TABLE tpc13_registerdt
        ADD CONSTRAINT uq_tpc13_registerdt_bill_line
        UNIQUE (rgstbillid, lineno)
    """)

    # 2. tpc14_pcbill: Rename custcd → suppliercd (table is empty, safe)
    op.execute("ALTER TABLE tpc14_pcbill RENAME COLUMN custcd TO suppliercd")

    # tpc14_pcbill: Add new columns
    op.add_column("tpc14_pcbill",
                  sa.Column("ref_rgstbillid", sa.String(8), nullable=True))
    op.add_column("tpc14_pcbill",
                  sa.Column("pay_type", sa.String(3), nullable=True,
                            server_default="COD"))
    op.add_column("tpc14_pcbill",
                  sa.Column("invoice_no", sa.String(50), nullable=True))
    op.add_column("tpc14_pcbill",
                  sa.Column("invoice_date", sa.Date(), nullable=True))
    op.add_column("tpc14_pcbill",
                  sa.Column("total_settle_amt", sa.Numeric(16, 4), nullable=True,
                            server_default="0"))
    op.add_column("tpc14_pcbill",
                  sa.Column("auditflg", sa.String(1), nullable=True,
                            server_default="0"))
    op.add_column("tpc14_pcbill",
                  sa.Column("auditman", sa.String(6), nullable=True))
    op.add_column("tpc14_pcbill",
                  sa.Column("auditdate", sa.TIMESTAMP(), nullable=True))

    # 3. tpc14_pcbilldt: NEW TABLE — settlement detail lines
    op.create_table(
        "tpc14_pcbilldt",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pcbillid", sa.String(8), nullable=False),
        sa.Column("lineno", sa.Integer(), nullable=False),
        sa.Column("ref_rgstbillid", sa.String(8), nullable=False),
        sa.Column("ref_rgstlineno", sa.Integer(), nullable=False),
        sa.Column("itemcd", sa.String(6), nullable=False),
        sa.Column("order_qty", sa.Numeric(12, 2), nullable=True,
                  server_default="0"),
        sa.Column("received_qty", sa.Numeric(12, 2), nullable=True,
                  server_default="0"),
        sa.Column("already_settled", sa.Numeric(12, 2), nullable=True,
                  server_default="0"),
        sa.Column("settle_qty", sa.Numeric(12, 2), nullable=False),
        sa.Column("settle_price", sa.Numeric(16, 4), nullable=False),
        sa.Column("settle_amt", sa.Numeric(16, 4), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=True,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=True,
                  server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pcbillid", "lineno"),
    )

    # FK: pcbillid → tpc14_pcbill.pcbillid ON DELETE CASCADE
    op.execute("""
        ALTER TABLE tpc14_pcbilldt
        ADD CONSTRAINT fk_tpc14_pcbilldt_pcbillid
        FOREIGN KEY (pcbillid)
        REFERENCES tpc14_pcbill(pcbillid)
        ON DELETE CASCADE
    """)

    # FK: (ref_rgstbillid, ref_rgstlineno) → tpc13_registerdt(rgstbillid, lineno)
    #    Requires the UNIQUE constraint on tpc13_registerdt created above
    op.execute("""
        ALTER TABLE tpc14_pcbilldt
        ADD CONSTRAINT fk_tpc14_pcbilldt_ref_registerdt
        FOREIGN KEY (ref_rgstbillid, ref_rgstlineno)
        REFERENCES tpc13_registerdt(rgstbillid, lineno)
        ON DELETE RESTRICT
    """)

    # Indexes on tpc14_pcbilldt
    op.create_index("ix_tpc14_pcbilldt_pcbillid", "tpc14_pcbilldt",
                    ["pcbillid"])
    op.create_index("ix_tpc14_pcbilldt_ref_reg", "tpc14_pcbilldt",
                    ["ref_rgstbillid", "ref_rgstlineno"])
    op.create_index("ix_tpc14_pcbilldt_itemcd", "tpc14_pcbilldt",
                    ["itemcd"])

    # 4. tpc16_rpcbill: Rename custcd → suppliercd (table is empty, safe)
    op.execute("ALTER TABLE tpc16_rpcbill RENAME COLUMN custcd TO suppliercd")

    # tpc16_rpcbill: Add return_reason
    op.add_column("tpc16_rpcbill",
                  sa.Column("return_reason", sa.String(20), nullable=True))

    # 5. tpc17_rpcbilldt: Add columns
    op.add_column("tpc17_rpcbilldt",
                  sa.Column("return_price", sa.Numeric(16, 4), nullable=True))
    op.add_column("tpc17_rpcbilldt",
                  sa.Column("return_amt", sa.Numeric(16, 4), nullable=True))
    op.add_column("tpc17_rpcbilldt",
                  sa.Column("line_reason", sa.String(100), nullable=True))


def downgrade():
    # Reverse in reverse order

    # 5. tpc17_rpcbilldt: Drop columns
    op.drop_column("tpc17_rpcbilldt", "line_reason")
    op.drop_column("tpc17_rpcbilldt", "return_amt")
    op.drop_column("tpc17_rpcbilldt", "return_price")

    # 4. tpc16_rpcbill: Drop return_reason, rename suppliercd → custcd
    op.drop_column("tpc16_rpcbill", "return_reason")
    op.execute("ALTER TABLE tpc16_rpcbill RENAME COLUMN suppliercd TO custcd")

    # 3. tpc14_pcbilldt: Drop indexes, drop FK, drop table
    op.drop_index("ix_tpc14_pcbilldt_itemcd", "tpc14_pcbilldt")
    op.drop_index("ix_tpc14_pcbilldt_ref_reg", "tpc14_pcbilldt")
    op.drop_index("ix_tpc14_pcbilldt_pcbillid", "tpc14_pcbilldt")
    op.execute("""
        ALTER TABLE tpc14_pcbilldt
        DROP CONSTRAINT IF EXISTS fk_tpc14_pcbilldt_ref_registerdt
    """)
    op.execute("""
        ALTER TABLE tpc14_pcbilldt
        DROP CONSTRAINT IF EXISTS fk_tpc14_pcbilldt_pcbillid
    """)
    op.drop_table("tpc14_pcbilldt")

    # 2. tpc14_pcbill: Drop columns, rename suppliercd → custcd
    op.drop_column("tpc14_pcbill", "auditdate")
    op.drop_column("tpc14_pcbill", "auditman")
    op.drop_column("tpc14_pcbill", "auditflg")
    op.drop_column("tpc14_pcbill", "total_settle_amt")
    op.drop_column("tpc14_pcbill", "invoice_date")
    op.drop_column("tpc14_pcbill", "invoice_no")
    op.drop_column("tpc14_pcbill", "pay_type")
    op.drop_column("tpc14_pcbill", "ref_rgstbillid")
    op.execute("ALTER TABLE tpc14_pcbill RENAME COLUMN suppliercd TO custcd")

    # 1. tpc13_registerdt: Drop UNIQUE constraint
    op.execute("""
        ALTER TABLE tpc13_registerdt
        DROP CONSTRAINT IF EXISTS uq_tpc13_registerdt_bill_line
    """)
