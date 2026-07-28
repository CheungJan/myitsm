import request from './request'

export interface SlaRecord { [key: string]: unknown }
export interface SlaPage { items: SlaRecord[]; total: number }

export function fetchSlaDefinitions(p?: Record<string, string>) {
    return request.get<never, { data: SlaRecord[] }>('/sla/definitions', { params: p }).then(r => {
        const arr = r?.data || []
        return { data: { items: arr, total: arr.length } as SlaPage }
    })
}
export function fetchSlaTickets(p?: Record<string, string>) {
    return request.get<never, { data: SlaRecord[] }>('/sla/tickets', { params: p }).then(r => {
        const arr = r?.data || []
        return { data: { items: arr, total: arr.length } as SlaPage }
    })
}
export function createSlaDefinition(data: Record<string, unknown>) {
    return request.post<never, { data: SlaRecord }>('/sla/definitions', data)
}
export function updateSlaDefinition(sla_id: string, data: Record<string, unknown>) {
    return request.put<never, { data: SlaRecord }>(`/sla/definitions/${sla_id}`, data)
}
