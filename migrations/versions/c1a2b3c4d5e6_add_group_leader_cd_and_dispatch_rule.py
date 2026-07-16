"""add tmc12_groups.leader_cd and tit30_dispatch_rule

Revision ID: c1a2b3c4d5e6
Revises: b9c8d7e6f5a4
Create Date: 2026-07-15

阶段：派工与通知优化第一阶段。
1) tmc12_groups 增加 leader_cd 字段（组长用户编码）。
2) 新增 tit30_dispatch_rule 派单规则表，支持故障类型 + 两级兜底链路。
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c1a2b3c4d5e6"
down_revision = "b9c8d7e6f5a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级：加 leader_cd 字段 + 建 tit30_dispatch_rule 表。"""
    op.add_column(
        "tmc12_groups",
        sa.Column("leader_cd", sa.String(6), nullable=True, comment="组长用户编码"),
    )

    op.create_table(
        "tit30_dispatch_rule",
        sa.Column("rule_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("rule_name", sa.String(50), nullable=False, comment="规则名称"),
        sa.Column("priority", sa.Integer(), nullable=True, comment="优先级（小优先）"),
        sa.Column("fault_type", sa.String(2), nullable=True, comment="故障类型"),
        sa.Column("store_id", sa.String(8), nullable=True, comment="门店编码"),
        sa.Column(
            "target_type",
            sa.String(20),
            nullable=True,
            comment="派单目标: area_manager/group_leader/manual",
        ),
        sa.Column("target_value", sa.String(20), nullable=True, comment="目标值"),
        sa.Column("fallback_type", sa.String(20), nullable=True, comment="一级兜底目标"),
        sa.Column("fallback_value", sa.String(20), nullable=True, comment="一级兜底值"),
        sa.Column(
            "ultimate_fallback_type", sa.String(20), nullable=True, comment="最终兜底目标"
        ),
        sa.Column(
            "ultimate_fallback_value", sa.String(20), nullable=True, comment="最终兜底值"
        ),
        sa.Column("useflg", sa.String(1), nullable=True, comment="有效标志"),
        sa.Column("creator", sa.String(6), nullable=True, comment="创建人"),
        sa.Column("create_time", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("updator", sa.String(6), nullable=True, comment="更新人"),
        sa.Column("update_time", sa.DateTime(), nullable=True, comment="更新时间"),
        comment="派单规则表",
    )

    # 预置 4 条派单规则（按故障类型细分 + 兜底）
    op.execute(
        sa.text(
            """
            INSERT INTO tit30_dispatch_rule
                (rule_name, priority, fault_type, target_type, target_value,
                 fallback_type, fallback_value,
                 ultimate_fallback_type, ultimate_fallback_value,
                 useflg, creator, create_time)
            VALUES
                ('POS故障→区域负责人', 10, '1', 'area_manager', NULL,
                 'group_leader', 'A1',
                 'manual', NULL,
                 '1', 'SYSTEM', NOW()),
                ('视频故障→A1组长', 20, '2', 'group_leader', 'A1',
                 'group_leader', 'TT',
                 'manual', NULL,
                 '1', 'SYSTEM', NOW()),
                ('取机故障→区域负责人', 30, '3', 'area_manager', NULL,
                 'group_leader', 'A1',
                 'manual', NULL,
                 '1', 'SYSTEM', NOW()),
                ('兜底→A1组长', 99, NULL, 'group_leader', 'A1',
                 'manual', NULL,
                 'manual', NULL,
                 '1', 'SYSTEM', NOW())
            """
        )
    )

    # 预置 TT 组组长 1612（A1 组组长待业务确认，暂留空）
    op.execute(
        sa.text(
            """
            UPDATE tmc12_groups SET leader_cd = '1612'
            WHERE group_cd = 'TT'
            """
        )
    )

    # 预置 DISPATCH 通知模板（站内通知，Jinja2 占位符，创建时一次性渲染快照）
    op.execute(
        sa.text(
            """
            INSERT INTO tntf01_template
                (template_id, template_name, channel, subject, body,
                 opercd, gendate, upddate, useflg, created_at, updated_at)
            VALUES
                ('DISPATCH', '派工通知模板', 'internal',
                 '新派工通知：维护单 {{ maintenance_id }}',
                 '维护单 {{ maintenance_id }}（门店 {{ store_id }}）已派给 {{ accpectder_name }}（组 {{ accpectd_group }}），故障类型 {{ fault_type }}，请及时处理。',
                 'SYSTEM', NOW(), NOW(), '1', NOW(), NOW())
            ON CONFLICT (template_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    """回滚：删表 + 删字段 + 删模板。"""
    op.execute(sa.text("DELETE FROM tntf01_template WHERE template_id = 'DISPATCH'"))
    op.drop_table("tit30_dispatch_rule")
    op.drop_column("tmc12_groups", "leader_cd")
