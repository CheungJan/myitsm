-- =============================================================================
-- 数据修复脚本：tit10_maintenanceday.requst_typ
-- =============================================================================
-- 背景：
--   PB 版本请求方式为硬编码 ddlb，取值：电话 / 微信 / 现场 / (空)。
--   重构后统一使用 FT（记录来源）系统字典：
--     00 电话 / 10 企业微信 / 20 微信公众号 / 30 微信内部群
--     40 微信交流群 / 50 微烟草 / 60 微信联系人 / 70 现场 / 99 呼出
--   旧值"微信"在新字典中拆分为 10/20/30/40/50/60 多个子类，
--   历史数据无法据上下文精确拆分，按行业惯例统一映射到默认码 60（微信联系人）。
--
-- 映射规则：
--   电话 → 00   （1:1 确定性）
--   现场 → 70   （1:1 确定性）
--   微信 → 60   （1:N 默认值，业务确认后执行）
--   (空) → 保持空（历史未录入，不补默认值，避免失真）
--
-- 执行前请先备份：
--   CREATE TABLE tit10_maintenanceday_bak_requst_typ AS
--   SELECT maintenance_id, requst_typ FROM tit10_maintenanceday;
-- =============================================================================

-- 1. 执行前对账（确认数据分布与预期一致）
-- 预期：空 45489 / 电话 30122 / 微信 1903 / 现场 590
SELECT COALESCE(requst_typ, '') AS requst_typ, COUNT(*) AS cnt
FROM tit10_maintenanceday
GROUP BY 1
ORDER BY 2 DESC;

-- 2. 电话 → 00
UPDATE tit10_maintenanceday
SET requst_typ = '00',
    updated_at = NOW()
WHERE requst_typ = '电话';

-- 3. 现场 → 70
UPDATE tit10_maintenanceday
SET requst_typ = '70',
    updated_at = NOW()
WHERE requst_typ = '现场';

-- 4. 微信 → 60（微信联系人，默认码）
--    旧值"微信"无法拆分到企业微信/公众号/群等子类，
--    统一落到"微信联系人"这一最贴近旧语义的默认码。
--    如业务后续需要细分，可据 backup 表人工复核后再调整。
UPDATE tit10_maintenanceday
SET requst_typ = '60',
    updated_at = NOW()
WHERE requst_typ = '微信';

-- 5. 执行后对账（应仅剩 NULL/'' 与 00/60/70 四类）
SELECT COALESCE(requst_typ, '') AS requst_typ, COUNT(*) AS cnt
FROM tit10_maintenanceday
GROUP BY 1
ORDER BY 2 DESC;

-- 6. 回滚预案（如需）
-- UPDATE tit10_maintenanceday t
-- SET requst_typ = b.requst_typ
-- FROM tit10_maintenanceday_bak_requst_typ b
-- WHERE t.maintenance_id = b.maintenance_id;
