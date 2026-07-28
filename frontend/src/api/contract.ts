import request from './request'

export interface ContractRecord { [key: string]: unknown }
export interface ContractPage { items: ContractRecord[]; total: number }

export function fetchContracts(p?: Record<string, string>) {
    return request.get<never, { data: ContractPage }>('/contract/contracts', { params: p })
}
export function fetchInvoices(p?: Record<string, string>) {
    return request.get<never, { data: ContractPage }>('/contract/invoices', { params: p })
}
