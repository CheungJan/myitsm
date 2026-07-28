-- 将2026年之前创建的采购需求单标记为已完成（v2 - 避免数据冲突）
-- 策略：为每个历史需求单创建独立的虚拟"已完成"采购订单
-- 确保与现有 tpc12/tpc13 数据无冲突

-- 步骤1：先检查2026年前的需求单数据概况
SELECT 
    COUNT(*) as total_requisitions,
    COUNT(CASE WHEN auditflg='2' THEN 1 END) as approved_count,
    MIN(gendate) as earliest_date,
    MAX(gendate) as latest_date
FROM tpc01_pcplan 
WHERE gendate < '2026-01-01' AND useflg = '1';

-- 步骤2：检查是否已有关联记录（避免重复处理）
SELECT 
    COUNT(*) as existing_links
FROM tpc20_requisition_order_link l
JOIN tpc01_pcplan p ON l.pcplanid = p.pcplanid
WHERE p.gendate < '2026-01-01' AND p.useflg = '1';

-- 步骤3：创建虚拟采购订单（每个需求单一个）
-- 使用 HI + 需求单号 作为虚拟订单号（8位限制）
INSERT INTO tpc12_register (rgstbillid, custcd, pcrep, rgstdate, useflg, gendate, opercd, memo)
SELECT 
    ('H' || RIGHT(p.pcplanid, 7))::varchar(8) as rgstbillid,  -- HI+原单号后7位
    'SYSTEM' as custcd,
    'SYSTEM' as pcrep,
    CURRENT_DATE as rgstdate,
    '1' as useflg,
    CURRENT_TIMESTAMP as gendate,
    'SYSTEM' as opercd,
    '历史归档：' || p.pcplanid as memo
FROM tpc01_pcplan p
WHERE p.gendate < '2026-01-01'
  AND p.useflg = '1'
  AND p.auditflg = '2'
  AND NOT EXISTS (SELECT 1 FROM tpc12_register r WHERE r.rgstbillid = ('H' || RIGHT(p.pcplanid, 7))::varchar(8))
ON CONFLICT (rgstbillid) DO NOTHING;

-- 步骤4：创建需求-订单关联（每条明细一行）
INSERT INTO tpc20_requisition_order_link (
    pcplanid, pclineno, rgstbillid, rgstlineno, 
    linkqty, linkstatus, gendate, opercd
)
SELECT 
    p.pcplanid,
    dt.lineno as pclineno,
    ('H' || RIGHT(p.pcplanid, 7))::varchar(8) as rgstbillid,
    dt.lineno as rgstlineno,  -- 使用明细行号保持一致
    dt.auditqty as linkqty,
    'completed' as linkstatus,
    CURRENT_TIMESTAMP as gendate,
    'SYSTEM' as opercd
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE p.gendate < '2026-01-01'
  AND p.useflg = '1'
  AND p.auditflg = '2'
  AND dt.auditqty > 0
  AND NOT EXISTS (
      SELECT 1 FROM tpc20_requisition_order_link l 
      WHERE l.pcplanid = p.pcplanid AND l.pclineno = dt.lineno
  );

-- 步骤5：创建订单明细（使 received_qty 计算正确）
INSERT INTO tpc13_registerdt (rgstbillid, lineno, itemcd, rgsqty, rgstprice, inqty, units)
SELECT 
    ('H' || RIGHT(p.pcplanid, 7))::varchar(8) as rgstbillid,
    dt.lineno,
    dt.itemcd,
    dt.auditqty as rgsqty,
    0 as rgstprice,
    dt.auditqty as inqty,  -- 已入库 = 订单数量（表示全部完成）
    dt.units
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE p.gendate < '2026-01-01'
  AND p.useflg = '1'
  AND p.auditflg = '2'
  AND dt.auditqty > 0
  AND NOT EXISTS (
      SELECT 1 FROM tpc13_registerdt rd 
      WHERE rd.rgstbillid = ('H' || RIGHT(p.pcplanid, 7))::varchar(8)
        AND rd.lineno = dt.lineno
  );

-- 步骤6：验证更新结果
SELECT 
    p.pcplanid,
    p.gendate,
    COUNT(dt.lineno) as detail_count,
    SUM(dt.auditqty) as total_audit_qty,
    ('H' || RIGHT(p.pcplanid, 7))::varchar(8) as virtual_order
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE p.gendate < '2026-01-01'
  AND p.useflg = '1'
  AND p.auditflg = '2'
GROUP BY p.pcplanid, p.gendate
ORDER BY p.gendate DESC
LIMIT 10;

-- 步骤7：查看执行状态验证
SELECT 
    pcplanid,
    lineno,
    itemcd,
    plan_qty,
    audit_qty,
    ordered_qty,
    received_qty,
    available_qty,
    execution_status,
    execution_rate
FROM v_requisition_execution
WHERE pcplanid IN (
    SELECT pcplanid FROM tpc01_pcplan 
    WHERE gendate < '2026-01-01' AND useflg = '1' AND auditflg = '2'
    LIMIT 5
)
ORDER BY pcplanid, lineno;
