"""add notify_channel + template ref_type/is_default/sort_no

Revision ID: b2c4d6e8f0a1
Revises: a1b3c5d7e9f0
Create Date: 2026-07-17

阶段：派工与通知优化第二阶段。
1) tit30_dispatch_rule 增加 notify_channel 字段（自动派工通知渠道）。
2) tntf01_template 增加 ref_type/is_default/sort_no 字段，支持按业务类型筛选默认模板与自定义排序。
3) 预置 DISPATCH 模板 ref_type='dispatch'、is_default='1'。
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b2c4d6e8f0a1"
down_revision = "a1b3c5d7e9f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级：加字段 + 标记默认模板。"""
    # 1) 派单规则加通知渠道
    op.add_column(
        "tit30_dispatch_rule",
        sa.Column(
            "notify_channel",
            sa.String(10),
            nullable=True,
            server_default="internal",
            comment="自动派工通知渠道: internal/email/sms/dingtalk/wecom/feishu/ntfy",
        ),
    )
    op.add_column(
        "tit30_dispatch_rule",
        sa.Column(
            "auto_dispatch",
            sa.String(1),
            nullable=True,
            server_default="1",
            comment="自动派单开关: 1=启用/0=禁用",
        ),
    )

    # 2) 通知模板加业务类型/默认/排序
    op.add_column(
        "tntf01_template",
        sa.Column(
            "ref_type",
            sa.String(20),
            nullable=True,
            comment="业务类型: dispatch/maintenance/renovate/open/change/recycle 等",
        ),
    )
    op.add_column(
        "tntf01_template",
        sa.Column(
            "is_default",
            sa.String(1),
            nullable=True,
            server_default="0",
            comment="是否该 ref_type 下默认: 1=是/0=否",
        ),
    )
    op.add_column(
        "tntf01_template",
        sa.Column(
            "sort_no",
            sa.Integer(),
            nullable=True,
            server_default="0",
            comment="排序号（小优先）",
        ),
    )

    # 3) 预置 DISPATCH 模板标记为 dispatch 默认
    op.execute(
        sa.text(
            """
            UPDATE tntf01_template
            SET ref_type = 'dispatch', is_default = '1', sort_no = 10
            WHERE template_id = 'DISPATCH'
            """
        )
    )


def downgrade() -> None:
    """回滚：移除字段。"""
    op.drop_column("tntf01_template", "sort_no")
    op.drop_column("tntf01_template", "is_default")
    op.drop_column("tntf01_template", "ref_type")
    op.drop_column("tit30_dispatch_rule", "auto_dispatch")
    op.drop_column("tit30_dispatch_rule", "notify_channel")
