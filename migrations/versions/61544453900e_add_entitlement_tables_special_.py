"""add entitlement tables special_agreement + service_contract

Revision ID: 61544453900e
Revises: f1fd3e67c4a6
Create Date: 2026-07-28

P2 Entitlement 完整化：新增特殊客户协议、维保合同两张表，
用于 entitlement_service.resolve_entitlement() 优先级 1-2 判定。
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "61544453900e"
down_revision = "f1fd3e67c4a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建 tit71_special_agreement 和 tit72_service_contract 表。"""
    now_default = sa.text("CURRENT_TIMESTAMP")
    op.create_table(
        "tit71_special_agreement",
        sa.Column("agreement_id", sa.String(20), primary_key=True, comment="协议ID"),
        sa.Column("cust_cd", sa.String(8), nullable=False, comment="客户编码"),
        sa.Column("agreement_nm", sa.String(100), comment="协议名称"),
        sa.Column("is_free", sa.String(1), server_default="1", comment="是否免费: 1=免费 0=收费"),
        sa.Column("effective_date", sa.Date, nullable=False, comment="生效日期"),
        sa.Column("expire_date", sa.Date, comment="失效日期（空=长期有效）"),
        sa.Column("remark", sa.String(200), comment="备注"),
        sa.Column("useflg", sa.String(1), server_default="1", comment="有效标志"),
        sa.Column("creator", sa.String(20), comment="创建人"),
        sa.Column("updator", sa.String(20), comment="更新人"),
        sa.Column("created_at", sa.DateTime, server_default=now_default, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=now_default, comment="更新时间"),
    )
    op.create_index(
        "ix_tit71_special_agreement_cust_cd",
        "tit71_special_agreement",
        ["cust_cd"],
    )

    op.create_table(
        "tit72_service_contract",
        sa.Column("contract_id", sa.String(20), primary_key=True, comment="合同ID"),
        sa.Column("contract_no", sa.String(30), comment="合同编号"),
        sa.Column("cust_cd", sa.String(8), comment="客户编码"),
        sa.Column("eid", sa.String(13), comment="设备ID"),
        sa.Column("contract_nm", sa.String(100), comment="合同名称"),
        sa.Column("is_free", sa.String(1), server_default="1", comment="是否免费: 1=免费 0=收费"),
        sa.Column("effective_date", sa.Date, nullable=False, comment="生效日期"),
        sa.Column("expire_date", sa.Date, nullable=False, comment="失效日期"),
        sa.Column("remark", sa.String(200), comment="备注"),
        sa.Column("useflg", sa.String(1), server_default="1", comment="有效标志"),
        sa.Column("creator", sa.String(20), comment="创建人"),
        sa.Column("updator", sa.String(20), comment="更新人"),
        sa.Column("created_at", sa.DateTime, server_default=now_default, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=now_default, comment="更新时间"),
    )
    op.create_index(
        "ix_tit72_service_contract_cust_cd",
        "tit72_service_contract",
        ["cust_cd"],
    )
    op.create_index(
        "ix_tit72_service_contract_eid",
        "tit72_service_contract",
        ["eid"],
    )


def downgrade() -> None:
    """删除 tit72_service_contract 和 tit71_special_agreement 表。"""
    op.drop_index("ix_tit72_service_contract_eid", table_name="tit72_service_contract")
    op.drop_index("ix_tit72_service_contract_cust_cd", table_name="tit72_service_contract")
    op.drop_table("tit72_service_contract")
    op.drop_index("ix_tit71_special_agreement_cust_cd", table_name="tit71_special_agreement")
    op.drop_table("tit71_special_agreement")
