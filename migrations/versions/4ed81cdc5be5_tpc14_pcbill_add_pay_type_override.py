"""tpc14_pcbill_add_pay_type_override

Revision ID: 4ed81cdc5be5
Revises: dda87465b637
Create Date: 2026-05-27 17:29:28.116640

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4ed81cdc5be5'
down_revision = 'dda87465b637'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tpc14_pcbill', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'pay_type_override',
            sa.String(length=1),
            nullable=True,
            server_default='N',
            comment='是否强制覆盖付款方式一致性(Y/N)，说明追加至memo，操作人/时间复用opercd/gendate'
        ))


def downgrade():
    with op.batch_alter_table('tpc14_pcbill', schema=None) as batch_op:
        batch_op.drop_column('pay_type_override')


def _downgrade_unused():
    # 保留自动生成的其余回滚片段（不执行）
    with op.batch_alter_table('tpc20_requisition_order_link', schema=None) as batch_op:
        batch_op.create_foreign_key(batch_op.f('fk_tpc20_register'), 'tpc12_register', ['rgstbillid'], ['rgstbillid'], ondelete='CASCADE')

    with op.batch_alter_table('tpc17_rpcbilldt', schema=None) as batch_op:
        batch_op.alter_column('line_reason',
               existing_type=sa.VARCHAR(length=100),
               comment=None,
               existing_comment='行级退货原因说明',
               existing_nullable=True)
        batch_op.alter_column('return_amt',
               existing_type=sa.NUMERIC(precision=16, scale=4),
               comment=None,
               existing_comment='退货金额',
               existing_nullable=True)
        batch_op.alter_column('return_price',
               existing_type=sa.NUMERIC(precision=16, scale=4),
               comment=None,
               existing_comment='退货单价',
               existing_nullable=True)

    with op.batch_alter_table('tpc16_rpcbill', schema=None) as batch_op:
        batch_op.alter_column('return_reason',
               existing_type=sa.VARCHAR(length=20),
               comment=None,
               existing_comment='退货原因',
               existing_nullable=True)
        batch_op.alter_column('suppliercd',
               existing_type=sa.VARCHAR(length=8),
               comment='客户编码',
               existing_comment='供应商编码',
               existing_nullable=True)

    with op.batch_alter_table('tpc14_pcbilldt', schema=None) as batch_op:
        batch_op.create_foreign_key(batch_op.f('fk_tpc14_pcbilldt_ref_registerdt'), 'tpc13_registerdt', ['ref_rgstbillid', 'ref_rgstlineno'], ['rgstbillid', 'lineno'], ondelete='RESTRICT')
        batch_op.create_unique_constraint(batch_op.f('tpc14_pcbilldt_pcbillid_lineno_key'), ['pcbillid', 'lineno'], postgresql_nulls_not_distinct=False)
        batch_op.create_index(batch_op.f('ix_tpc14_pcbilldt_ref_reg'), ['ref_rgstbillid', 'ref_rgstlineno'], unique=False)
        batch_op.create_index(batch_op.f('ix_tpc14_pcbilldt_pcbillid'), ['pcbillid'], unique=False)
        batch_op.create_index(batch_op.f('ix_tpc14_pcbilldt_itemcd'), ['itemcd'], unique=False)
        batch_op.alter_column('updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
        batch_op.alter_column('created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
        batch_op.alter_column('settle_amt',
               existing_type=sa.NUMERIC(precision=16, scale=4),
               comment=None,
               existing_comment='结算金额',
               existing_nullable=False)
        batch_op.alter_column('settle_price',
               existing_type=sa.NUMERIC(precision=16, scale=4),
               comment=None,
               existing_comment='结算单价',
               existing_nullable=False)
        batch_op.alter_column('settle_qty',
               existing_type=sa.NUMERIC(precision=12, scale=2),
               comment=None,
               existing_comment='本次结算数量',
               existing_nullable=False)
        batch_op.alter_column('already_settled',
               existing_type=sa.NUMERIC(precision=12, scale=2),
               comment=None,
               existing_comment='该行已结算累计(不含本次)',
               existing_nullable=True,
               existing_server_default=sa.text("'0'::numeric"))
        batch_op.alter_column('received_qty',
               existing_type=sa.NUMERIC(precision=12, scale=2),
               comment=None,
               existing_comment='已入库数量(快照)',
               existing_nullable=True,
               existing_server_default=sa.text("'0'::numeric"))
        batch_op.alter_column('order_qty',
               existing_type=sa.NUMERIC(precision=12, scale=2),
               comment=None,
               existing_comment='订购数量(快照)',
               existing_nullable=True,
               existing_server_default=sa.text("'0'::numeric"))
        batch_op.alter_column('itemcd',
               existing_type=sa.VARCHAR(length=6),
               comment=None,
               existing_comment='物料编码',
               existing_nullable=False)
        batch_op.alter_column('ref_rgstlineno',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='来源订单行号',
               existing_nullable=False)
        batch_op.alter_column('ref_rgstbillid',
               existing_type=sa.VARCHAR(length=8),
               comment=None,
               existing_comment='来源采购订单号',
               existing_nullable=False)
        batch_op.alter_column('lineno',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='行号',
               existing_nullable=False)
        batch_op.alter_column('pcbillid',
               existing_type=sa.VARCHAR(length=8),
               comment=None,
               existing_comment='结算单号',
               existing_nullable=False)

    with op.batch_alter_table('tpc14_pcbill', schema=None) as batch_op:
        batch_op.alter_column('auditdate',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='审核日期',
               existing_nullable=True)
        batch_op.alter_column('auditman',
               existing_type=sa.VARCHAR(length=6),
               comment=None,
               existing_comment='审核人',
               existing_nullable=True)
        batch_op.alter_column('auditflg',
               existing_type=sa.VARCHAR(length=1),
               comment=None,
               existing_comment='审核标志',
               existing_nullable=True,
               existing_server_default=sa.text("'0'::character varying"))
        batch_op.alter_column('whcd',
               existing_type=sa.VARCHAR(length=50),
               comment='入库仓库',
               existing_comment='入库仓库（多选逗号分隔）',
               existing_nullable=True)
        batch_op.alter_column('total_settle_amt',
               existing_type=sa.NUMERIC(precision=16, scale=4),
               comment=None,
               existing_comment='结算总额',
               existing_nullable=True,
               existing_server_default=sa.text("'0'::numeric"))
        batch_op.alter_column('pcdate',
               existing_type=postgresql.TIMESTAMP(),
               comment='采购日期',
               existing_comment='结算日期',
               existing_nullable=True)
        batch_op.alter_column('invoice_date',
               existing_type=sa.DATE(),
               comment=None,
               existing_comment='发票日期',
               existing_nullable=True)
        batch_op.alter_column('invoice_no',
               existing_type=sa.VARCHAR(length=50),
               comment=None,
               existing_comment='发票号码',
               existing_nullable=True)
        batch_op.alter_column('pay_type',
               existing_type=sa.VARCHAR(length=3),
               comment=None,
               existing_comment='付款方式',
               existing_nullable=True,
               existing_server_default=sa.text("'COD'::character varying"))
        batch_op.alter_column('suppliercd',
               existing_type=sa.VARCHAR(length=8),
               comment='客户编码',
               existing_comment='供应商编码',
               existing_nullable=True)
        batch_op.alter_column('ref_rgstbillid',
               existing_type=sa.VARCHAR(length=8),
               comment=None,
               existing_comment='来源采购订单（月结置空）',
               existing_nullable=True)
        batch_op.alter_column('pcbillid',
               existing_type=sa.VARCHAR(length=8),
               comment='采购单号',
               existing_comment='结算单号',
               existing_nullable=False)
        batch_op.drop_column('pay_type_override')

    with op.batch_alter_table('tpc13_registerdt', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(batch_op.f('fk_registerdt_item'), 'tmm12_items', ['itemcd'], ['item_cd'], onupdate='CASCADE')
        batch_op.create_foreign_key(batch_op.f('tpc13_registerdt_rgstbillid_fkey'), 'tpc12_register', ['rgstbillid'], ['rgstbillid'], onupdate='CASCADE', ondelete='CASCADE')
        batch_op.create_unique_constraint(batch_op.f('uq_tpc13_registerdt_bill_line'), ['rgstbillid', 'lineno'], postgresql_nulls_not_distinct=False)

    with op.batch_alter_table('tpc02_pcplandt', schema=None) as batch_op:
        batch_op.create_foreign_key(batch_op.f('fk_pcplandt_item'), 'tmm12_items', ['itemcd'], ['item_cd'], onupdate='CASCADE')

    with op.batch_alter_table('tmm44_pos_r_eid', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('idx_pos_r_eid_useflg'), ['useflg', 'eid'], unique=False)
        batch_op.create_index(batch_op.f('idx_pos_r_eid_eid'), ['eid'], unique=False)

    with op.batch_alter_table('tmm43_eid_track', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('idx_eid_track_type_eid'), ['type', 'eid'], unique=False)
        batch_op.create_index(batch_op.f('idx_eid_track_eid_itemcd'), ['eid', 'itemcd'], unique=False)

    with op.batch_alter_table('tmm42_bomdt', schema=None) as batch_op:
        batch_op.alter_column('bomcd',
               existing_type=sa.String(length=6),
               type_=sa.VARCHAR(length=20),
               existing_comment='BOM编码',
               existing_nullable=False)

    with op.batch_alter_table('tmm41_bom', schema=None) as batch_op:
        batch_op.alter_column('bomcd',
               existing_type=sa.String(length=6),
               type_=sa.VARCHAR(length=20),
               existing_comment='BOM编码',
               existing_nullable=False)

    with op.batch_alter_table('tmm35_cust_pos_rl', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('idx_cust_pos_rl_eid_useflg'), ['eid', 'useflg'], unique=False)

    with op.batch_alter_table('tmm24_custitems', schema=None) as batch_op:
        batch_op.create_foreign_key(batch_op.f('fk_custitems_item'), 'tmm12_items', ['itemcd'], ['item_cd'], onupdate='CASCADE')

    with op.batch_alter_table('tip02_supplier_price', schema=None) as batch_op:
        batch_op.create_foreign_key(batch_op.f('fk_supplier_price_item'), 'tmm12_items', ['itemcd'], ['item_cd'], onupdate='CASCADE')

    op.create_table('backup_tpc20_20260523',
    sa.Column('id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('pcplanid', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('pclineno', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('rgstbillid', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('rgstlineno', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('linkqty', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=True),
    sa.Column('linkstatus', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('gendate', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('upddate', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('opercd', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True)
    )
    # ### end Alembic commands ###
