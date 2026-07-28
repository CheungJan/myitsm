"""D2: fault_analysis view 支持历史数据补全

Revision ID: e2f3a4b5c6d8
Revises: d1e2f3a4b5c7
Create Date: 2026-07-22 15:50:00

变更:
  - 改造 v_fault_analysis 视图：从 D2D 行维度改为工单维度聚合
  - 历史数据补全：
    1. device_id：优先 TIT25 配件更新 device_id，其次主表 device_id
    2. gzdm：优先 TIT23 D2D gzdm，其次 TIT10 faultcode 解析（格式 "级别,故障代码/"）
    3. arrive_time：TIT23 d2d_type='1'（到店）最早时间
    4. leave_time：TIT23 d2d_type='2'（离店）最晚时间
    5. repair_minutes：leave_time - arrive_time（分钟）
  - 用途：D2 故障分析报表能覆盖历史迁移数据（20万+工单）
"""
from alembic import op
from sqlalchemy import text as sa_text

# revision identifiers, used by Alembic.
revision = 'e2f3a4b5c6d8'
down_revision = 'd1e2f3a4b5c7'
branch_labels = None
depends_on = None


# 视图 DDL：工单维度聚合，补全历史数据
# 1. TIT23 D2D 按 maintenance_id 聚合到店/离店时间 + gzdm
# 2. TIT25 按 maintenance_id 聚合 device_id（配件对应的 EID）
# 3. 主表 UNION 提供 bill_type/status/time + 主表 device_id + TIT10 faultcode
# 4. device_id 优先 TIT25，其次主表；gzdm 优先 TIT23，其次 TIT10 faultcode 解析
# 5. repair_minutes = leave_time - arrive_time
_VIEW_SQL = """
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
    -- device_id：优先 TIT25 配件 EID，其次主表 device_id
    COALESCE(t25.device_id_t25, m.device_id_main) AS device_id,
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
"""


def upgrade():
    op.execute(sa_text("DROP VIEW IF EXISTS v_fault_analysis"))
    op.execute(sa_text(_VIEW_SQL))


def downgrade():
    op.execute(sa_text("DROP VIEW IF EXISTS v_fault_analysis"))
    # 回退到 D1 版本视图（D2D 行维度）
    op.execute(sa_text("""
CREATE OR REPLACE VIEW v_fault_analysis AS
SELECT d.id AS d2d_id, d.maintenance_id, d.business_operation_id, d.d2d_type, d.d2d_result,
       d.arrive_time, d.leave_time, d.gzdm, a.arch_nm AS fault_nm, a.fault_type AS fault_type_cd,
       a.arch_group AS fault_group, d.device_id, e.itemcd AS device_itemcd, e.etyp AS device_etyp,
       e.sflg AS device_sflg, e.asset_type AS device_asset_type, e.whcd AS device_whcd,
       i.item_nm AS device_item_nm, m.bill_type, m.current_status, m.request_time, m.close_time,
       CASE WHEN d.d2d_type = '2' AND d.arrive_time IS NOT NULL AND d.leave_time IS NOT NULL
            THEN EXTRACT(EPOCH FROM (d.leave_time - d.arrive_time)) / 60 END AS repair_minutes
FROM tit23_maintenance_d2d d
LEFT JOIN tit04_archivecode a ON a.arch_cd = d.gzdm AND a.useflg = '1'
LEFT JOIN tmm43_eid e ON e.eid = d.device_id AND e.useflg = '1'
LEFT JOIN tmm12_items i ON i.item_cd = e.itemcd
LEFT JOIN (
    SELECT maintenance_id, 'MD' AS bill_type, current_status, request_time, close_time FROM tit10_maintenanceday
    UNION ALL SELECT new_opening_id, 'MO', current_status, request_time, close_time FROM tit13_maintenance_open
    UNION ALL SELECT renew_id, 'MR', current_status, request_time, close_time FROM tit15_maintenance_renovate
    UNION ALL SELECT device_change_id, 'BG', current_status, request_time, close_time FROM tit16_device_change
    UNION ALL SELECT daily_maintenance_id, 'BY', current_status, request_time, close_time FROM tit17_maintenance
) m ON m.maintenance_id = d.maintenance_id
WHERE d.useflg = '1'
"""))
