import request from './request'

export interface MenuItem {
    menu_cd: string
    menu_nm: string
    exe_path: string
    parent_cd: string | null
    children?: MenuItem[]
}

export interface UserItem {
    user_cd: string
    user_nm: string
    dept_cd: string
    useflg: string
    phone: string
    email: string
    created_at: string
}

export interface DeptItem {
    dept_cd: string
    dept_nm: string
    parent_cd: string
    childflg: string
}

export function fetchMenus() {
    return request.get<never, { data: MenuItem[] }>('/menus')
}
export function fetchUsers(params?: Record<string, string>) {
    return request.get<never, { data: UserItem[]; total: number }>('/users', { params })
}
export function fetchUser(userCd: string) {
    return request.get<never, { data: UserItem }>(`/users/${userCd}`)
}
export function fetchDepartments() {
    return request.get<never, { data: DeptItem[] }>('/departments')
}
export function fetchGroups() {
    return request.get<never, { data: Record<string,unknown>[] }>('/groups')
}
export function fetchSysparms() {
    return request.get<never, { data: Record<string,unknown>[] }>('/sysparms')
}
