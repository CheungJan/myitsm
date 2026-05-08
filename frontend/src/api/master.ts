import request from './request'

export function fetchItems(params?: Record<string, string>) {
    return request.get('/items', { params })
}
export function fetchCustomers(params?: Record<string, string>) {
    return request.get('/customers', { params })
}
export function fetchEidList(params?: Record<string, string>) {
    return request.get('/eid', { params })
}
export function fetchAssets(params?: Record<string, string>) {
    return request.get('/assets', { params })
}
