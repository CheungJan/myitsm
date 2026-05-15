import request from './request'

export interface MesRecord { [key: string]: unknown }
export interface MesPage { items: MesRecord[]; total: number }

export function fetchWorkOrders(p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>('/mes/work-orders', { params: p })
}
export function fetchProcessDefs(p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>('/mes/processes', { params: p })
}
export function fetchWorkProcesses(woId: string, p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>(`/mes/work-orders/${woId}/processes`, { params: p })
}
export function fetchMaterialConsumes(woId: string, p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>(`/mes/work-orders/${woId}/materials`, { params: p })
}
