import request from './request'

export interface MesRecord { [key: string]: unknown }
export interface MesPage { items: MesRecord[]; total: number }

export function fetchWorkOrders(p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>('/mes/work-orders', { params: p })
}
export function fetchProcessDefs(p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>('/mes/processes', { params: p })
}
/** 全部工单工序列表 */
export function fetchAllWorkProcesses(p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>('/mes/work-processes', { params: p })
}
/** 按工单查询工序 */
export function fetchWorkProcesses(woId: string, p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>(`/mes/work-orders/${woId}/processes`, { params: p })
}
/** 全部物料消耗列表 */
export function fetchAllMaterialConsumes(p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>('/mes/materials', { params: p })
}
/** 按工单查询物料消耗 */
export function fetchMaterialConsumes(woId: string, p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>(`/mes/work-orders/${woId}/materials`, { params: p })
}
