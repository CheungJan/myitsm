/** 前端菜单配置 — 与前端路由对齐，后续可从数据库动态加载 */

export interface MenuConfig {
    menu_cd: string
    menu_nm: string
    icon?: string
    path?: string
    children?: MenuConfig[]
}

export const FRONTEND_MENUS: MenuConfig[] = [
    {
        menu_cd: 'dashboard', menu_nm: '首页', icon: 'HomeFilled',
        path: '/dashboard'
    },
    {
        menu_cd: 'system', menu_nm: '系统管理',
        children: [
            { menu_cd: 'users', menu_nm: '用户管理', path: '/system/users' },
            { menu_cd: 'depts', menu_nm: '部门管理', path: '/system/departments' },
            { menu_cd: 'groups', menu_nm: '用户组管理', path: '/system/groups' },
            { menu_cd: 'params', menu_nm: '系统参数', path: '/system/params' },
            { menu_cd: 'codes', menu_nm: '系统字典', path: '/system/codes' },
            { menu_cd: 'transfers', menu_nm: '调拨科目', path: '/system/transfers' }
        ]
    },
    {
        menu_cd: 'master', menu_nm: '基础数据',
        children: [
            { menu_cd: 'items', menu_nm: '物料管理', path: '/master/items' },
            { menu_cd: 'bom', menu_nm: 'BOM管理', path: '/master/bom' },
            { menu_cd: 'pos-models', menu_nm: '机型押金标准', path: '/master/pos-models' },
            { menu_cd: 'customers', menu_nm: '客户管理', path: '/master/customers' },
            { menu_cd: 'eid', menu_nm: 'EID 管理', path: '/master/eid' },
            { menu_cd: 'assets', menu_nm: '资产台账', path: '/master/assets' },
            { menu_cd: 'warehouses', menu_nm: '仓库管理', path: '/master/warehouses' },
            { menu_cd: 'asset-attrib', menu_nm: '资产属性', path: '/master/asset-attrib' }
        ]
    },
    {
        menu_cd: 'warehouse', menu_nm: '仓储管理',
        children: [
            { menu_cd: 'warehouse-config', menu_nm: '仓库配置', path: '/warehouse/config' },
            { menu_cd: 'stock-in', menu_nm: '入库单管理', path: '/warehouse/stock-in' },
            { menu_cd: 'stock-out', menu_nm: '出库单管理', path: '/warehouse/stock-out' },
            { menu_cd: 'stock', menu_nm: '库存查询', path: '/warehouse/stock-balance' },
            { menu_cd: 'stock-movement', menu_nm: '库存流水', path: '/warehouse/stock-movement' },
            { menu_cd: 'asset-check', menu_nm: '资产盘点', path: '/warehouse/asset-check' },
            { menu_cd: 'pos-change', menu_nm: '设备回收确认', path: '/warehouse/pos-change' },
            { menu_cd: 'overlost', menu_nm: '盘盈盘亏', path: '/warehouse/overlost' },
            { menu_cd: 'warehouse-reports', menu_nm: '仓库报表', path: '/warehouse/reports' }
        ]
    },
    {
        menu_cd: 'procurement', menu_nm: '采购管理',
        children: [
            { menu_cd: 'proc-dashboard', menu_nm: '执行看板', path: '/procurement/dashboard' },
            { menu_cd: 'proc-requisitions', menu_nm: '采购需求', path: '/procurement/requisitions' },
            { menu_cd: 'proc-orders', menu_nm: '采购订单', path: '/procurement/orders' },
            { menu_cd: 'proc-settlements', menu_nm: '采购结算单', path: '/procurement/settlements' },
            { menu_cd: 'proc-returns', menu_nm: '采购退货', path: '/procurement/returns' },
            { menu_cd: 'suppliers', menu_nm: '供应商管理', path: '/procurement/suppliers' },
            { menu_cd: 'appraisals', menu_nm: '供应商评价', path: '/procurement/appraisals' }
        ]
    },
    {
        menu_cd: 'itsm', menu_nm: 'ITSM工单',
        children: [
            { menu_cd: 'maintenance', menu_nm: '日常维修', path: '/itsm/maintenance' },
            { menu_cd: 'renovate', menu_nm: '旧机翻新', path: '/itsm/renovate' },
            { menu_cd: 'device-change', menu_nm: '磁卡号变更', path: '/itsm/device-change' },
            { menu_cd: 'store-close', menu_nm: '门店关闭', path: '/itsm/store-close' },
            { menu_cd: 'itsm-open', menu_nm: '新机开通', path: '/itsm/open' },
            { menu_cd: 'recycle', menu_nm: '回收任务', path: '/itsm/recycle' },
            { menu_cd: 'maint-plans', menu_nm: '保养计划', path: '/itsm/maintenance-plans' },
            { menu_cd: 'maint-t17', menu_nm: '保养工单', path: '/itsm/maintenance-t17' },
            { menu_cd: 'area-management', menu_nm: '区域人员管理', path: '/itsm/area-management' },
            { menu_cd: 'dispatch-rules', menu_nm: '派单规则', path: '/itsm/dispatch-rules' },
            { menu_cd: 'archives', menu_nm: '归档记录', path: '/itsm/archives' }
        ]
    },
    {
        menu_cd: 'sales', menu_nm: '销售管理',
        children: [
            { menu_cd: 'plans', menu_nm: '预计划管理', path: '/sales/plans' },
            { menu_cd: 'sales-serves', menu_nm: '呼出管理', path: '/sales/serves' },
            { menu_cd: 'sales-imple', menu_nm: '计划实施管理', path: '/sales/imple-plans' },
            { menu_cd: 'sales-bills', menu_nm: '销售单据', path: '/sales/bills' },
            { menu_cd: 'sales-extend', menu_nm: '延期管理', path: '/sales/extends' },
            { menu_cd: 'calls', menu_nm: '话务台', path: '/sales/calls' }
        ]
    },
    {
        menu_cd: 'qc', menu_nm: '质检管理',
        children: [
            { menu_cd: 'qc-results', menu_nm: '质检结果', path: '/qc/results' },
            { menu_cd: 'qc-input', menu_nm: '质检录入', path: '/qc/input' }
        ]
    },
    {
        menu_cd: 'transactions', menu_nm: '事务查询',
        children: [
            { menu_cd: 'all-transactions', menu_nm: '全模块查询', path: '/transactions/bills' },
            { menu_cd: 'transfer', menu_nm: '调拨流转', path: '/transactions/transfer' }
        ]
    },
    {
        menu_cd: 'portal', menu_nm: '客户门户',
        children: [
            { menu_cd: 'portal-users', menu_nm: '门户用户', path: '/portal/users' },
            { menu_cd: 'repairs', menu_nm: '自助报修', path: '/portal/repairs' },
            { menu_cd: 'ratings', menu_nm: '服务评价', path: '/portal/ratings' }
        ]
    },
    {
        menu_cd: 'sla', menu_nm: 'SLA管理',
        children: [
            { menu_cd: 'sla-defs', menu_nm: 'SLA定义', path: '/sla/definitions' },
            { menu_cd: 'sla-tickets', menu_nm: 'SLA监控', path: '/sla/tickets' }
        ]
    },
    {
        menu_cd: 'notification', menu_nm: '通知管理',
        children: [
            { menu_cd: 'notif-tpl', menu_nm: '通知模板', path: '/notification/templates' },
            { menu_cd: 'notif-list', menu_nm: '通知记录', path: '/notification/notifications' }
        ]
    },
    {
        menu_cd: 'contract', menu_nm: '合同管理',
        children: [
            { menu_cd: 'contracts', menu_nm: '合同管理', path: '/contract/contracts' },
            { menu_cd: 'invoices', menu_nm: '发票管理', path: '/contract/invoices' }
        ]
    },
    {
        menu_cd: 'billing', menu_nm: '结算管理',
        children: [
            { menu_cd: 'billing-rules', menu_nm: '结算规则', path: '/billing/rules' },
            { menu_cd: 'bills', menu_nm: '账单管理', path: '/billing/bills' }
        ]
    },
    {
        menu_cd: 'finance', menu_nm: '财务管理',
        children: [
            { menu_cd: 'accounts', menu_nm: '会计科目', path: '/finance/accounts' },
            { menu_cd: 'receivables', menu_nm: '应收管理', path: '/finance/receivables' },
            { menu_cd: 'payables', menu_nm: '应付管理', path: '/finance/payables' },
            { menu_cd: 'payments', menu_nm: '收付款管理', path: '/finance/payments' },
            { menu_cd: 'depreciation', menu_nm: '设备折旧', path: '/finance/depreciations' }
        ]
    },
    {
        menu_cd: 'deposit', menu_nm: '押金管理',
        children: [
            { menu_cd: 'deposits', menu_nm: '押金台账', path: '/deposit/deposits' },
            { menu_cd: 'deposit-details', menu_nm: '押金明细', path: '/deposit/details' },
            { menu_cd: 'deposit-io', menu_nm: '押金流水', path: '/deposit/io' }
        ]
    },
    {
        menu_cd: 'attendance', menu_nm: '考勤管理',
        children: [
            { menu_cd: 'attendance-list', menu_nm: '考勤记录', path: '/attendance/records' },
            { menu_cd: 'attendance-count', menu_nm: '考勤汇总', path: '/attendance/summary' }
        ]
    },
    {
        menu_cd: 'inventory', menu_nm: '库存管理',
        children: [
            { menu_cd: 'inv-limits', menu_nm: '库存预警', path: '/inventory/limits' },
            { menu_cd: 'prices', menu_nm: '价格管理', path: '/inventory/prices' },
            { menu_cd: 'adjust-prices', menu_nm: '调价记录', path: '/inventory/adjust-prices' }
        ]
    },
    {
        menu_cd: 'mes', menu_nm: '生产管理',
        children: [
            { menu_cd: 'work-orders', menu_nm: '生产工单', path: '/mes/work-orders' },
            { menu_cd: 'process-defs', menu_nm: '工序定义', path: '/mes/processes' },
            { menu_cd: 'work-processes', menu_nm: '工单工序', path: '/mes/work-processes' },
            { menu_cd: 'materials', menu_nm: '物料消耗', path: '/mes/materials' },
            { menu_cd: 'labels', menu_nm: '标签管理', path: '/mes/labels' }
        ]
    },
    {
        menu_cd: 'iot', menu_nm: 'IoT物联',
        children: [
            { menu_cd: 'device-conn', menu_nm: '设备接入', path: '/iot/connections' },
            { menu_cd: 'device-data', menu_nm: '设备数据', path: '/iot/data' },
            { menu_cd: 'alert-rules', menu_nm: '报警规则', path: '/iot/alert-rules' },
            { menu_cd: 'alert-logs', menu_nm: '报警记录', path: '/iot/alerts' }
        ]
    },
    {
        menu_cd: 'reports', menu_nm: '报表中心',
        children: [
            { menu_cd: 'reports-center', menu_nm: '报表中心', path: '/reports/center' }
        ]
    }
    // F3+ 模块将在后续阶段追加
]
