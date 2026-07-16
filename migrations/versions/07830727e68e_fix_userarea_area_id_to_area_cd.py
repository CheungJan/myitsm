"""fix_userarea_area_id_to_area_cd

Revision ID: 07830727e68e
Revises: b7c8d9e0f1a2
Create Date: 2026-07-14 14:38:08.725379

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '07830727e68e'
down_revision = 'b7c8d9e0f1a2'
branch_labels = None
depends_on = None


def upgrade():
    """tit06_userarea: area_id(int) → area_cd(string20)，对齐 tmm46_area.area_cd 主键类型。"""
    with op.batch_alter_table('tit06_userarea', schema=None) as batch_op:
        batch_op.add_column(sa.Column('area_cd', sa.String(length=20), nullable=True, comment='区域编码（FK→tmm46_area.area_cd）'))
    # 回填 area_cd（通过 tmm46_area.area_id 备份列关联）
    op.execute(
        "UPDATE tit06_userarea SET area_cd = "
        "(SELECT area_cd FROM tmm46_area WHERE tmm46_area.area_id = tit06_userarea.area_id) "
        "WHERE area_cd IS NULL"
    )
    with op.batch_alter_table('tit06_userarea', schema=None) as batch_op:
        batch_op.alter_column('area_cd', existing_type=sa.String(length=20), nullable=False)
        batch_op.drop_constraint(batch_op.f('uq_userarea'), type_='unique')
        batch_op.create_unique_constraint('uq_userarea', ['area_cd', 'user_cd'])
        batch_op.drop_column('area_id')


def downgrade():
    with op.batch_alter_table('tit06_userarea', schema=None) as batch_op:
        batch_op.add_column(sa.Column('area_id', sa.INTEGER(), autoincrement=False, nullable=True, comment='区域ID'))
        batch_op.drop_constraint('uq_userarea', type_='unique')
        batch_op.create_unique_constraint(batch_op.f('uq_userarea'), ['area_id', 'user_cd'])
        batch_op.drop_column('area_cd')
