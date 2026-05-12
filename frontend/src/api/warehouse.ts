import request from './request'

export interface WarehouseRecord {
    wh_cd: string
    wh_nm: string
    address: string
    phone: string
    leader: string
    useflg: string
}

export function fetchWarehouses() {
    return request.get<never, { data: WarehouseRecord[] }>('/warehouse/warehouses')
}

export function createWarehouse(data: Record<string, unknown>) {
    return request.post<never, unknown>('/warehouse/warehouses', data)
}

export function updateWarehouse(whcd: string, data: Record<string, unknown>) {
    return request.put<never, unknown>(`/warehouse/warehouses/${whcd}`, data)
}

export function deleteWarehouse(whcd: string) {
    return request.delete<never, unknown>(`/warehouse/warehouses/${whcd}`)
}
