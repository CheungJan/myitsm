import request from './request'

export interface MesRecord { [key: string]: unknown }
export interface MesPage { items: MesRecord[]; total: number }

export function createWorkOrder(body: Record<string, unknown>) {
    return request.post<never, { data: MesRecord }>('/mes/work-orders', body)
}
export function fetchWorkOrders(p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>('/mes/work-orders', { params: p })
}
export function fetchProcessDefs(p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>('/mes/processes', { params: p })
}
export function createProcessDef(body: Record<string, unknown>) {
    return request.post<never, { data: MesRecord }>('/mes/processes', body)
}
export function updateProcessDef(cd: string, body: Record<string, unknown>) {
    return request.put<never, { data: MesRecord }>(`/mes/processes/${cd}`, body)
}
/** 全部工单工序列表 */
export function fetchAllWorkProcesses(p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>('/mes/work-processes', { params: p })
}
/** 按工单查询工序 */
export function fetchWorkProcesses(woId: string, p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>(`/mes/work-orders/${woId}/processes`, { params: p })
}
export function updateWorkProcess(id: number, body: Record<string, unknown>) {
    return request.put<never, { data: MesRecord }>(`/mes/work-processes/${id}`, body)
}
export function deleteWorkProcess(id: number) {
    return request.delete<never, unknown>(`/mes/work-processes/${id}`)
}
/** 全部物料消耗列表 */
export function fetchAllMaterialConsumes(p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>('/mes/materials', { params: p })
}
/** 按工单查询物料消耗 */
export function fetchMaterialConsumes(woId: string, p?: Record<string, string>) {
    return request.get<never, { data: MesPage }>(`/mes/work-orders/${woId}/materials`, { params: p })
}
/** 工单状态流转 */
export function deleteWorkOrder(woId: string) {
    return request.delete<never, unknown>(`/mes/work-orders/${woId}`)
}
export function transitionWorkOrder(woId: string, target: string) {
    return request.post<never, { data: unknown }>(`/mes/work-orders/${woId}/transition`, { target })
}
/** 工单物料更换 */
export function replaceWorkOrderAsset(woId: string, body: { old_eid?: string; new_eid?: string; itemcd: string; old_batch_no?: string; new_batch_no?: string; memo?: string }) {
    return request.post<never, { data: unknown }>(`/mes/work-orders/${woId}/replace`, body)
}
/** 查询工单物料更换历史 */
export function fetchReplaceRecords(woId: string) {
    return request.get<never, { data: Array<{ id?: number; wo_id: string; old_eid: string; new_eid: string; itemcd: string; old_batch_no: string; new_batch_no: string; memo: string; replace_date: string; operator_cd: string; operator_name: string }> }>(`/mes/work-orders/${woId}/replace-records`)
}
/** 查询工单 FQC 不良品关联的、且已审核的补料明细 */
export function fetchAvailableReplenish(woId: string) {
    return request.get<never, { data: { items: Array<{ outbillid: string; itemcd: string; eid: string | null; prddate: string | null; itemtyp: string; typ: 'eid' | 'batch' }>; audited_billids: string[]; pending_billids: string[] } }>(`/mes/work-orders/${woId}/replenish-available`)
}
