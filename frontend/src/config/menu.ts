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
    }
    // F2+ 模块将在后续阶段追加
]
