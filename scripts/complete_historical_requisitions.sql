-- 将2026年之前创建的采购需求单标记为已完成
-- 策略：为这些历史需求单创建虚拟的"已完成"采购订单关联
-- 使 v_requisition_execution 视图计算结果显示"已完成"

-- 步骤1：创建虚拟的历史归档采购订单（如果不存在）
-- 使用一个特殊的订单号前缀 "HI" (History)
INSERT INTO tpc12_register (rgstbillid, custcd, pcrep, rgstdate, useflg, gendate, opercd, memo)
SELECT DISTINCT 
    'HI000001' as rgstbillid,
    'SYSTEM' as custcd,
    'SYSTEM' as pcrep,
    CURRENT_DATE as rgstdate,
    '1' as useflg,
    CURRENT_TIMESTAMP as gendate,
    'SYSTEM' as opercd,
    '历史数据归档用虚拟订单' as memo
WHERE NOT EXISTS (SELECT 1 FROM tpc12_register WHERE rgstbillid = 'HI000001');

-- 步骤2：为2026年前的采购需求明细创建关联记录
-- 关联数量 = 审核数量（表示已全部完成）
INSERT INTO tpc20_requisition_order_link (
    pcplanid, pclineno, rgstbillid, rgstlineno, 
    linkqty, linkstatus, gendate, opercd
)
SELECT 
    p.pcplanid,
    dt.lineno as pclineno,
    'HI000001' as rgstbillid,
    1 as rgstlineno,  -- 虚拟行号
    dt.auditqty as linkqty,  -- 关联数量 = 审核数量
    'completed' as linkstatus,  -- 已完成状态
    CURRENT_TIMESTAMP as gendate,
    'SYSTEM' as opercd
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE p.gendate < '2026-01-01'
  AND p.useflg = '1'
  AND p.auditflg = '2'  -- 只处理已审批的
  AND dt.auditqty > 0   -- 有审核数量的
  AND NOT EXISTS (  -- 避免重复插入
      SELECT 1 FROM tpc20_requisition_order_link l 
      WHERE l.pcplanid = p.pcplanid 
        AND l.pclineno = dt.lineno
  );

-- 步骤3：创建对应的订单明细（使 received_qty 计算正确）
INSERT INTO tpc13_registerdt (rgstbillid, lineno, itemcd, rgsqty, rgstprice, inqty, units)
SELECT DISTINCT
    'HI000001' as rgstbillid,
    1 as lineno,
    dt.itemcd,
    dt.auditqty as rgsqty,
    0 as rgstprice,  -- 历史数据价格设为0
    dt.auditqty as inqty,  -- 已入库数量 = 订单数量（表示已全部收货）
    dt.units
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE p.gendate < '2026-01-01'
  AND p.useflg = '1'
  AND p.auditflg = '2'
  AND dt.auditqty > 0
  AND NOT EXISTS (
      SELECT 1 FROM tpc13_registerdt rd 
      WHERE rd.rgstbillid = 'HI000001' 
        AND rd.lineno = 1
  );

-- 步骤4：验证更新结果
SELECT 
    p.pcplanid,
    p.gendate,
    COUNT(dt.lineno) as detail_count,
    SUM(dt.auditqty) as total_audit_qty
FROM tpc01_pcplan p
JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
WHERE p.gendate < '2026-01-01'
  AND p.useflg = '1'
  AND p.auditflg = '2'
GROUP BY p.pcplanid, p.gendate
ORDER BY p.gendate DESC
LIMIT 10;

-- 步骤5：查看执行状态验证
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
)
ORDER BY pcplanid, lineno
LIMIT 20;
