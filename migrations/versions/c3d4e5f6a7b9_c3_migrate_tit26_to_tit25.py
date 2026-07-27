"""C3: migrate tit26_paylist to tit25_accessories_update (c_type=3/5)

Revision ID: c3d4e5f6a7b9
Revises: 00d946c2e6b2
Create Date: 2026-07-22 12:05:00

变更:
  - 历史数据迁移：TIT26_PAYLIST → TIT25_ACCESSORIES_UPDATE（c_type=3/5）
  - 三轮匹配分类（审核意见 3）：
    第 1 轮：paytype = tmm12_items.itemnm 精确匹配且 consume='1' → c_type='5'（耗材/线材）
    第 2 轮：LIKE '%...%' 双向模糊匹配且 consume='1' → c_type='5'
    第 3 轮：未匹配 → c_type='3'（纯服务费）
  - 字段映射：useflg→auditflg、receiptid→receipt_id、deliveryid→delivery_id
    c_type=5 时 accessories_type=paytype（耗材名称存名称字段）
    c_type=3 时 paytype 保留原值
  - business_operation_id 冲突处理：TIT25/TIT26 共享同一 maintenance_id 下序号空间，
    迁移时按 maintenance_id 重新分配（TIT25 当前最大值 + ROW_NUMBER），避免与已有记录冲突
  - 溯源标记：description 前缀加 [MIGRATED_FROM_TIT26:{id}]，便于回滚定位
  - TIT26 保留不删，仅标记 useflg='0' 只读
"""
from alembic import op
from sqlalchemy import text as sa_text

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b9'
down_revision = '00d946c2e6b2'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # 第 1+2 轮：耗材/线材（paytype 匹配 tmm12_items.consume='1'）→ c_type='5'
    # 精确匹配优先，模糊匹配降级；business_operation_id 按 maintenance_id 重新分配
    bind.execute(sa_text("""
        INSERT INTO tit25_accessories_update (
            maintenance_id, business_operation_id, store_id, engineer_id,
            receipt_id, delivery_id, accessories_type, description,
            create_time, creator, update_time, updator,
            created_at, updated_at,
            auditflg, c_type, payje, paydate, memo, version
        )
        WITH ranked AS (
            SELECT
                p.id AS src_id,
                p.maintenance_id,
                p.business_operation_id AS src_seq,
                p.store_id,
                p.engineer_id,
                p.receipt_id,
                p.delivery_id,
                p.paytype,
                p.payje,
                p.paydate,
                p.memo,
                p.useflg,
                p.create_time,
                p.creator,
                p.update_time,
                p.updator,
                ROW_NUMBER() OVER (PARTITION BY p.maintenance_id ORDER BY p.id) AS rn
            FROM tit26_paylist p
            WHERE p.useflg = '1'
              AND EXISTS (
                SELECT 1 FROM tmm12_items i
                WHERE i.consume = '1'
                  AND (p.paytype LIKE '%' || i.item_nm || '%'
                       OR i.item_nm LIKE '%' || p.paytype || '%')
              )
        ),
        max_seq AS (
            SELECT maintenance_id, COALESCE(MAX(business_operation_id), 0) AS mx
            FROM tit25_accessories_update
            GROUP BY maintenance_id
        )
        SELECT
            r.maintenance_id,
            COALESCE(m.mx, 0) + r.rn AS business_operation_id,
            r.store_id,
            r.engineer_id,
            r.receipt_id,
            r.delivery_id,
            r.paytype AS accessories_type,
            '[MIGRATED_FROM_TIT26:' || r.src_id || '] ' || COALESCE(r.memo, '') AS description,
            r.create_time,
            r.creator,
            r.update_time,
            r.updator,
            COALESCE(r.create_time, NOW()) AS created_at,
            COALESCE(r.update_time, NOW()) AS updated_at,
            r.useflg AS auditflg,
            '5' AS c_type,
            r.payje,
            r.paydate,
            r.memo,
            1 AS version
        FROM ranked r
        LEFT JOIN max_seq m ON m.maintenance_id = r.maintenance_id
    """))

    # 第 3 轮：纯服务费（未匹配耗材）→ c_type='3'
    bind.execute(sa_text("""
        INSERT INTO tit25_accessories_update (
            maintenance_id, business_operation_id, store_id, engineer_id,
            receipt_id, delivery_id, description,
            create_time, creator, update_time, updator,
            created_at, updated_at,
            auditflg, c_type, payje, paytype, paydate, memo, version
        )
        WITH ranked AS (
            SELECT
                p.id AS src_id,
                p.maintenance_id,
                p.store_id,
                p.engineer_id,
                p.receipt_id,
                p.delivery_id,
                p.paytype,
                p.payje,
                p.paydate,
                p.memo,
                p.useflg,
                p.create_time,
                p.creator,
                p.update_time,
                p.updator,
                ROW_NUMBER() OVER (PARTITION BY p.maintenance_id ORDER BY p.id) AS rn
            FROM tit26_paylist p
            WHERE p.useflg = '1'
              AND NOT EXISTS (
                SELECT 1 FROM tmm12_items i
                WHERE i.consume = '1'
                  AND (p.paytype LIKE '%' || i.item_nm || '%'
                       OR i.item_nm LIKE '%' || p.paytype || '%')
              )
        ),
        max_seq AS (
            SELECT maintenance_id, COALESCE(MAX(business_operation_id), 0) AS mx
            FROM tit25_accessories_update
            GROUP BY maintenance_id
        )
        SELECT
            r.maintenance_id,
            COALESCE(m.mx, 0) + r.rn AS business_operation_id,
            r.store_id,
            r.engineer_id,
            r.receipt_id,
            r.delivery_id,
            '[MIGRATED_FROM_TIT26:' || r.src_id || '] ' || COALESCE(r.memo, '') AS description,
            r.create_time,
            r.creator,
            r.update_time,
            r.updator,
            COALESCE(r.create_time, NOW()) AS created_at,
            COALESCE(r.update_time, NOW()) AS updated_at,
            r.useflg AS auditflg,
            '3' AS c_type,
            r.payje,
            r.paytype,
            r.paydate,
            r.memo,
            1 AS version
        FROM ranked r
        LEFT JOIN max_seq m ON m.maintenance_id = r.maintenance_id
    """))

    # TIT26 标记只读（保留表结构，useflg='0'）
    bind.execute(sa_text("UPDATE tit26_paylist SET useflg = '0' WHERE useflg = '1'"))


def downgrade():
    bind = op.get_bind()
    # 删除迁移记录（按溯源标记定位）
    bind.execute(sa_text(
        "DELETE FROM tit25_accessories_update "
        "WHERE description LIKE '[MIGRATED_FROM_TIT26:%]'"
    ))
    # 恢复 TIT26 useflg='1'（无法精确恢复原值，因迁移前可能已有 useflg='0' 记录）
    # 注：downgrade 仅回滚 TIT25 迁移数据，TIT26 useflg 不自动恢复
