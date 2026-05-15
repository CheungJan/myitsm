import request from './request'

export interface DepositRecord { [key: string]: unknown }
export interface DepositPage { items: DepositRecord[]; total: number }

export function fetchDeposits(p?: Record<string, string>) {
    return request.get<never, { data: DepositPage }>('/deposit/deposits', { params: p })
}
export function fetchDepositDetails(custcd: string, p?: Record<string, string>) {
    return request.get<never, { data: DepositPage }>(`/deposit/deposits/${custcd}/details`, { params: p })
}
export function fetchDepositIO(p?: Record<string, string>) {
    return request.get<never, { data: DepositPage }>('/deposit/deposits/io', { params: p })
}
