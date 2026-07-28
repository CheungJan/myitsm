-- 分析2026年前历史数据的关联情况
-- 目的：了解现有数据状态，决定如何处理

-- 1. 2026年前需求单概况
SELECT 
    '2026年前需求单概况' as section,
    COUNT(*) as total_count,
    COUNT(CASE WHEN auditflg='0' THEN 1 END) as unapproved,
    COUNT(CASE WHEN auditflg='1' THEN 1 END) as in_review,
    COUNT(CASE WHEN auditflg='2' THEN 1 END) as approved,
    COUNT(CASE WHEN auditflg='9' THEN 1 END) as voided,
    MIN(gendate) as earliest,
    MAX(gendate) as latest
FROM tpc01_pcplan 
WHERE gendate < '2026-01-01' AND useflg = '1';

-- 2. 检查2026年前需求单是否已有订单关联（TPC20新表）
SELECT 
    '新系统关联情况(TPC20)' as section,
    COUNT(DISTINCT l.pcplanid) as linked_plans,
    COUNT(*) as total_links,
    SUM(l.linkqty) as total_linked_qty
FROM tpc20_requisition_order_link l
JOIN tpc01_pcplan p ON l.pcplanid = p.pcplanid
WHERE p.gendate < '2026-01-01' AND p.useflg = '1';

-- 3. 检查2026年前需求单明细的执行状态（新系统视图）
SELECT 
    '新系统执行状态分布' as section,
    execution_status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM v_requisition_execution
WHERE pcplanid IN (SELECT pcplanid FROM tpc01_pcplan WHERE gendate < '2026-01-01' AND useflg = '1')
GROUP BY execution_status
ORDER BY count DESC;

-- 4. 检查订单明细中ref_pcplanid的关联情况（冗余字段）
SELECT 
    '订单明细冗余字段关联' as section,
    COUNT(DISTINCT ref_pcplanid) as linked_plans,
    COUNT(*) as total_lines,
    SUM(CASE WHEN ref_pcplanid IS NOT NULL THEN 1 ELSE 0 END) as with_ref
FROM tpc13_registerdt
WHERE rgstbillid IN (
    SELECT rgstbillid FROM tpc12_register WHERE gendate < '2026-01-01' AND useflg = '1'
);

-- 5. 查看具体样本：2026年前已审批但未开始的需求单
SELECT 
    p.pcplanid,
    p.gendate,
    p.auditflg,
    p.slbillid,
    COUNT(dt.lineno) as detail_count,
    SUM(dt.auditqty) as total_audit_qty
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE p.gendate < '2026-01-01'
  AND p.useflg = '1'
  AND p.auditflg = '2'
  AND NOT EXISTS (
      SELECT 1 FROM tpc20_requisition_order_link l WHERE l.pcplanid = p.pcplanid
  )
GROUP BY p.pcplanid, p.gendate, p.auditflg, p.slbillid
ORDER BY p.gendate DESC
LIMIT 10;

-- 6. 查看有销售单号的需求单（可能是老系统遗留）
SELECT 
    p.pcplanid,
    p.gendate,
    p.slbillid,
    COUNT(dt.lineno) as detail_count,
    (SELECT rgstbillid FROM tpc20_requisition_order_link l WHERE l.pcplanid = p.pcplanid LIMIT 1) as linked_order
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE p.gendate < '2026-01-01'
  AND p.useflg = '1'
  AND p.slbillid IS NOT NULL
GROUP BY p.pcplanid, p.gendate, p.slbillid
ORDER BY p.gendate DESC
LIMIT 10;
