"""修复采购需求执行状态判定逻辑

问题：execution_status 仅根据 received_qty 判定“已下单”和“执行中”，
未考虑 ordered_qty 与 audit_qty 的关系。
当 partially ordered（下单 < 审核）但未收货时，状态错误地显示“已下单”而非“执行中”。

修复：ordered_qty >= audit_qty 且未收货 → “已下单”
      ordered_qty > 0 但 < audit_qty → “执行中”

Revision ID: a34751d36973
Revises: 856f824896ae
Create Date: 2026-05-26
"""
from alembic import op

revision = "a34751d36973"
down_revision = "856f824896ae"


def upgrade():
    op.execute("""
        CREATE OR REPLACE VIEW v_requisition_execution AS
        SELECT
            p.pcplanid, p.plandate, p.auditflg, p.auditman, p.auditdate, p.useflg,
            dt.lineno, dt.itemcd, i.item_nm AS itemnm, i.spec, i.wunit,
            dt.rgstqty AS plan_qty,
            dt.auditqty AS audit_qty,
            COALESCE(link_stats.ordered_qty, 0) AS ordered_qty,
            COALESCE(link_stats.received_qty, 0) AS received_qty,
            dt.auditqty - COALESCE(link_stats.ordered_qty, 0) AS available_qty,
            CASE
                WHEN COALESCE(link_stats.ordered_qty, 0) = 0 THEN '未开始'
                WHEN COALESCE(link_stats.received_qty, 0) >= dt.rgstqty THEN '已完成'
                WHEN COALESCE(link_stats.received_qty, 0) > 0 THEN '执行中'
                WHEN COALESCE(link_stats.ordered_qty, 0) >= dt.auditqty THEN '已下单'
                ELSE '执行中'
            END AS execution_status,
            CASE WHEN dt.rgstqty > 0
                THEN ROUND(COALESCE(link_stats.received_qty, 0) / dt.rgstqty * 100, 2)
                ELSE 0
            END AS execution_rate
        FROM tpc01_pcplan p
        JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
        LEFT JOIN tmm12_items i ON dt.itemcd = i.item_cd
        LEFT JOIN (
            SELECT l.pcplanid, l.pclineno,
                SUM(l.linkqty) AS ordered_qty,
                SUM(CASE WHEN rd.inqty >= rd.rgsqty THEN l.linkqty ELSE 0 END) AS received_qty
            FROM tpc20_requisition_order_link l
            JOIN tpc13_registerdt rd ON l.rgstbillid = rd.rgstbillid AND l.rgstlineno = rd.lineno
            JOIN tpc12_register r ON rd.rgstbillid = r.rgstbillid
            WHERE r.useflg <> '9'
            GROUP BY l.pcplanid, l.pclineno
        ) link_stats ON dt.pcplanid = link_stats.pcplanid AND dt.lineno = link_stats.pclineno
        WHERE p.useflg = '1'
    """)


def downgrade():
    op.execute("""
        CREATE OR REPLACE VIEW v_requisition_execution AS
        SELECT
            p.pcplanid, p.plandate, p.auditflg, p.auditman, p.auditdate, p.useflg,
            dt.lineno, dt.itemcd, i.item_nm AS itemnm, i.spec, i.wunit,
            dt.rgstqty AS plan_qty,
            dt.auditqty AS audit_qty,
            COALESCE(link_stats.ordered_qty, 0) AS ordered_qty,
            COALESCE(link_stats.received_qty, 0) AS received_qty,
            dt.auditqty - COALESCE(link_stats.ordered_qty, 0) AS available_qty,
            CASE
                WHEN COALESCE(link_stats.ordered_qty, 0) = 0 THEN '未开始'
                WHEN COALESCE(link_stats.received_qty, 0) >= dt.rgstqty THEN '已完成'
                WHEN COALESCE(link_stats.received_qty, 0) > 0 THEN '执行中'
                ELSE '已下单'
            END AS execution_status,
            CASE WHEN dt.rgstqty > 0
                THEN ROUND(COALESCE(link_stats.received_qty, 0) / dt.rgstqty * 100, 2)
                ELSE 0
            END AS execution_rate
        FROM tpc01_pcplan p
        JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
        LEFT JOIN tmm12_items i ON dt.itemcd = i.item_cd
        LEFT JOIN (
            SELECT l.pcplanid, l.pclineno,
                SUM(l.linkqty) AS ordered_qty,
                SUM(CASE WHEN rd.inqty >= rd.rgsqty THEN l.linkqty ELSE 0 END) AS received_qty
            FROM tpc20_requisition_order_link l
            JOIN tpc13_registerdt rd ON l.rgstbillid = rd.rgstbillid AND l.rgstlineno = rd.lineno
            JOIN tpc12_register r ON rd.rgstbillid = r.rgstbillid
            WHERE r.useflg <> '9'
            GROUP BY l.pcplanid, l.pclineno
        ) link_stats ON dt.pcplanid = link_stats.pcplanid AND dt.lineno = link_stats.pclineno
        WHERE p.useflg = '1'
    """)
