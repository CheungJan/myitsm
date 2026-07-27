"""D3: v_fault_analysis 视图增加优化方案字段列

Revision ID: f3a4b5c6d7e9
Revises: e2f3a4b5c6d8
Create Date: 2026-07-22 17:55:00

变更:
  - 视图增加优化方案已落地字段：
    1. TIT23_D2D.device_id / accessories_id（事项1方案B，本次处理设备/配件追溯）
    2. TIT25.itemcd / fault_cd（B3，配件更换关联故障代码）
  - 兼容 PB 迁移数据：新字段在 PB 历史中为 null，COALESCE 回退到老源
  - 报表 SQL 可引用新列支持按配件 itemcd / 故障代码筛选
"""
from alembic import op
from sqlalchemy import text as sa_text

# revision identifiers, used by Alembic.
revision = 'f3a4b5c6d7e9'
down_revision = 'e2f3a4b5c6d8'
branch_labels = None
depends_on = None


# 视图 DDL：在 D2 基础上增加优化方案字段列
# 1. d2d_agg 增加 device_id_d2d / accessories_id_d2d（TIT23 新增字段）
# 2. t25_agg 增加 itemcd_t25 / fault_cd_t25（TIT25 新增字段）
# 3. SELECT 输出新列，PB 历史数据新列为 null，不影响老逻辑
_VIEW_SQL = """
CREATE OR REPLACE VIEW v_fault_analysis AS
WITH d2d_agg AS (
    SELECT maintenance_id,
           MIN(CASE WHEN d2d_type = '1' THEN arrive_time END) AS arrive_time,
           MAX(CASE WHEN d2d_type = '2' THEN leave_time END) AS leave_time,
           MAX(gzdm) AS gzdm_d2d,
           MAX(device_id) AS device_id_d2d,
           MAX(accessories_id) AS accessories_id_d2d
    FROM tit23_maintenance_d2d
    WHERE useflg = '1'
    GROUP BY maintenance_id
),
t25_agg AS (
    SELECT maintenance_id,
           MAX(device_id) AS device_id_t25,
           MAX(itemcd) AS itemcd_t25,
           MAX(fault_cd) AS fault_cd_t25
    FROM tit25_accessories_update
    WHERE device_id IS NOT NULL AND device_id <> ''
       OR itemcd IS NOT NULL AND itemcd <> ''
    GROUP BY maintenance_id
),
m AS (
    SELECT maintenance_id, 'MD' AS bill_type, current_status, request_time, close_time,
           device_id AS device_id_main, faultcode
    FROM tit10_maintenanceday
    UNION ALL
    SELECT new_opening_id, 'MO', current_status, request_time, close_time, device_id, NULL
    FROM tit13_maintenance_open
    UNION ALL
    SELECT renew_id, 'MR', current_status, request_time, close_time, NULL::varchar, NULL
    FROM tit15_maintenance_renovate
    UNION ALL
    SELECT device_change_id, 'BG', current_status, request_time, close_time, device_id, NULL
    FROM tit16_device_change
    UNION ALL
    SELECT daily_maintenance_id, 'BY', current_status, request_time, close_time, NULL::varchar, NULL
    FROM tit17_maintenance
)
SELECT
    m.maintenance_id,
    m.bill_type,
    m.current_status,
    m.request_time,
    m.close_time,
    d.arrive_time,
    d.leave_time,
    -- device_id：优先 TIT25 配件 EID，其次 TIT23 D2D device_id，最后主表 device_id
    COALESCE(t25.device_id_t25, d.device_id_d2d, m.device_id_main) AS device_id,
    -- gzdm：优先 TIT23 D2D，其次 TIT10 faultcode 解析（"级别,故障代码/" → 故障代码）
    COALESCE(
        d.gzdm_d2d,
        CASE
            WHEN m.faultcode LIKE '%,%/%' THEN
                SUBSTRING(m.faultcode FROM POSITION(',' IN m.faultcode) + 1
                          FOR POSITION('/' IN m.faultcode) - POSITION(',' IN m.faultcode) - 1)
        END
    ) AS gzdm,
    -- 设备主数据关联
    e.itemcd AS device_itemcd,
    e.etyp AS device_etyp,
    e.sflg AS device_sflg,
    e.asset_type AS device_asset_type,
    e.whcd AS device_whcd,
    i.item_nm AS device_item_nm,
    -- 故障代码关联
    a.arch_nm AS fault_nm,
    -- fault_type 按 itemcd 前2位推导（TIT04.fault_type 历史未维护）
    LEFT(e.itemcd, 2) AS fault_type_cd,
    a.arch_group AS fault_group,
    -- 修复时长（分钟）：离店 - 到店
    CASE
        WHEN d.arrive_time IS NOT NULL AND d.leave_time IS NOT NULL
        THEN EXTRACT(EPOCH FROM (d.leave_time - d.arrive_time)) / 60
    END AS repair_minutes,
    -- 优化方案新增列（PB 历史为 null，新数据有值）
    d.device_id_d2d AS d2d_device_id,
    d.accessories_id_d2d AS d2d_accessories_id,
    t25.itemcd_t25 AS accessory_itemcd,
    t25.fault_cd_t25 AS accessory_fault_cd
FROM m
LEFT JOIN d2d_agg d ON d.maintenance_id = m.maintenance_id
LEFT JOIN t25_agg t25 ON t25.maintenance_id = m.maintenance_id
LEFT JOIN tmm43_eid e ON e.eid = COALESCE(t25.device_id_t25, d.device_id_d2d, m.device_id_main) AND e.useflg = '1'
LEFT JOIN tmm12_items i ON i.item_cd = e.itemcd
LEFT JOIN tit04_archivecode a ON a.arch_cd = COALESCE(
        d.gzdm_d2d,
        CASE
            WHEN m.faultcode LIKE '%,%/%' THEN
                SUBSTRING(m.faultcode FROM POSITION(',' IN m.faultcode) + 1
                          FOR POSITION('/' IN m.faultcode) - POSITION(',' IN m.faultcode) - 1)
        END
    ) AND a.useflg = '1'
"""


def upgrade():
    op.execute(sa_text("DROP VIEW IF EXISTS v_fault_analysis"))
    op.execute(sa_text(_VIEW_SQL))


def downgrade():
    # 回退到 D2 版本视图（不含优化方案新列）
    op.execute(sa_text("DROP VIEW IF EXISTS v_fault_analysis"))
    op.execute(sa_text("""
CREATE OR REPLACE VIEW v_fault_analysis AS
WITH d2d_agg AS (
    SELECT maintenance_id,
           MIN(CASE WHEN d2d_type = '1' THEN arrive_time END) AS arrive_time,
           MAX(CASE WHEN d2d_type = '2' THEN leave_time END) AS leave_time,
           MAX(gzdm) AS gzdm_d2d
    FROM tit23_maintenance_d2d
    WHERE useflg = '1'
    GROUP BY maintenance_id
),
t25_agg AS (
    SELECT maintenance_id, MAX(device_id) AS device_id_t25
    FROM tit25_accessories_update
    WHERE device_id IS NOT NULL AND device_id <> ''
    GROUP BY maintenance_id
),
m AS (
    SELECT maintenance_id, 'MD' AS bill_type, current_status, request_time, close_time,
           device_id AS device_id_main, faultcode
    FROM tit10_maintenanceday
    UNION ALL
    SELECT new_opening_id, 'MO', current_status, request_time, close_time, device_id, NULL
    FROM tit13_maintenance_open
    UNION ALL
    SELECT renew_id, 'MR', current_status, request_time, close_time, NULL::varchar, NULL
    FROM tit15_maintenance_renovate
    UNION ALL
    SELECT device_change_id, 'BG', current_status, request_time, close_time, device_id, NULL
    FROM tit16_device_change
    UNION ALL
    SELECT daily_maintenance_id, 'BY', current_status, request_time, close_time, NULL::varchar, NULL
    FROM tit17_maintenance
)
SELECT
    m.maintenance_id,
    m.bill_type,
    m.current_status,
    m.request_time,
    m.close_time,
    d.arrive_time,
    d.leave_time,
    COALESCE(t25.device_id_t25, m.device_id_main) AS device_id,
    COALESCE(
        d.gzdm_d2d,
        CASE
            WHEN m.faultcode LIKE '%,%/%' THEN
                SUBSTRING(m.faultcode FROM POSITION(',' IN m.faultcode) + 1
                          FOR POSITION('/' IN m.faultcode) - POSITION(',' IN m.faultcode) - 1)
        END
    ) AS gzdm,
    e.itemcd AS device_itemcd,
    e.etyp AS device_etyp,
    e.sflg AS device_sflg,
    e.asset_type AS device_asset_type,
    e.whcd AS device_whcd,
    i.item_nm AS device_item_nm,
    a.arch_nm AS fault_nm,
    LEFT(e.itemcd, 2) AS fault_type_cd,
    a.arch_group AS fault_group,
    CASE
        WHEN d.arrive_time IS NOT NULL AND d.leave_time IS NOT NULL
        THEN EXTRACT(EPOCH FROM (d.leave_time - d.arrive_time)) / 60
    END AS repair_minutes
FROM m
LEFT JOIN d2d_agg d ON d.maintenance_id = m.maintenance_id
LEFT JOIN t25_agg t25 ON t25.maintenance_id = m.maintenance_id
LEFT JOIN tmm43_eid e ON e.eid = COALESCE(t25.device_id_t25, m.device_id_main) AND e.useflg = '1'
LEFT JOIN tmm12_items i ON i.item_cd = e.itemcd
LEFT JOIN tit04_archivecode a ON a.arch_cd = COALESCE(
        d.gzdm_d2d,
        CASE
            WHEN m.faultcode LIKE '%,%/%' THEN
                SUBSTRING(m.faultcode FROM POSITION(',' IN m.faultcode) + 1
                          FOR POSITION('/' IN m.faultcode) - POSITION(',' IN m.faultcode) - 1)
        END
    ) AND a.useflg = '1'
"""))
