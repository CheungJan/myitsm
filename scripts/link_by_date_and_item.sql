-- 基于老PB逻辑：通过生成日期范围和itemcd关联需求单与订单
-- 关联规则：
-- 1. 订单日期在需求单日期之后（订单是下游单据）
-- 2. 相同itemcd
-- 3. 订单数量 <= 需求单可用余额

-- 步骤1：查看2026年前订单数据概况
SELECT 
    '2026年前订单概况' as section,
    COUNT(*) as total_orders,
    MIN(gendate) as earliest,
    MAX(gendate) as latest
FROM tpc12_register
WHERE gendate < '2026-01-01' AND useflg = '1';

-- 步骤2：查看订单明细数据（含itemcd）
SELECT 
    '订单明细概况' as section,
    COUNT(*) as total_lines,
    COUNT(DISTINCT rgstbillid) as order_count,
    COUNT(DISTINCT itemcd) as item_count,
    SUM(rgsqty) as total_qty,
    SUM(inqty) as total_inqty
FROM tpc13_registerdt
WHERE rgstbillid IN (SELECT rgstbillid FROM tpc12_register WHERE gendate < '2026-01-01' AND useflg = '1');

-- 步骤3：基于日期范围和itemcd创建关联
-- 逻辑：对于每个需求单明细，查找日期范围内相同itemcd的订单明细进行关联
WITH requisition_lines AS (
    -- 2026年前的需求单明细（已审批，有审核数量）
    SELECT 
        p.pcplanid,
        p.gendate as req_date,
        dt.lineno,
        dt.itemcd,
        dt.auditqty,
        dt.auditqty - COALESCE(
            (SELECT SUM(linkqty) FROM tpc20_requisition_order_link l 
             WHERE l.pcplanid = p.pcplanid AND l.pclineno = dt.lineno), 0
        ) as remaining_qty
    FROM tpc01_pcplan p
    JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
    WHERE p.gendate < '2026-01-01'
      AND p.useflg = '1'
      AND p.auditflg = '2'
      AND dt.auditqty > 0
),
order_lines AS (
    -- 2026年前的订单明细
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
      AND r.useflg = '1'
),
matched_links AS (
    -- 匹配：订单日期 >= 需求单日期（下游单据），相同itemcd
    SELECT 
        req.pcplanid,
        req.lineno as pclineno,
        ord.rgstbillid,
        ord.order_lineno as rgstlineno,
        req.itemcd,
        LEAST(req.remaining_qty, ord.rgsqty) as linkqty,  -- 关联数量为两者较小值
        CASE 
            WHEN ord.inqty >= ord.rgsqty THEN 'completed'
            WHEN ord.inqty > 0 THEN 'partial_in'
            ELSE 'ordered'
        END as linkstatus,
        ROW_NUMBER() OVER (
            PARTITION BY req.pcplanid, req.lineno 
            ORDER BY ord.order_date, ord.rgstbillid, ord.order_lineno
        ) as rn  -- 每个需求单行只关联一个订单（最早的）
    FROM requisition_lines req
    JOIN order_lines ord ON req.itemcd = ord.itemcd 
        AND ord.order_date >= req.req_date  -- 订单日期在需求单之后
    WHERE req.remaining_qty > 0  -- 还有剩余数量需要关联
)
-- 预览将要创建的关联（前10条）
SELECT 
    pcplanid,
    pclineno,
    rgstbillid,
    rgstlineno,
    itemcd,
    linkqty,
    linkstatus
FROM matched_links
WHERE rn = 1  -- 只取每个需求单行的第一个匹配订单
ORDER BY pcplanid, pclineno
LIMIT 20;

-- 步骤4：实际插入关联记录（取消注释执行）
/*
INSERT INTO tpc20_requisition_order_link (
    pcplanid, pclineno, rgstbillid, rgstlineno, 
    linkqty, linkstatus, gendate, opercd
)
WITH requisition_lines AS (
    SELECT 
        p.pcplanid,
        p.gendate as req_date,
        dt.lineno,
        dt.itemcd,
        dt.auditqty,
        dt.auditqty - COALESCE(
            (SELECT SUM(linkqty) FROM tpc20_requisition_order_link l 
             WHERE l.pcplanid = p.pcplanid AND l.pclineno = dt.lineno), 0
        ) as remaining_qty
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
      AND r.useflg = '1'
),
matched_links AS (
    SELECT 
        req.pcplanid,
        req.lineno as pclineno,
        ord.rgstbillid,
        ord.order_lineno as rgstlineno,
        LEAST(req.remaining_qty, ord.rgsqty) as linkqty,
        CASE 
            WHEN ord.inqty >= ord.rgsqty THEN 'completed'
            WHEN ord.inqty > 0 THEN 'partial_in'
            ELSE 'ordered'
        END as linkstatus,
        ROW_NUMBER() OVER (
            PARTITION BY req.pcplanid, req.lineno 
            ORDER BY ord.order_date, ord.rgstbillid, ord.order_lineno
        ) as rn
    FROM requisition_lines req
    JOIN order_lines ord ON req.itemcd = ord.itemcd 
        AND ord.order_date >= req.req_date
    WHERE req.remaining_qty > 0
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
FROM matched_links
WHERE rn = 1
  AND NOT EXISTS (
      SELECT 1 FROM tpc20_requisition_order_link l 
      WHERE l.pcplanid = matched_links.pcplanid 
        AND l.pclineno = matched_links.pclineno
  );
*/

-- 步骤5：验证关联后的执行状态
/*
SELECT 
    execution_status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM v_requisition_execution
WHERE pcplanid IN (SELECT pcplanid FROM tpc01_pcplan WHERE gendate < '2026-01-01' AND useflg = '1')
GROUP BY execution_status
ORDER BY count DESC;
*/
