"""add_warehouse_area_id_user_default_whcd

Revision ID: f6a7b8c9d0e1
Revises: d4e5f6a7b8c9
Create Date: 2026-07-20 17:05:00

变更:
  - twh01_warehouse 新增 area_id 字段（FK→tmm46_area.area_cd，仓库位置属性）
  - tmc13_users 新增 default_whcd 字段（FK→twh01_warehouse.whcd，用户默认仓库）
  - 工程师虚拟仓命名治理方案 B：仓库存位置，用户存默认仓库，维度解耦
  - 配合事项 12 新配件选择：通过 User.default_whcd 找工程师虚拟仓库存
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f6a7b8c9d0e1'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    # 1. twh01_warehouse 新增 area_id 字段
    op.add_column(
        'twh01_warehouse',
        sa.Column(
            'area_id',
            sa.String(20),
            nullable=True,
            comment='所属划区（FK→tmm46_area.area_cd，仓库位置属性）',
        ),
    )
    op.create_foreign_key(
        'fk_warehouse_area',
        'twh01_warehouse',
        'tmm46_area',
        ['area_id'],
        ['area_cd'],
    )

    # 2. tmc13_users 新增 default_whcd 字段
    op.add_column(
        'tmc13_users',
        sa.Column(
            'default_whcd',
            sa.String(2),
            nullable=True,
            comment='默认仓库（FK→twh01_warehouse.whcd，工程师虚拟仓场景使用）',
        ),
    )
    op.create_foreign_key(
        'fk_user_default_warehouse',
        'tmc13_users',
        'twh01_warehouse',
        ['default_whcd'],
        ['whcd'],
    )

    # 3. 数据回填：工程师虚拟仓的 area_id 从 tit06_userarea 反查
    #    工程师仓 whnm 已改为纯姓名（= user_cd），通过 tit06_userarea.user_cd 匹配
    op.execute(
        """
        UPDATE twh01_warehouse w
        SET area_id = ua.area_cd
        FROM tit06_userarea ua
        WHERE w.whnm = ua.user_cd
          AND w.area_id IS NULL
        """
    )

    # 4. 数据回填：工程师用户的 default_whcd 从 twh01_warehouse 反查
    #    工程师仓 whnm 已改为纯姓名（= user_cd），直接匹配
    op.execute(
        """
        UPDATE tmc13_users u
        SET default_whcd = w.whcd
        FROM twh01_warehouse w
        WHERE w.whnm = u.user_cd
          AND u.default_whcd IS NULL
        """
    )


def downgrade():
    # 删除 tmc13_users.default_whcd
    op.drop_constraint('fk_user_default_warehouse', 'tmc13_users', type_='foreignkey')
    op.drop_column('tmc13_users', 'default_whcd')

    # 删除 twh01_warehouse.area_id
    op.drop_constraint('fk_warehouse_area', 'twh01_warehouse', type_='foreignkey')
    op.drop_column('twh01_warehouse', 'area_id')
