import request from './request'

export interface ItemRecord {
    item_cd: string; item_nm: string; class_cd: string; spec: string
    unit: string; useflg: string; created_at: string
}
export interface CustomerRecord {
    cust_cd: string; cust_nm: string; class_cd: string; phone_no: string
    contactor: string; address: string; useflg: string; created_at: string
}
export interface EidRecord {
    item_cd: string; eid: string; etyp: string; whcd: string
    sflg: string; useflg: string; gendate: string
}

export function fetchItems(params?: Record<string, string>) {
    return request.get('/warehouse/stock', { params })
}
export function fetchCustomers(params?: Record<string, string>) {
    return request.get('/users', { params })
}
export function fetchEidList(params?: Record<string, string>) {
    return request.get('/reports/eid-lifecycle', { params })
}
