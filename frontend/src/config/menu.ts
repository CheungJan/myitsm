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
            { menu_cd: 'codes', menu_nm: '系统字典', path: '/system/codes' }
        ]
    },
    {
        menu_cd: 'master', menu_nm: '基础数据',
        children: [
            { menu_cd: 'items', menu_nm: '物料管理', path: '/master/items' },
            { menu_cd: 'bom', menu_nm: 'BOM管理', path: '/master/bom' },
            { menu_cd: 'customers', menu_nm: '客户管理', path: '/master/customers' },
            { menu_cd: 'eid', menu_nm: 'EID 管理', path: '/master/eid' },
            { menu_cd: 'assets', menu_nm: '资产台账', path: '/master/assets' },
            { menu_cd: 'warehouses', menu_nm: '仓库管理', path: '/master/warehouses' }
        ]
    },
    {
        menu_cd: 'warehouse', menu_nm: '仓储管理',
        children: [
            { menu_cd: 'stock-in', menu_nm: '入库单管理', path: '/warehouse/stock-in' },
            { menu_cd: 'stock-out', menu_nm: '出库单管理', path: '/warehouse/stock-out' },
            { menu_cd: 'stock', menu_nm: '库存查询', path: '/warehouse/stock-balance' },
            { menu_cd: 'asset-check', menu_nm: '资产盘点', path: '/warehouse/asset-check' },
            { menu_cd: 'pos-change', menu_nm: '设备回收确认', path: '/warehouse/pos-change' }
        ]
    },
    {
        menu_cd: 'procurement', menu_nm: '采购管理',
        children: [
            { menu_cd: 'proc-plans', menu_nm: '采购计划', path: '/procurement/plans' },
            { menu_cd: 'proc-registers', menu_nm: '采购登记', path: '/procurement/registers' },
            { menu_cd: 'proc-bills', menu_nm: '采购单据', path: '/procurement/bills' },
            { menu_cd: 'suppliers', menu_nm: '供应商管理', path: '/procurement/suppliers' },
            { menu_cd: 'appraisals', menu_nm: '供应商评价', path: '/procurement/appraisals' }
        ]
    },
    {
        menu_cd: 'itsm', menu_nm: 'ITSM工单',
        children: [
            { menu_cd: 'maintenance', menu_nm: '日常维修', path: '/itsm/maintenance' },
            { menu_cd: 'renovate', menu_nm: '旧机翻新', path: '/itsm/renovate' },
            { menu_cd: 'device-change', menu_nm: '设备变更', path: '/itsm/device-change' },
            { menu_cd: 'store-close', menu_nm: '门店关闭', path: '/itsm/store-close' },
            { menu_cd: 'itsm-open', menu_nm: '新机开通', path: '/itsm/open' },
            { menu_cd: 'recycle', menu_nm: '回收任务', path: '/itsm/recycle' }
        ]
    },
    {
        menu_cd: 'sales', menu_nm: '销售管理',
        children: [
            { menu_cd: 'plans', menu_nm: '预计划管理', path: '/sales/plans' },
            { menu_cd: 'sales-bills', menu_nm: '销售单据', path: '/sales/bills' },
            { menu_cd: 'sales-extend', menu_nm: '延期管理', path: '/sales/extends' },
            { menu_cd: 'calls', menu_nm: '话务台', path: '/sales/calls' }
        ]
    },
    {
        menu_cd: 'qc', menu_nm: '质检管理',
        children: [
            { menu_cd: 'qc-results', menu_nm: '质检结果', path: '/qc/results' }
        ]
    }
    // F2+ 模块将在后续阶段追加
]
