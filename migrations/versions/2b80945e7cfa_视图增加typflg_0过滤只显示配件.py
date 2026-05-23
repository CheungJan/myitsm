"""视图增加typflg=0过滤只显示配件

Revision ID: 2b80945e7cfa
Revises: 5e2f0e99c995
Create Date: 2026-05-23 15:43:07.105514

"""
from alembic import op


revision = '2b80945e7cfa'
down_revision = '5e2f0e99c995'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP VIEW IF EXISTS v_item_requisition_status")
    op.execute("DROP VIEW IF EXISTS v_requisition_execution")
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
        LEFT JOIN tmm12_items i ON dt.itemcd = i.item_cd AND i.typflg = '0'
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

    op.execute("""
        CREATE OR REPLACE VIEW v_item_requisition_status AS
        SELECT
            dt.itemcd, i.item_nm AS itemnm, i.spec, i.wunit,
            SUM(dt.auditqty) AS total_audit_qty,
            SUM(dt.auditqty) - COALESCE(SUM(link_stats.ordered_qty), 0) AS available_for_order,
            json_agg(jsonb_build_object(
                'pcplanid', dt.pcplanid, 'pclineno', dt.lineno,
                'plandate', p.plandate, 'auditqty', dt.auditqty,
                'available_qty', dt.auditqty - COALESCE(link_stats.ordered_qty, 0)
            ) ORDER BY p.plandate) AS plan_details
        FROM tpc02_pcplandt dt
        JOIN tpc01_pcplan p ON dt.pcplanid = p.pcplanid AND p.useflg = '1' AND p.auditflg = '2'
        LEFT JOIN tmm12_items i ON dt.itemcd = i.item_cd AND i.typflg = '0'
        LEFT JOIN (
            SELECT l.pcplanid, l.pclineno, SUM(l.linkqty) AS ordered_qty
            FROM tpc20_requisition_order_link l
            JOIN tpc12_register r ON l.rgstbillid = r.rgstbillid
            WHERE r.useflg <> '9'
            GROUP BY l.pcplanid, l.pclineno
        ) link_stats ON dt.pcplanid = link_stats.pcplanid AND dt.lineno = link_stats.pclineno
        WHERE dt.auditqty > 0
        GROUP BY dt.itemcd, i.item_nm, i.spec, i.wunit
        HAVING SUM(dt.auditqty) - COALESCE(SUM(link_stats.ordered_qty), 0) > 0
    """)


def downgrade():
    op.execute("DROP VIEW IF EXISTS v_item_requisition_status")
    op.execute("DROP VIEW IF EXISTS v_requisition_execution")
    # 回退到无 typflg 过滤的版本
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

    op.execute("""
        CREATE OR REPLACE VIEW v_item_requisition_status AS
        SELECT
            dt.itemcd, i.item_nm AS itemnm, i.spec, i.wunit,
            SUM(dt.auditqty) AS total_audit_qty,
            SUM(dt.auditqty) - COALESCE(SUM(link_stats.ordered_qty), 0) AS available_for_order,
            json_agg(jsonb_build_object(
                'pcplanid', dt.pcplanid, 'pclineno', dt.lineno,
                'plandate', p.plandate, 'auditqty', dt.auditqty,
                'available_qty', dt.auditqty - COALESCE(link_stats.ordered_qty, 0)
            ) ORDER BY p.plandate) AS plan_details
        FROM tpc02_pcplandt dt
        JOIN tpc01_pcplan p ON dt.pcplanid = p.pcplanid AND p.useflg = '1' AND p.auditflg = '2'
        LEFT JOIN tmm12_items i ON dt.itemcd = i.item_cd
        LEFT JOIN (
            SELECT l.pcplanid, l.pclineno, SUM(l.linkqty) AS ordered_qty
            FROM tpc20_requisition_order_link l
            JOIN tpc12_register r ON l.rgstbillid = r.rgstbillid
            WHERE r.useflg <> '9'
            GROUP BY l.pcplanid, l.pclineno
        ) link_stats ON dt.pcplanid = link_stats.pcplanid AND dt.lineno = link_stats.pclineno
        WHERE dt.auditqty > 0
        GROUP BY dt.itemcd, i.item_nm, i.spec, i.wunit
        HAVING SUM(dt.auditqty) - COALESCE(SUM(link_stats.ordered_qty), 0) > 0
    """)
