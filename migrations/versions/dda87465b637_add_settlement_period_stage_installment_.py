"""add settlement_period, settle_stage, installment_no, total_installments, due_date to tpc14_pcbill

Revision ID: dda87465b637
Revises: d48ced158839
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa

revision = "dda87465b637"
down_revision = "d48ced158839"


def upgrade():
    op.add_column("tpc14_pcbill", sa.Column("settlement_period", sa.String(7), comment="月结周期(YYYY-MM)"))
    op.add_column("tpc14_pcbill", sa.Column("settle_stage", sa.String(10), server_default="final", comment="结算阶段(deposit=预付/final=尾款)"))
    op.add_column("tpc14_pcbill", sa.Column("installment_no", sa.Integer(), comment="分期序号"))
    op.add_column("tpc14_pcbill", sa.Column("total_installments", sa.Integer(), comment="分期总期数"))
    op.add_column("tpc14_pcbill", sa.Column("due_date", sa.Date(), comment="付款到期日"))


def downgrade():
    op.drop_column("tpc14_pcbill", "due_date")
    op.drop_column("tpc14_pcbill", "total_installments")
    op.drop_column("tpc14_pcbill", "installment_no")
    op.drop_column("tpc14_pcbill", "settle_stage")
    op.drop_column("tpc14_pcbill", "settlement_period")
