import request from './request'

export interface SlaRecord { [key: string]: unknown }
export interface SlaPage { items: SlaRecord[]; total: number }

export function fetchSlaDefinitions(p?: Record<string, string>) {
    return request.get<never, { data: SlaPage }>('/sla/definitions', { params: p })
}
export function fetchSlaTickets(p?: Record<string, string>) {
    return request.get<never, { data: SlaPage }>('/sla/tickets', { params: p })
}
