import request from './request'

export function fetchItems(params?: Record<string, string>) {
    return request.get('/items', { params })
}
export function createItem(data: Record<string, unknown>) {
    return request.post('/items', data)
}
export function updateItem(itemCd: string, data: Record<string, unknown>) {
    return request.put(`/items/${itemCd}`, data)
}
export function deleteItem(itemCd: string) {
    return request.delete(`/items/${itemCd}`)
}

export function fetchCustomers(params?: Record<string, string>) {
    return request.get('/customers', { params })
}
export function createCustomer(data: Record<string, unknown>) {
    return request.post('/customers', data)
}
export function updateCustomer(custCd: string, data: Record<string, unknown>) {
    return request.put(`/customers/${custCd}`, data)
}
export function deleteCustomer(custCd: string) {
    return request.delete(`/customers/${custCd}`)
}

export function fetchEidList(params?: Record<string, string>) {
    return request.get('/eid', { params })
}
export function createEid(data: Record<string, unknown>) {
    return request.post('/eid', data)
}
export function updateEid(eidVal: string, data: Record<string, unknown>) {
    return request.put(`/eid/${eidVal}`, data)
}
export function deleteEid(eidVal: string) {
    return request.delete(`/eid/${eidVal}`)
}

export function fetchAssets(params?: Record<string, string>) {
    return request.get('/assets', { params })
}
