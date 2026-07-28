-- 重建2026年前历史数据的采购需求-订单关联
-- 基于实际数据库数据分析结果

-- 数据概况验证
SELECT '需求单2026年前' as item, COUNT(*) as cnt FROM tpc01_pcplan WHERE gendate < '2026-01-01' AND useflg = '1' AND auditflg = '2'
UNION ALL
SELECT '需求明细总数', COUNT(*) FROM tpc02_pcplandt WHERE pcplanid IN (SELECT pcplanid FROM tpc01_pcplan WHERE gendate < '2026-01-01' AND useflg = '1')
UNION ALL
SELECT '订单主表2026年前(useflg=2)', COUNT(*) FROM tpc12_register WHERE gendate < '2026-01-01'
UNION ALL
SELECT '订单明细总数', COUNT(*) FROM tpc13_registerdt WHERE rgstbillid IN (SELECT rgstbillid FROM tpc12_register WHERE gendate < '2026-01-01')
UNION ALL
SELECT '已有TPC20关联数', COUNT(*) FROM tpc20_requisition_order_link;

-- 关联策略：
-- 1. 订单日期 >= 需求单日期（下游单据）
-- 2. 相同 itemcd
-- 3. 订单数量 <= 需求单可用数量
-- 4. 每个需求明细行匹配最早的可用订单明细

-- 预览将要建立的关联（前20条）
WITH demand_lines AS (
    -- 2026年前需求明细（已审批）
    SELECT 
        p.pcplanid,
        p.gendate as demand_date,
        dt.lineno,
        dt.itemcd,
        dt.auditqty
    FROM tpc01_pcplan p
    JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
    WHERE p.gendate < '2026-01-01'
      AND p.useflg = '1'
      AND p.auditflg = '2'
      AND dt.auditqty > 0
),
order_lines AS (
    -- 2026年前订单明细
    SELECT 
        r.rgstbillid,
        r.gendate as order_date,
        rd.lineno as order_lineno,
        rd.itemcd,
        rd.rgsqty,
        rd.inqty
    FROM tpc12_register r
    JOIN tpc13_registerdt rd ON r.rgstbillid = rd.rgstbillid
    WHERE r.gendate < '2026-01-01'
),
matched AS (
    SELECT 
        d.pcplanid,
        d.lineno as pclineno,
        o.rgstbillid,
        o.order_lineno as rgstlineno,
        d.itemcd,
        LEAST(d.auditqty, o.rgsqty) as linkqty,
        CASE 
            WHEN o.inqty >= o.rgsqty THEN 'completed'
            WHEN o.inqty > 0 THEN 'partial_in'
            ELSE 'ordered'
        END as linkstatus,
        ROW_NUMBER() OVER (
            PARTITION BY d.pcplanid, d.lineno 
            ORDER BY o.order_date, o.rgstbillid, o.order_lineno
        ) as rn
    FROM demand_lines d
    JOIN order_lines o ON d.itemcd = o.itemcd 
        AND o.order_date >= d.demand_date
    WHERE NOT EXISTS (
        SELECT 1 FROM tpc20_requisition_order_link l 
        WHERE l.pcplanid = d.pcplanid AND l.pclineno = d.lineno
    )
)
SELECT 
    pcplanid,
    pclineno,
    rgstbillid,
    rgstlineno,
    itemcd,
    linkqty,
    linkstatus
FROM matched
WHERE rn = 1
ORDER BY pcplanid, pclineno
LIMIT 20;

-- 实际执行插入（取消注释后执行）
/*
INSERT INTO tpc20_requisition_order_link (
    pcplanid, pclineno, rgstbillid, rgstlineno, 
    linkqty, linkstatus, gendate, opercd
)
WITH demand_lines AS (
    SELECT 
        p.pcplanid,
        p.gendate as demand_date,
        dt.lineno,
        dt.itemcd,
        dt.auditqty
    FROM tpc01_pcplan p
    JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
    WHERE p.gendate < '2026-01-01'
      AND p.useflg = '1'
      AND p.auditflg = '2'
      AND dt.auditqty > 0
),
order_lines AS (
    SELECT 
        r.rgstbillid,
        r.gendate as order_date,
        rd.lineno as order_lineno,
        rd.itemcd,
        rd.rgsqty,
        rd.inqty
    FROM tpc12_register r
    JOIN tpc13_registerdt rd ON r.rgstbillid = rd.rgstbillid
    WHERE r.gendate < '2026-01-01'
),
matched AS (
    SELECT 
        d.pcplanid,
        d.lineno as pclineno,
        o.rgstbillid,
        o.order_lineno as rgstlineno,
        LEAST(d.auditqty, o.rgsqty) as linkqty,
        CASE 
            WHEN o.inqty >= o.rgsqty THEN 'completed'
            WHEN o.inqty > 0 THEN 'partial_in'
            ELSE 'ordered'
        END as linkstatus,
        ROW_NUMBER() OVER (
            PARTITION BY d.pcplanid, d.lineno 
            ORDER BY o.order_date, o.rgstbillid, o.order_lineno
        ) as rn
    FROM demand_lines d
    JOIN order_lines o ON d.itemcd = o.itemcd 
        AND o.order_date >= d.demand_date
    WHERE NOT EXISTS (
        SELECT 1 FROM tpc20_requisition_order_link l 
        WHERE l.pcplanid = d.pcplanid AND l.pclineno = d.lineno
    )
)
SELECT 
    pcplanid,
    pclineno,
    rgstbillid,
    rgstlineno,
    linkqty,
    linkstatus,
    CURRENT_TIMESTAMP as gendate,
    'SYSTEM' as opercd
FROM matched
WHERE rn = 1;
*/

-- 执行后验证：查看执行状态分布
/*
SELECT 
    execution_status,
    COUNT(*) as cnt,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pct
FROM v_requisition_execution
WHERE pcplanid IN (SELECT pcplanid FROM tpc01_pcplan WHERE gendate < '2026-01-01' AND useflg = '1')
GROUP BY execution_status
ORDER BY cnt DESC;
*/
