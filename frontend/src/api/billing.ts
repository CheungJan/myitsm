import request from './request'

export interface BillingRecord { [key: string]: unknown }
export interface BillingPage { items: BillingRecord[]; total: number }

export function fetchBillingRules(p?: Record<string, string>) {
    return request.get<never, { data: BillingPage }>('/billing/rules', { params: p })
}
export function fetchBills(p?: Record<string, string>) {
    return request.get<never, { data: BillingPage }>('/billing/bills', { params: p })
}
