import request from './request'

export interface InvRecord { [key: string]: unknown }
export interface InvPage { items: InvRecord[]; total: number }

export function fetchInventoryLimits(p?: Record<string, string>) {
    return request.get<never, { data: InvPage }>('/inventory/inventory-limits', { params: p })
}
export function fetchPrices(p?: Record<string, string>) {
    return request.get<never, { data: InvPage }>('/inventory/prices', { params: p })
}
export function fetchAdjustPrices(pabillid: string, p?: Record<string, string>) {
    return request.get<never, { data: InvPage }>(`/inventory/adjust-prices/${pabillid}`, { params: p })
}
