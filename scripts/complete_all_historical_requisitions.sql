-- 方案B：将2026年前所有采购需求单标记为已完成
-- 策略：为每个需求单创建虚拟采购订单，建立完成关联

-- ============================================
-- 步骤0：数据备份（可选，建议先执行）
-- ============================================
-- CREATE TABLE backup_tpc20_before_completion AS SELECT * FROM tpc20_requisition_order_link;

-- ============================================
-- 步骤1：创建虚拟采购订单（每个需求单对应一个订单）
-- ============================================
-- 使用 HI + 需求单号后6位 作为虚拟订单号
INSERT INTO tpc12_register (
    rgstbillid, custcd, pcrep, rgstdate, useflg, gendate, opercd, 
    auditflg, auditman, auditdate, memo
)
SELECT 
    ('HI' || SUBSTRING(p.pcplanid FROM 3 FOR 6)) as rgstbillid,  -- HI000629 格式
    'SYSTEM' as custcd,
    'SYSTEM' as pcrep,
    p.gendate as rgstdate,  -- 使用需求单日期作为订单日期
    '1' as useflg,
    CURRENT_TIMESTAMP as gendate,
    'SYSTEM' as opercd,
    '2' as auditflg,  -- 已审核
    'SYSTEM' as auditman,
    CURRENT_DATE as auditdate,
    '历史数据自动归档订单，来源需求单：' || p.pcplanid as memo
FROM tpc01_pcplan p
WHERE p.gendate < '2026-01-01'
  AND p.useflg = '1'
  AND p.auditflg = '2'
  AND NOT EXISTS (
      SELECT 1 FROM tpc12_register r 
      WHERE r.rgstbillid = ('HI' || SUBSTRING(p.pcplanid FROM 3 FOR 6))
  );

-- 统计创建的虚拟订单数量
SELECT '创建的虚拟订单数量' as step, COUNT(*) as cnt 
FROM tpc12_register 
WHERE rgstbillid LIKE 'HI%' AND memo LIKE '%历史数据自动归档%';

-- ============================================
-- 步骤2：创建订单明细（每个需求明细对应一个订单明细）
-- ============================================
INSERT INTO tpc13_registerdt (
    rgstbillid, lineno, itemcd, rgsqty, rgstprice, 
    inqty, units, deliverdate,  -- inqty = rgsqty 表示全部已收货
    ref_pcplanid, ref_pclineno   -- 记录来源需求单信息
)
SELECT 
    ('HI' || SUBSTRING(p.pcplanid FROM 3 FOR 6)) as rgstbillid,
    dt.lineno,
    dt.itemcd,
    dt.auditqty as rgsqty,      -- 订单数量 = 需求审核数量
    0 as rgstprice,             -- 历史数据不记录价格
    dt.auditqty as inqty,       -- 已入库数量 = 订单数量（表示全部完成）
    dt.units,
    p.plandate as deliverdate,  -- 计划日期作为交付日期
    p.pcplanid as ref_pcplanid,
    dt.lineno as ref_pclineno
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE p.gendate < '2026-01-01'
  AND p.useflg = '1'
  AND p.auditflg = '2'
  AND dt.auditqty > 0
  AND NOT EXISTS (
      SELECT 1 FROM tpc13_registerdt rd 
      WHERE rd.rgstbillid = ('HI' || SUBSTRING(p.pcplanid FROM 3 FOR 6))
        AND rd.lineno = dt.lineno
  );

-- 统计创建的订单明细数量
SELECT '创建的订单明细数量' as step, COUNT(*) as cnt 
FROM tpc13_registerdt 
WHERE rgstbillid LIKE 'HI%' AND ref_pcplanid IN (SELECT pcplanid FROM tpc01_pcplan WHERE gendate < '2026-01-01');

-- ============================================
-- 步骤3：创建需求-订单关联（TPC20）
-- ============================================
INSERT INTO tpc20_requisition_order_link (
    pcplanid, pclineno, rgstbillid, rgstlineno, 
    linkqty, linkstatus, gendate, opercd
)
SELECT 
    p.pcplanid,
    dt.lineno as pclineno,
    ('HI' || SUBSTRING(p.pcplanid FROM 3 FOR 6)) as rgstbillid,
    dt.lineno as rgstlineno,
    dt.auditqty as linkqty,       -- 关联数量 = 审核数量
    'completed' as linkstatus,      -- 已完成状态
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

-- 统计创建的关联数量
SELECT '创建的TPC20关联数量' as step, COUNT(*) as cnt 
FROM tpc20_requisition_order_link 
WHERE opercd = 'SYSTEM' AND gendate::date = CURRENT_DATE;

-- ============================================
-- 步骤4：验证执行状态变化
-- ============================================
SELECT 
    '执行状态分布' as step,
    execution_status,
    COUNT(*) as cnt,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM v_requisition_execution
WHERE pcplanid IN (SELECT pcplanid FROM tpc01_pcplan WHERE gendate < '2026-01-01' AND useflg = '1')
GROUP BY execution_status
ORDER BY cnt DESC;

-- ============================================
-- 步骤5：验证关联详情（样本）
-- ============================================
SELECT 
    v.pcplanid,
    v.lineno,
    v.itemcd,
    v.audit_qty,
    v.ordered_qty,
    v.received_qty,
    v.execution_status,
    v.execution_rate
FROM v_requisition_execution v
WHERE v.pcplanid IN (
    SELECT pcplanid FROM tpc01_pcplan 
    WHERE gendate < '2026-01-01' AND useflg = '1'
    ORDER BY gendate DESC
    LIMIT 5
)
ORDER BY v.pcplanid, v.lineno;

-- ============================================
-- 回滚脚本（如需撤销，取消注释执行）
-- ============================================
/*
-- 删除今天创建的TPC20关联
DELETE FROM tpc20_requisition_order_link 
WHERE opercd = 'SYSTEM' AND gendate::date = CURRENT_DATE;

-- 删除虚拟订单明细
DELETE FROM tpc13_registerdt 
WHERE rgstbillid LIKE 'HI%' 
  AND ref_pcplanid IN (SELECT pcplanid FROM tpc01_pcplan WHERE gendate < '2026-01-01');

-- 删除虚拟订单
DELETE FROM tpc12_register 
WHERE rgstbillid LIKE 'HI%' 
  AND memo LIKE '%历史数据自动归档%';
*/
