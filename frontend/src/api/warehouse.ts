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
