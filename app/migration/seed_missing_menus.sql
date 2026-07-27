-- 补齐前端新增菜单的权限数据(tmc01_menus + tmc02_menusdt)
-- 解决: 预计划管理(plans)、机型押金标准(pos-models) 等菜单在管理员组(99)下不可见/无权限问题
-- 执行方式: psql -d myitsm -f app/migration/seed_missing_menus.sql
-- 幂等: 使用 ON CONFLICT DO NOTHING,可重复执行

-- 1. 菜单主表(tmc01_menus)
INSERT INTO tmc01_menus (menu_cd, menu_nm, parent_cd, menu_order, status, useflg, levelcd, childflg, openflg, created_at, updated_at)
SELECT v.menu_cd, v.menu_nm, v.parent_cd, v.menu_order, v.status, v.useflg, v.levelcd, v.childflg, v.openflg, NOW(), NOW()
FROM (VALUES
  -- 销售管理子菜单
  ('plans',       '预计划管理',   'sales', 10, '1', '1', '2', '0', '1'),
  ('sales-serves','呼出管理',     'sales', 20, '1', '1', '2', '0', '1'),
  ('sales-imple', '计划实施管理', 'sales', 30, '1', '1', '2', '0', '1'),
  ('sales-bills', '销售单据',     'sales', 40, '1', '1', '2', '0', '1'),
  ('sales-extend','延期管理',     'sales', 50, '1', '1', '2', '0', '1'),
  ('calls',       '话务台',       'sales', 60, '1', '1', '2', '0', '1'),
  -- 基础数据子菜单
  ('pos-models',  '机型押金标准', 'master', 25, '1', '1', '2', '0', '1'),
  ('asset-attrib','资产属性',     'master', 80, '1', '1', '2', '0', '1'),
  -- 仓储管理子菜单
  ('warehouse-config','仓库配置', 'warehouse', 10, '1', '1', '2', '0', '1'),
  ('pos-change',      '设备回收确认','warehouse', 70, '1', '1', '2', '0', '1'),
  ('overlost',        '盘盈盘亏',  'warehouse', 80, '1', '1', '2', '0', '1'),
  ('warehouse-reports','仓库报表', 'warehouse', 90, '1', '1', '2', '0', '1'),
  -- ITSM 子菜单
  ('free-replace', '免费更换',    'itsm', 90, '1', '1', '2', '0', '1'),
  ('archives',     '归档记录',    'itsm', 100, '1', '1', '2', '0', '1'),
  -- 采购管理子菜单
  ('proc-dashboard','执行看板',   'procurement', 5, '1', '1', '2', '0', '1'),
  ('proc-returns',  '采购退货',   'procurement', 70, '1', '1', '2', '0', '1'),
  ('appraisals',    '供应商评价', 'procurement', 80, '1', '1', '2', '0', '1'),
  -- 质检管理
  ('qc-results', '质检结果', 'qc', 10, '1', '1', '2', '0', '1'),
  ('qc-input',   '质检录入', 'qc', 20, '1', '1', '2', '0', '1'),
  -- 事务查询
  ('all-transactions', '全模块查询', 'transactions', 10, '1', '1', '2', '0', '1'),
  ('transfer',         '调拨流转',   'transactions', 20, '1', '1', '2', '0', '1'),
  -- 门户
  ('portal-users', '门户用户', 'portal', 10, '1', '1', '2', '0', '1'),
  ('repairs',       '自助报修', 'portal', 20, '1', '1', '2', '0', '1'),
  ('ratings',       '服务评价', 'portal', 30, '1', '1', '2', '0', '1'),
  -- SLA
  ('sla-defs',    'SLA定义',  'sla', 10, '1', '1', '2', '0', '1'),
  ('sla-tickets', 'SLA监控',  'sla', 20, '1', '1', '2', '0', '1'),
  -- 通知
  ('notif-tpl',  '通知模板', 'notification', 10, '1', '1', '2', '0', '1'),
  ('notif-list', '通知记录', 'notification', 20, '1', '1', '2', '0', '1'),
  -- 合同
  ('contracts', '合同管理', 'contract', 10, '1', '1', '2', '0', '1'),
  ('invoices',  '发票管理', 'contract', 20, '1', '1', '2', '0', '1'),
  -- 结算
  ('billing-rules', '结算规则', 'billing', 10, '1', '1', '2', '0', '1'),
  ('bills',         '账单管理', 'billing', 20, '1', '1', '2', '0', '1'),
  -- 财务
  ('accounts',     '会计科目', 'finance', 10, '1', '1', '2', '0', '1'),
  ('receivables',  '应收管理', 'finance', 20, '1', '1', '2', '0', '1'),
  ('payables',     '应付管理', 'finance', 30, '1', '1', '2', '0', '1'),
  ('payments',     '收付款管理','finance', 40, '1', '1', '2', '0', '1'),
  ('depreciation', '设备折旧', 'finance', 50, '1', '1', '2', '0', '1'),
  -- 押金
  ('deposits',       '押金台账', 'deposit', 10, '1', '1', '2', '0', '1'),
  ('deposit-details','押金明细', 'deposit', 20, '1', '1', '2', '0', '1'),
  ('deposit-io',     '押金流水', 'deposit', 30, '1', '1', '2', '0', '1'),
  -- 考勤
  ('attendance-list',  '考勤记录', 'attendance', 10, '1', '1', '2', '0', '1'),
  ('attendance-count', '考勤汇总', 'attendance', 20, '1', '1', '2', '0', '1'),
  -- 库存
  ('inv-limits',      '库存预警', 'inventory', 10, '1', '1', '2', '0', '1'),
  ('prices',          '价格管理', 'inventory', 20, '1', '1', '2', '0', '1'),
  ('adjust-prices',   '调价记录', 'inventory', 30, '1', '1', '2', '0', '1'),
  -- MES
  ('work-orders',    '生产工单', 'mes', 10, '1', '1', '2', '0', '1'),
  ('process-defs',   '工序定义', 'mes', 20, '1', '1', '2', '0', '1'),
  ('work-processes', '工单工序', 'mes', 30, '1', '1', '2', '0', '1'),
  ('materials',      '物料消耗', 'mes', 40, '1', '1', '2', '0', '1'),
  ('labels',         '标签管理', 'mes', 50, '1', '1', '2', '0', '1'),
  -- IoT
  ('device-conn',  '设备接入', 'iot', 10, '1', '1', '2', '0', '1'),
  ('device-data',  '设备数据', 'iot', 20, '1', '1', '2', '0', '1'),
  ('alert-rules',  '报警规则', 'iot', 30, '1', '1', '2', '0', '1'),
  ('alert-logs',   '报警记录', 'iot', 40, '1', '1', '2', '0', '1'),
  -- 报表
  ('reports-center', '报表中心', 'reports', 10, '1', '1', '2', '0', '1')
) AS v(menu_cd, menu_nm, parent_cd, menu_order, status, useflg, levelcd, childflg, openflg)
ON CONFLICT (menu_cd) DO NOTHING;

-- 2. 菜单明细表(tmc02_menusdt) — 每个菜单添加 view 功能权限
INSERT INTO tmc02_menusdt (menu_cd, func_cd, func_nm, useflg, created_at, updated_at)
SELECT m.menu_cd, 'view', m.menu_nm, '1', NOW(), NOW()
FROM tmc01_menus m
WHERE m.menu_cd IN (
  'plans','sales-serves','sales-imple','sales-bills','sales-extend','calls',
  'pos-models','asset-attrib',
  'warehouse-config','pos-change','overlost','warehouse-reports',
  'free-replace','archives',
  'proc-dashboard','proc-returns','appraisals',
  'qc-results','qc-input',
  'all-transactions','transfer',
  'portal-users','repairs','ratings',
  'sla-defs','sla-tickets',
  'notif-tpl','notif-list',
  'contracts','invoices',
  'billing-rules','bills',
  'accounts','receivables','payables','payments','depreciation',
  'deposits','deposit-details','deposit-io',
  'attendance-list','attendance-count',
  'inv-limits','prices','adjust-prices',
  'work-orders','process-defs','work-processes','materials','labels',
  'device-conn','device-data','alert-rules','alert-logs',
  'reports-center'
)
AND NOT EXISTS (
  SELECT 1 FROM tmc02_menusdt d WHERE d.menu_cd = m.menu_cd AND d.func_cd = 'view'
);

-- 3. 确保父级菜单存在(销售管理/基础数据等模块级菜单)
INSERT INTO tmc01_menus (menu_cd, menu_nm, parent_cd, menu_order, status, useflg, levelcd, childflg, openflg, created_at, updated_at)
SELECT v.menu_cd, v.menu_nm, v.parent_cd, v.menu_order, v.status, v.useflg, v.levelcd, v.childflg, v.openflg, NOW(), NOW()
FROM (VALUES
  ('sales',       '销售管理',   NULL, 60, '1', '1', '1', '1', '1'),
  ('master',      '基础数据',   NULL, 20, '1', '1', '1', '1', '1'),
  ('warehouse',   '仓储管理',   NULL, 30, '1', '1', '1', '1', '1'),
  ('itsm',        'ITSM工单',   NULL, 40, '1', '1', '1', '1', '1'),
  ('procurement', '采购管理',   NULL, 50, '1', '1', '1', '1', '1'),
  ('qc',          '质检管理',   NULL, 70, '1', '1', '1', '1', '1'),
  ('transactions','事务查询',   NULL, 80, '1', '1', '1', '1', '1'),
  ('portal',      '客户门户',   NULL, 90, '1', '1', '1', '1', '1'),
  ('sla',         'SLA管理',    NULL, 100, '1', '1', '1', '1', '1'),
  ('notification','通知管理',   NULL, 110, '1', '1', '1', '1', '1'),
  ('contract',    '合同管理',   NULL, 120, '1', '1', '1', '1', '1'),
  ('billing',     '结算管理',   NULL, 130, '1', '1', '1', '1', '1'),
  ('finance',     '财务管理',   NULL, 140, '1', '1', '1', '1', '1'),
  ('deposit',     '押金管理',   NULL, 150, '1', '1', '1', '1', '1'),
  ('attendance',  '考勤管理',   NULL, 160, '1', '1', '1', '1', '1'),
  ('inventory',   '库存管理',   NULL, 170, '1', '1', '1', '1', '1'),
  ('mes',         '生产管理',   NULL, 180, '1', '1', '1', '1', '1'),
  ('iot',         'IoT物联',    NULL, 190, '1', '1', '1', '1', '1'),
  ('reports',     '报表中心',   NULL, 200, '1', '1', '1', '1', '1')
) AS v(menu_cd, menu_nm, parent_cd, menu_order, status, useflg, levelcd, childflg, openflg)
ON CONFLICT (menu_cd) DO NOTHING;
