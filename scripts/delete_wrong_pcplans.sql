-- 删除错误的需求单号记录
-- 目标单号: 1832D5FB, 79184E44, 2DB56F0B
-- 执行顺序: 先删关联表，再删明细表，最后删主表

-- ============================================
-- 第一步：查看将要删除的数据（预览）
-- ============================================

-- 查看主表数据
SELECT pcplanid, pctyp, auditflg, gendate, opercd, memo 
FROM tpc01_pcplan 
WHERE pcplanid IN ('1832D5FB', '79184E44', '2DB56F0B');

-- 查看明细表数据
SELECT pcplanid, lineno, itemcd, rgstqty, auditqty, units 
FROM tpc02_pcplandt 
WHERE pcplanid IN ('1832D5FB', '79184E44', '2DB56F0B')
ORDER BY pcplanid, lineno;

-- 查看关联表数据（如果有的话）
SELECT pcplanid, pclineno, rgstbillid, linkqty, linkstatus 
FROM tpc20_requisition_order_link 
WHERE pcplanid IN ('1832D5FB', '79184E44', '2DB56F0B')
ORDER BY pcplanid;


-- ============================================
-- 第二步：执行删除（确认无误后再执行）
-- ============================================

-- 开启事务
BEGIN;

-- 1. 删除关联表数据
DELETE FROM tpc20_requisition_order_link 
WHERE pcplanid IN ('1832D5FB', '79184E44', '2DB56F0B');

-- 2. 删除明细表数据
DELETE FROM tpc02_pcplandt 
WHERE pcplanid IN ('1832D5FB', '79184E44', '2DB56F0B');

-- 3. 删除主表数据
DELETE FROM tpc01_pcplan 
WHERE pcplanid IN ('1832D5FB', '79184E44', '2DB56F0B');

-- 提交事务
COMMIT;


-- ============================================
-- 第三步：验证删除结果
-- ============================================

-- 确认已删除
SELECT COUNT(*) as remaining_count 
FROM tpc01_pcplan 
WHERE pcplanid IN ('1832D5FB', '79184E44', '2DB56F0B');

-- 确认明细表已删除
SELECT COUNT(*) as remaining_details 
FROM tpc02_pcplandt 
WHERE pcplanid IN ('1832D5FB', '79184E44', '2DB56F0B');

-- 确认关联表已删除
SELECT COUNT(*) as remaining_links 
FROM tpc20_requisition_order_link 
WHERE pcplanid IN ('1832D5FB', '79184E44', '2DB56F0B');
