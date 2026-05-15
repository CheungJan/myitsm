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
            { menu_cd: 'stock-out', menu_nm: '出库单管理', path: '/warehouse/stock-out' }
        ]
    },
    {
        menu_cd: 'procurement', menu_nm: '采购管理',
        children: [
            { menu_cd: 'proc-plans', menu_nm: '采购计划', path: '/procurement/plans' },
            { menu_cd: 'proc-registers', menu_nm: '采购登记', path: '/procurement/registers' }
        ]
    },
    {
        menu_cd: 'itsm', menu_nm: 'ITSM工单',
        children: [
            { menu_cd: 'maintenance', menu_nm: '日常维修', path: '/itsm/maintenance' }
        ]
    },
    {
        menu_cd: 'sales', menu_nm: '销售管理',
        children: [
            { menu_cd: 'plans', menu_nm: '预计划管理', path: '/sales/plans' }
        ]
    }
    // F2+ 模块将在后续阶段追加
]
