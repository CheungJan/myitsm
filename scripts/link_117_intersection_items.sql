-- 精确关联117种交集物料
-- 排除仅需求有的物料（MK0007）和仅订单有的物料（MT7002）

-- 步骤1：统计本次将要处理的记录数
WITH demand_lines AS (
    SELECT p.pcplanid, p.gendate as demand_date, dt.lineno, dt.itemcd, dt.auditqty
    FROM tpc01_pcplan p
    JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
    WHERE p.gendate < '2026-01-01'
      AND p.useflg = '1'
      AND p.auditflg = '2'
      AND dt.auditqty > 0
      AND dt.itemcd NOT IN ('MK0007', 'MT7002')  -- 排除两边不交集的物料
),
order_lines AS (
    SELECT r.rgstbillid, r.gendate as order_date, rd.lineno as order_lineno,
           rd.itemcd, rd.rgsqty, rd.inqty
    FROM tpc12_register r
    JOIN tpc13_registerdt rd ON r.rgstbillid = rd.rgstbillid
    WHERE r.gendate < '2026-01-01'
),
matched AS (
    SELECT d.pcplanid, d.lineno as pclineno, o.rgstbillid, o.order_lineno as rgstlineno,
           d.itemcd, LEAST(d.auditqty, o.rgsqty) as linkqty,
           CASE WHEN o.inqty >= o.rgsqty THEN 'completed'
                WHEN o.inqty > 0 THEN 'partial_in'
                ELSE 'ordered' END as linkstatus,
           ROW_NUMBER() OVER (PARTITION BY d.pcplanid, d.lineno 
                              ORDER BY o.order_date, o.rgstbillid, o.order_lineno) as rn
    FROM demand_lines d
    JOIN order_lines o ON d.itemcd = o.itemcd 
        AND o.order_date >= d.demand_date
        AND o.order_date < d.demand_date + INTERVAL '365 days'
    WHERE NOT EXISTS (
        SELECT 1 FROM tpc20_requisition_order_link l 
        WHERE l.pcplanid = d.pcplanid AND l.pclineno = d.lineno
    )
)
SELECT 
    COUNT(*) as total_matches,
    COUNT(CASE WHEN linkstatus = 'completed' THEN 1 END) as completed_count,
    COUNT(CASE WHEN linkstatus = 'partial_in' THEN 1 END) as partial_count,
    COUNT(CASE WHEN linkstatus = 'ordered' THEN 1 END) as ordered_count
FROM matched WHERE rn = 1;

-- 步骤2：预览前30条将要创建的关联
WITH demand_lines AS (
    SELECT p.pcplanid, p.gendate as demand_date, dt.lineno, dt.itemcd, dt.auditqty
    FROM tpc01_pcplan p
    JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
    WHERE p.gendate < '2026-01-01'
      AND p.useflg = '1'
      AND p.auditflg = '2'
      AND dt.auditqty > 0
      AND dt.itemcd NOT IN ('MK0007', 'MT7002')
),
order_lines AS (
    SELECT r.rgstbillid, r.gendate as order_date, rd.lineno as order_lineno,
           rd.itemcd, rd.rgsqty, rd.inqty
    FROM tpc12_register r
    JOIN tpc13_registerdt rd ON r.rgstbillid = rd.rgstbillid
    WHERE r.gendate < '2026-01-01'
),
matched AS (
    SELECT d.pcplanid, d.lineno as pclineno, o.rgstbillid, o.order_lineno as rgstlineno,
           d.itemcd, LEAST(d.auditqty, o.rgsqty) as linkqty,
           CASE WHEN o.inqty >= o.rgsqty THEN 'completed'
                WHEN o.inqty > 0 THEN 'partial_in'
                ELSE 'ordered' END as linkstatus,
           ROW_NUMBER() OVER (PARTITION BY d.pcplanid, d.lineno 
                              ORDER BY o.order_date, o.rgstbillid, o.order_lineno) as rn
    FROM demand_lines d
    JOIN order_lines o ON d.itemcd = o.itemcd 
        AND o.order_date >= d.demand_date
        AND o.order_date < d.demand_date + INTERVAL '365 days'
    WHERE NOT EXISTS (
        SELECT 1 FROM tpc20_requisition_order_link l 
        WHERE l.pcplanid = d.pcplanid AND l.pclineno = d.lineno
    )
)
SELECT pcplanid, pclineno, rgstbillid, rgstlineno, itemcd, linkqty, linkstatus
FROM matched WHERE rn = 1
ORDER BY pcplanid, pclineno
LIMIT 30;

-- 步骤3：执行关联插入（取消注释执行）
/*
INSERT INTO tpc20_requisition_order_link (
    pcplanid, pclineno, rgstbillid, rgstlineno, 
    linkqty, linkstatus, gendate, opercd
)
WITH demand_lines AS (
    SELECT p.pcplanid, p.gendate as demand_date, dt.lineno, dt.itemcd, dt.auditqty
    FROM tpc01_pcplan p
    JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
    WHERE p.gendate < '2026-01-01'
      AND p.useflg = '1'
      AND p.auditflg = '2'
      AND dt.auditqty > 0
      AND dt.itemcd NOT IN ('MK0007', 'MT7002')
),
order_lines AS (
    SELECT r.rgstbillid, r.gendate as order_date, rd.lineno as order_lineno,
           rd.itemcd, rd.rgsqty, rd.inqty
    FROM tpc12_register r
    JOIN tpc13_registerdt rd ON r.rgstbillid = rd.rgstbillid
    WHERE r.gendate < '2026-01-01'
),
matched AS (
    SELECT d.pcplanid, d.lineno as pclineno, o.rgstbillid, o.order_lineno as rgstlineno,
           LEAST(d.auditqty, o.rgsqty) as linkqty,
           CASE WHEN o.inqty >= o.rgsqty THEN 'completed'
                WHEN o.inqty > 0 THEN 'partial_in'
                ELSE 'ordered' END as linkstatus,
           ROW_NUMBER() OVER (PARTITION BY d.pcplanid, d.lineno 
                              ORDER BY o.order_date, o.rgstbillid, o.order_lineno) as rn
    FROM demand_lines d
    JOIN order_lines o ON d.itemcd = o.itemcd 
        AND o.order_date >= d.demand_date
        AND o.order_date < d.demand_date + INTERVAL '365 days'
    WHERE NOT EXISTS (
        SELECT 1 FROM tpc20_requisition_order_link l 
        WHERE l.pcplanid = d.pcplanid AND l.pclineno = d.lineno
    )
)
SELECT pcplanid, pclineno, rgstbillid, rgstlineno, linkqty, linkstatus,
       CURRENT_TIMESTAMP as gendate, 'AUTO_LINK' as opercd
FROM matched WHERE rn = 1;
*/

-- 步骤4：验证执行结果
-- SELECT 
--     execution_status,
--     COUNT(*) as cnt,
--     ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pct
-- FROM v_requisition_execution
-- WHERE pcplanid IN (SELECT pcplanid FROM tpc01_pcplan WHERE gendate < '2026-01-01' AND useflg = '1')
-- GROUP BY execution_status
-- ORDER BY cnt DESC;
