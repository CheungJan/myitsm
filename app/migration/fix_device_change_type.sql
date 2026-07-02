-- =============================================================================
-- 数据修复脚本：tit16_device_change.change_type
-- =============================================================================
-- 背景：
--   迁移脚本错误地将 change_type 写成了数字码（10/30），而非字母码（CK/BQ/BG）。
--   Oracle 原始数据：CK 232 / BQ 167 / BG 298 = 697
--   PG 迁移后数据：  10 530 / 30 167        = 697
--   其中 530 = 232(CK) + 298(BG)，167 = 167(BQ)
--
-- 修复映射（按业务语义重新定义）：
--   CK = 仅磁卡号变更（new_store_card 非空，device_id 为空）
--   BG = 磁卡号+设备同时变更（device_id 非空）
--   BQ = 信息变更（地址/电话/联系人等，无磁卡号/设备变更）
--
-- 执行前请先备份：CREATE TABLE tit16_device_change_bak AS SELECT * FROM tit16_device_change;
-- =============================================================================

-- 1. 对账查询（执行前先跑，确认拆分规则正确）
-- 预期结果：BG候选 ≈ 298, CK候选 ≈ 232, BQ(30) = 167
SELECT
    CASE
        WHEN change_type = '30' THEN 'BQ'
        WHEN change_type = '10' AND device_id IS NOT NULL AND btrim(device_id) <> '' THEN 'BG候选'
        WHEN change_type = '10' THEN 'CK候选'
        ELSE '其他(' || change_type || ')'
    END AS guess,
    COUNT(*) AS cnt
FROM tit16_device_change
GROUP BY 1
ORDER BY 1;

-- 2. 修复 30 → BQ（167 条，可直接改）
UPDATE tit16_device_change
SET change_type = 'BQ',
    updated_at = NOW()
WHERE change_type = '30';

-- 3. 修复 10 → BG（device_id 非空 = 磁卡号+设备变更）
UPDATE tit16_device_change
SET change_type = 'BG',
    updated_at = NOW()
WHERE change_type = '10'
  AND device_id IS NOT NULL
  AND btrim(device_id) <> '';

-- 4. 修复 10 → CK（剩余 = 仅磁卡号变更）
UPDATE tit16_device_change
SET change_type = 'CK',
    updated_at = NOW()
WHERE change_type = '10';

-- 5. 修复后对账（应与 Oracle 原始数量一致：CK 232 / BQ 167 / BG 298）
SELECT change_type, COUNT(*) AS cnt
FROM tit16_device_change
GROUP BY change_type
ORDER BY change_type;
