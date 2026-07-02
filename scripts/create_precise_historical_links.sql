-- 精确关联历史数据：基于真实订单 + 虚拟订单补充
-- 策略：117种交集物料用真实订单关联，MK0007用虚拟订单标记完成

-- ============================================
-- 步骤1：数据预览
-- ============================================
SELECT '需求明细总数' as item, COUNT(*) as cnt FROM tpc02_pcplandt dt WHERE dt.pcplanid IN (SELECT pcplanid FROM tpc01_pcplan WHERE gendate < '2026-01-01' AND useflg = '1' AND auditflg = '2')
UNION ALL
SELECT '订单明细总数', COUNT(*) FROM tpc13_registerdt rd WHERE rd.rgstbillid IN (SELECT rgstbillid FROM tpc12_register WHERE gendate < '2026-01-01')
UNION ALL
SELECT '已有TPC20关联', COUNT(*) FROM tpc20_requisition_order_link;

-- ============================================
-- 步骤2：创建真实订单关联（117种交集物料）
-- 规则：订单日期 >= 需求日期，相同itemcd，数量匹配
-- ============================================
WITH demand_lines AS (
    -- 2026年前需求明细（交集物料，排除MK0007）
    SELECT 
        p.pcplanid,
        p.gendate as demand_date,
        dt.lineno,
        dt.itemcd,
        dt.auditqty,
        dt.units
    FROM tpc01_pcplan p
    JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
    WHERE p.gendate < '2026-01-01'
      AND p.useflg = '1'
      AND p.auditflg = '2'
      AND dt.auditqty > 0
      AND dt.itemcd != 'MK0007'  -- 排除仅需求有的物料
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
    -- 匹配：相同itemcd，订单日期在需求日期之后（允许90天内）
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
        AND o.order_date < d.demand_date + INTERVAL '365 days'  -- 1年内
    WHERE NOT EXISTS (
        SELECT 1 FROM tpc20_requisition_order_link l 
        WHERE l.pcplanid = d.pcplanid AND l.pclineno = d.lineno
    )
)
-- 预览前20条将要创建的关联
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

-- ============================================
-- 步骤3：执行真实订单关联插入（取消注释执行）
-- ============================================
/*
INSERT INTO tpc20_requisition_order_link (
    pcplanid, pclineno, rgstbillid, rgstlineno, 
    linkqty, linkstatus, gendate, opercd
)
WITH demand_lines AS (
    SELECT p.pcplanid, p.gendate as demand_date, dt.lineno, dt.itemcd, dt.auditqty
    FROM tpc01_pcplan p
    JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
    WHERE p.gendate < '2026-01-01' AND p.useflg = '1' AND p.auditflg = '2'
      AND dt.auditqty > 0 AND dt.itemcd != 'MK0007'
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

-- ============================================
-- 步骤4：为MK0007创建虚拟订单（仅需求有的物料）
-- ============================================
-- 查看MK0007的需求情况
SELECT 
    p.pcplanid,
    p.gendate::date,
    dt.lineno,
    dt.itemcd,
    dt.auditqty
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE dt.itemcd = 'MK0007'
  AND p.gendate < '2026-01-01'
  AND p.useflg = '1';

-- ============================================
-- 步骤5：创建MK0007虚拟订单（取消注释执行）
-- ============================================
/*
-- 创建虚拟订单
INSERT INTO tpc12_register (rgstbillid, custcd, pcrep, rgstdate, useflg, gendate, opercd, auditflg, memo)
SELECT ('VM' || SUBSTRING(pcplanid FROM 3 FOR 6)), 'SYSTEM', 'SYSTEM', gendate, '1', CURRENT_TIMESTAMP, 'SYSTEM', '2', 
       '虚拟订单：MK0007物料自动归档'
FROM tpc01_pcplan
WHERE pcplanid IN (SELECT DISTINCT pcplanid FROM tpc02_pcplandt WHERE itemcd = 'MK0007' AND pcplanid IN (SELECT pcplanid FROM tpc01_pcplan WHERE gendate < '2026-01-01'))
AND NOT EXISTS (SELECT 1 FROM tpc12_register WHERE rgstbillid = ('VM' || SUBSTRING(pcplanid FROM 3 FOR 6)));

-- 创建虚拟订单明细
INSERT INTO tpc13_registerdt (rgstbillid, lineno, itemcd, rgsqty, inqty, ref_pcplanid, ref_pclineno)
SELECT ('VM' || SUBSTRING(p.pcplanid FROM 3 FOR 6)), dt.lineno, 'MK0007', dt.auditqty, dt.auditqty, p.pcplanid, dt.lineno
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE dt.itemcd = 'MK0007' AND p.gendate < '2026-01-01' AND p.useflg = '1';

-- 创建MK0007的TPC20关联
INSERT INTO tpc20_requisition_order_link (pcplanid, pclineno, rgstbillid, rgstlineno, linkqty, linkstatus, gendate, opercd)
SELECT p.pcplanid, dt.lineno, ('VM' || SUBSTRING(p.pcplanid FROM 3 FOR 6)), dt.lineno, dt.auditqty, 'completed', CURRENT_TIMESTAMP, 'VM_LINK'
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE dt.itemcd = 'MK0007' AND p.gendate < '2026-01-01' AND p.useflg = '1'
AND NOT EXISTS (SELECT 1 FROM tpc20_requisition_order_link l WHERE l.pcplanid = p.pcplanid AND l.pclineno = dt.lineno);
*/

-- ============================================
-- 步骤6：验证执行结果
-- ============================================
-- 统计关联后各状态的数量
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

-- 查看MK0007的执行状态
/*
SELECT v.pcplanid, v.lineno, v.itemcd, v.audit_qty, v.execution_status
FROM v_requisition_execution v
WHERE v.itemcd = 'MK0007';
*/
