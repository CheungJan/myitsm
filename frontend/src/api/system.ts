import request from './request'

export interface MenuItem {
    menu_cd: string
    menu_nm: string
    exe_path: string
    parent_cd: string | null
    children?: MenuItem[]
}

export function fetchMenus() {
    return request.get<never, { data: MenuItem[] }>('/menus')
}
