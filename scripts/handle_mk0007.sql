-- 处理MK0007（仅需求有，无对应订单）
-- 策略：创建虚拟订单并标记为已完成

-- 步骤1：查看MK0007的需求情况
SELECT 
    'MK0007需求明细' as step,
    p.pcplanid,
    p.gendate::date as 需求日期,
    dt.lineno as 行号,
    dt.itemcd as 物料编码,
    dt.rgstqty as 申请数量,
    dt.auditqty as 审核数量,
    dt.units as 单位
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE dt.itemcd = 'MK0007'
  AND p.gendate < '2026-01-01'
  AND p.useflg = '1';

-- 步骤2：创建MK0007虚拟订单
INSERT INTO tpc12_register (
    rgstbillid, custcd, pcrep, rgstdate, useflg, 
    gendate, opercd, auditflg, auditman, auditdate, memo
)
SELECT 
    ('VM' || SUBSTRING(p.pcplanid FROM 3 FOR 6)) as rgstbillid,
    'SYSTEM' as custcd,
    'SYSTEM' as pcrep,
    p.gendate as rgstdate,
    '1' as useflg,
    CURRENT_TIMESTAMP as gendate,
    'SYSTEM' as opercd,
    '2' as auditflg,
    'SYSTEM' as auditman,
    CURRENT_DATE as auditdate,
    '虚拟订单：MK0007物料自动归档' as memo
FROM tpc01_pcplan p
WHERE p.pcplanid IN (
    SELECT DISTINCT pcplanid FROM tpc02_pcplandt 
    WHERE itemcd = 'MK0007' AND pcplanid IN (
        SELECT pcplanid FROM tpc01_pcplan 
        WHERE gendate < '2026-01-01' AND useflg = '1'
    )
)
AND NOT EXISTS (
    SELECT 1 FROM tpc12_register 
    WHERE rgstbillid = ('VM' || SUBSTRING(p.pcplanid FROM 3 FOR 6))
);

-- 步骤3：创建MK0007订单明细
INSERT INTO tpc13_registerdt (
    rgstbillid, lineno, itemcd, rgsqty, rgstprice, 
    inqty, units, deliverdate, ref_pcplanid, ref_pclineno
)
SELECT 
    ('VM' || SUBSTRING(p.pcplanid FROM 3 FOR 6)) as rgstbillid,
    dt.lineno,
    'MK0007',
    dt.auditqty as rgsqty,
    0 as rgstprice,
    dt.auditqty as inqty,  -- 全部收货完成
    dt.units,
    p.plandate as deliverdate,
    p.pcplanid as ref_pcplanid,
    dt.lineno as ref_pclineno
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE dt.itemcd = 'MK0007'
  AND p.gendate < '2026-01-01'
  AND p.useflg = '1'
  AND NOT EXISTS (
      SELECT 1 FROM tpc13_registerdt rd 
      WHERE rd.rgstbillid = ('VM' || SUBSTRING(p.pcplanid FROM 3 FOR 6))
        AND rd.lineno = dt.lineno
  );

-- 步骤4：创建MK0007的TPC20关联
INSERT INTO tpc20_requisition_order_link (
    pcplanid, pclineno, rgstbillid, rgstlineno, 
    linkqty, linkstatus, gendate, opercd, created_at, updated_at
)
SELECT 
    p.pcplanid,
    dt.lineno as pclineno,
    ('VM' || SUBSTRING(p.pcplanid FROM 3 FOR 6)) as rgstbillid,
    dt.lineno as rgstlineno,
    dt.auditqty as linkqty,
    'completed' as linkstatus,
    CURRENT_TIMESTAMP as gendate,
    'VM_LINK' as opercd,
    CURRENT_TIMESTAMP as created_at,
    CURRENT_TIMESTAMP as updated_at
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE dt.itemcd = 'MK0007'
  AND p.gendate < '2026-01-01'
  AND p.useflg = '1'
  AND NOT EXISTS (
      SELECT 1 FROM tpc20_requisition_order_link l 
      WHERE l.pcplanid = p.pcplanid AND l.pclineno = dt.lineno
  );

-- 步骤5：验证MK0007的执行状态
SELECT 
    'MK0007执行状态' as step,
    v.pcplanid,
    v.lineno,
    v.itemcd,
    v.audit_qty,
    v.ordered_qty,
    v.received_qty,
    v.execution_status,
    v.execution_rate
FROM v_requisition_execution v
WHERE v.itemcd = 'MK0007';

-- 步骤6：最终统计
SELECT 
    '最终执行状态分布' as step,
    execution_status,
    COUNT(*) as cnt,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) || '%' as pct
FROM v_requisition_execution
WHERE pcplanid IN (SELECT pcplanid FROM tpc01_pcplan WHERE gendate < '2026-01-01' AND useflg = '1')
GROUP BY execution_status
ORDER BY cnt DESC;
