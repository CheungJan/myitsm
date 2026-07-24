"""add unique constraint on tit23_maintenance_d2d (maintenance_id, business_operation_id)

Revision ID: c3d5e7f9a1b2
Revises: b2c4d6e8f0a1
Create Date: 2026-07-19

修复迁移分页 ORDER BY 不稳定导致的重复插入问题。
源库 ortopbitsmdb.tit23_maintenance_d2d 的 PK 为 (maintenance_id, business_operation_id)，
目标库 myitsm 改为自增 id PK 后丢失了业务唯一性约束，导致迁移分页重复读取时
同一 (maintenance_id, business_operation_id) 被多次插入。

本次迁移仅创建唯一约束。数据修复通过 TRUNCATE + 重新迁移完成：
  TRUNCATE tit23_maintenance_d2d CASCADE;
  # 从源库重新迁移（已修复 ORDER BY 全列排序）
  # 然后执行本迁移加约束

注意：直接执行本迁移前若表仍有重复行，约束创建会失败。需先 TRUNCATE + 重迁移。
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3d5e7f9a1b2"
down_revision = "b2c4d6e8f0a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级：创建唯一约束。"""
    op.create_unique_constraint(
        "uq_maintenance_d2d_op",
        "tit23_maintenance_d2d",
        ["maintenance_id", "business_operation_id"],
    )


def downgrade() -> None:
    """降级：删除唯一约束。"""
    op.drop_constraint("uq_maintenance_d2d_op", "tit23_maintenance_d2d", type_="unique")

