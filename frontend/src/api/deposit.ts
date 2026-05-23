import request from './request'

export interface DepositRecord { [key: string]: unknown }
export interface DepositPage { items: DepositRecord[]; total: number }

export function fetchDeposits(p?: Record<string, string>) {
    return request.get<never, { data: DepositPage }>('/deposit/deposits', { params: p })
}
/** 全部押金明细列表（不限客户） */
export function fetchAllDepositDetails(p?: Record<string, string>) {
    return request.get<never, { data: DepositPage }>('/deposit/deposits/details', { params: p })
}
/** 按客户查询押金明细 */
export function fetchDepositDetails(custcd: string, p?: Record<string, string>) {
    return request.get<never, { data: DepositPage }>(`/deposit/deposits/${custcd}/details`, { params: p })
}
export function fetchDepositIO(p?: Record<string, string>) {
    return request.get<never, { data: DepositPage }>('/deposit/deposits/io', { params: p })
}
