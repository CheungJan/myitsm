import request from './request'

export interface FinanceRecord { [key: string]: unknown }
export interface FinancePage { items: FinanceRecord[]; total: number }

export function fetchAccounts(p?: Record<string, string>) {
    return request.get<never, { data: FinancePage }>('/finance/accounts', { params: p })
}
export function fetchReceivables(p?: Record<string, string>) {
    return request.get<never, { data: FinancePage }>('/finance/receivables', { params: p })
}
export function fetchPayables(p?: Record<string, string>) {
    return request.get<never, { data: FinancePage }>('/finance/payables', { params: p })
}
export function fetchPayments(p?: Record<string, string>) {
    return request.get<never, { data: FinancePage }>('/finance/payments', { params: p })
}
export function fetchDepreciations(p?: Record<string, string>) {
    return request.get<never, { data: FinancePage }>('/finance/depreciations', { params: p })
}
