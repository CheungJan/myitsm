-- 117种交集物料关联执行脚本
-- 执行步骤：1.备份 -> 2.插入 -> 3.验证

-- ============================================
-- 步骤1：备份TPC20表
-- ============================================
DROP TABLE IF EXISTS backup_tpc20_20260523;
CREATE TABLE backup_tpc20_20260523 AS SELECT * FROM tpc20_requisition_order_link;

SELECT '备份完成' as step, COUNT(*) as backup_rows FROM backup_tpc20_20260523;

-- ============================================
-- 步骤2：执行117种物料关联插入
-- ============================================
INSERT INTO tpc20_requisition_order_link (
    pcplanid, pclineno, rgstbillid, rgstlineno, 
    linkqty, linkstatus, gendate, opercd, created_at, updated_at
)
WITH demand AS (
    SELECT p.pcplanid, p.gendate as demand_date, d.lineno, d.itemcd, d.auditqty
    FROM tpc01_pcplan p
    JOIN tpc02_pcplandt d ON p.pcplanid = d.pcplanid
    WHERE p.gendate < '2026-01-01'
      AND p.useflg = '1'
      AND p.auditflg = '2'
      AND d.auditqty > 0
      AND d.itemcd NOT IN ('MK0007', 'MT7002')
),
orders AS (
    SELECT r.rgstbillid, r.gendate as order_date, o.lineno, o.itemcd, o.rgsqty, o.inqty
    FROM tpc12_register r
    JOIN tpc13_registerdt o ON r.rgstbillid = o.rgstbillid
    WHERE r.gendate < '2026-01-01'
),
matched AS (
    SELECT 
        d.pcplanid, d.lineno as pclineno,
        o.rgstbillid, o.lineno as rgstlineno,
        LEAST(d.auditqty, o.rgsqty) as linkqty,
        CASE WHEN o.inqty >= o.rgsqty THEN 'completed'
             WHEN o.inqty > 0 THEN 'partial_in'
             ELSE 'ordered' END as linkstatus,
        ROW_NUMBER() OVER (PARTITION BY d.pcplanid, d.lineno 
                          ORDER BY o.order_date, o.rgstbillid, o.lineno) as rn
    FROM demand d
    JOIN orders o ON d.itemcd = o.itemcd 
        AND o.order_date >= d.demand_date
        AND o.order_date < d.demand_date + INTERVAL '365 days'
)
SELECT 
    pcplanid, pclineno, rgstbillid, rgstlineno,
    linkqty, linkstatus, NOW(), 'AUTO_LINK', NOW(), NOW()
FROM matched
WHERE rn = 1;

-- ============================================
-- 步骤3：验证插入结果
-- ============================================
SELECT 
    '插入结果统计' as step,
    COUNT(*) as total_inserted,
    COUNT(CASE WHEN linkstatus = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN linkstatus = 'ordered' THEN 1 END) as ordered,
    COUNT(CASE WHEN linkstatus = 'partial_in' THEN 1 END) as partial
FROM tpc20_requisition_order_link 
WHERE opercd = 'AUTO_LINK';

-- ============================================
-- 步骤4：验证执行状态视图
-- ============================================
SELECT 
    '执行状态分布' as step,
    execution_status,
    COUNT(*) as cnt,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pct
FROM v_requisition_execution
WHERE pcplanid IN (SELECT pcplanid FROM tpc01_pcplan WHERE gendate < '2026-01-01' AND useflg = '1')
GROUP BY execution_status
ORDER BY cnt DESC;

-- ============================================
-- 步骤5：查看样本数据
-- ============================================
SELECT 
    '样本数据' as step,
    pcplanid, pclineno, rgstbillid, rgstlineno, linkqty, linkstatus, opercd
FROM tpc20_requisition_order_link 
WHERE opercd = 'AUTO_LINK'
ORDER BY pcplanid, pclineno
LIMIT 10;

-- ============================================
-- 回滚脚本（如需撤销）
-- ============================================
/*
-- 删除今天插入的数据
DELETE FROM tpc20_requisition_order_link WHERE opercd = 'AUTO_LINK';

-- 或从备份恢复
-- TRUNCATE tpc20_requisition_order_link;
-- INSERT INTO tpc20_requisition_order_link SELECT * FROM backup_tpc20_20260523;
*/
