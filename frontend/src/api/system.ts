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
export function createUser(data: Record<string, string>) {
    return request.post<never, { data: UserItem }>('/users', data)
}
export function updateUser(userCd: string, data: Record<string, string>) {
    return request.put<never, { data: UserItem }>(`/users/${userCd}`, data)
}
export function deleteUser(userCd: string) {
    return request.delete<never, unknown>(`/users/${userCd}`)
}
export function fetchDepartments() {
    return request.get<never, { data: DeptItem[] }>('/departments')
}
export function createDepartment(data: Record<string, string>) {
    return request.post<never, { data: DeptItem }>('/departments', data)
}
export function updateDepartment(deptCd: string, data: Record<string, string>) {
    return request.put<never, { data: DeptItem }>(`/departments/${deptCd}`, data)
}
export function deleteDepartment(deptCd: string) {
    return request.delete<never, unknown>(`/departments/${deptCd}`)
}
export function fetchGroups() {
    return request.get<never, { data: Record<string,unknown>[] }>('/groups')
}
export function createGroup(data: Record<string, string>) {
    return request.post<never, unknown>('/groups', data)
}
export function updateGroup(groupCd: string, data: Record<string, string>) {
    return request.put<never, unknown>(`/groups/${groupCd}`, data)
}
export function deleteGroup(groupCd: string) {
    return request.delete<never, unknown>(`/groups/${groupCd}`)
}
export function fetchGroupMembers(groupCd: string) {
    return request.get<never, { data: { user_cd: string; user_nm: string }[] }>(`/groups/${groupCd}/members`)
}
export function addGroupMember(groupCd: string, userCd: string) {
    return request.post<never, unknown>(`/groups/${groupCd}/members`, { user_cd: userCd })
}
export function removeGroupMember(groupCd: string, userCd: string) {
    return request.delete<never, unknown>(`/groups/${groupCd}/members/${userCd}`)
}
export function fetchSysparms() {
    return request.get<never, { data: Record<string,unknown>[] }>('/sysparms')
}
export function updateSysparm(parmCd: string, data: Record<string, unknown>) {
    return request.put<never, { data: Record<string, unknown> }>(`/sysparms/${parmCd}`, data)
}

// 权限管理
export interface PermRight {
    menu_cd: string
    func_cd: string
}
export function fetchGroupRights(groupCd: string) {
    return request.get<never, { data: PermRight[] }>(`/groups/${groupCd}/rights`)
}
export function setGroupRights(groupCd: string, rights: PermRight[]) {
    return request.put<never, unknown>(`/groups/${groupCd}/rights`, { rights })
}
export function fetchUserPermissions(userCd: string) {
    return request.get<never, { data: PermRight[] }>(`/users/${userCd}/permissions`)
}

// 系统字典
export function fetchAllSyscodes() {
    return request.get<never, { data: Record<string,unknown>[] }>('/syscodes/all')
}
export function createSyscode(data: Record<string,unknown>) {
    return request.post<never, unknown>('/syscodes', data)
}
export function updateSyscode(id: number, data: Record<string,unknown>) {
    return request.put<never, unknown>(`/syscodes/${id}`, data)
}
export function deleteSyscode(id: number) {
    return request.delete<never, unknown>(`/syscodes/${id}`)
}
export interface PermTreeNode {
    menu_cd: string
    menu_nm: string
    children: {
        menu_cd: string
        menu_nm: string
        funcs: { func_cd: string; func_nm: string }[]
    }[]
}
export function fetchPermTree() {
    return request.get<never, { data: PermTreeNode[] }>('/menus/perm-tree')
}
