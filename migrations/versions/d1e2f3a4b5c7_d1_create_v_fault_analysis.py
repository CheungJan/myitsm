"""D1: create v_fault_analysis view

Revision ID: d1e2f3a4b5c7
Revises: c3d4e5f6a7b9
Create Date: 2026-07-22 13:05:00

变更:
  - 创建 v_fault_analysis PostgreSQL 视图
  - 打通故障代码（TIT04_ARCHIVECODE）与设备主数据（TMM43_EID/TMM12_ITEMS）关联
  - 数据源：TIT23_MAINTENANCE_D2D（gzdm 故障代码 + device_id 设备）
    JOIN TIT04_ARCHIVECODE（故障代码名称/大类/小类）
    JOIN TMM43_EID（设备主数据：itemcd/etyp/sflg/asset_type）
    JOIN TMM12_ITEMS（物料名称）
    JOIN 各维护单主表（TIT10/TIT13/TIT15/TIT16/TIT17）UNION 得单据类型/状态/时间
  - 用途：D2 关键分析报表（型号故障率/配件频次/修复时长）
"""
from alembic import op
from sqlalchemy import text as sa_text

# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c7'
down_revision = 'c3d4e5f6a7b9'
branch_labels = None
depends_on = None


# 视图 DDL：TIT23 D2D 为事实表，关联故障代码+设备+物料+维护单主表
# 维护单主表 UNION：TIT10(日常维护)/TIT13(新机开通)/TIT15(旧机翻新)/TIT16(设备变更)/TIT17(日常保养)
# 每个主表投影为统一列：maintenance_id / bill_type / current_status / request_time / close_time
_VIEW_SQL = """
CREATE OR REPLACE VIEW v_fault_analysis AS
SELECT
    d.id AS d2d_id,
    d.maintenance_id,
    d.business_operation_id,
    d.d2d_type,
    d.d2d_result,
    d.arrive_time,
    d.leave_time,
    d.gzdm,
    a.arch_nm AS fault_nm,
    a.fault_type AS fault_type_cd,
    a.arch_group AS fault_group,
    d.device_id,
    e.itemcd AS device_itemcd,
    e.etyp AS device_etyp,
    e.sflg AS device_sflg,
    e.asset_type AS device_asset_type,
    e.whcd AS device_whcd,
    i.item_nm AS device_item_nm,
    m.bill_type,
    m.current_status,
    m.request_time,
    m.close_time,
    -- 修复时长（分钟）：离店-到达，仅 d2d_type='2'（离店）且有完整时间
    CASE
        WHEN d.d2d_type = '2' AND d.arrive_time IS NOT NULL AND d.leave_time IS NOT NULL
        THEN EXTRACT(EPOCH FROM (d.leave_time - d.arrive_time)) / 60
    END AS repair_minutes
FROM tit23_maintenance_d2d d
LEFT JOIN tit04_archivecode a ON a.arch_cd = d.gzdm AND a.useflg = '1'
LEFT JOIN tmm43_eid e ON e.eid = d.device_id AND e.useflg = '1'
LEFT JOIN tmm12_items i ON i.item_cd = e.itemcd
LEFT JOIN (
    SELECT maintenance_id, 'MD' AS bill_type, current_status, request_time, close_time
    FROM tit10_maintenanceday
    UNION ALL
    SELECT new_opening_id, 'MO', current_status, request_time, close_time
    FROM tit13_maintenance_open
    UNION ALL
    SELECT renew_id, 'MR', current_status, request_time, close_time
    FROM tit15_maintenance_renovate
    UNION ALL
    SELECT device_change_id, 'BG', current_status, request_time, close_time
    FROM tit16_device_change
    UNION ALL
    SELECT daily_maintenance_id, 'BY', current_status, request_time, close_time
    FROM tit17_maintenance
) m ON m.maintenance_id = d.maintenance_id
WHERE d.useflg = '1'
"""


def upgrade():
    op.execute(sa_text(_VIEW_SQL))


def downgrade():
    op.execute(sa_text("DROP VIEW IF EXISTS v_fault_analysis"))
