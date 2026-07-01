import request from './request'

// ---- 预计划 ----
export interface PlanRecord {
    planno: string; plantyp: string; custcd: string; custnm: string
    custcard: string; custrnm?: string; plandate: string; plan_status: string
    opercd: string; gendate: string
    customer_status?: string
    is_rent?: string; deposit?: number; yun_type?: string
    pos_item?: string; is_contract?: string; is_outflag?: string
    imple_status?: string; imple_billid?: string; serve_status?: string
    address?: string; contactor?: string; phoneno?: string; busityp?: string
    [key: string]: unknown
}

export interface PlanPage { items: PlanRecord[]; total: number }
export interface PlanResult { success?: boolean; data?: any; downstream_id?: string; outbillid?: string; [key: string]: unknown }

export function fetchPlans(params?: Record<string, string>) {
    return request.get<never, { data: PlanPage }>('/sales/plans', { params })
}
export function fetchPlan(planno: string) {
    return request.get<never, { data: PlanRecord }>(`/sales/plans/${planno}`)
}
export function createPlan(data: Record<string, unknown>) {
    return request.post<never, { data: PlanResult }>('/sales/plans', data)
}
export function updatePlan(planno: string, data: Record<string, unknown>) {
    return request.put<never, { data: PlanResult }>(`/sales/plans/${planno}`, data)
}

// 预计划状态操作
export function transitionPlan(planno: string, to_status: string, remark?: string) {
    return request.post<never, { data: PlanResult }>(`/sales/plans/${planno}/transition`, { to_status, remark })
}
export function implementPlan(planno: string) {
    return request.post<never, { data: PlanResult }>(`/sales/plans/${planno}/implement`)
}
export function completePlan(planno: string) {
    return request.post<never, { data: PlanResult }>(`/sales/plans/${planno}/complete`)
}
export function voidPlan(planno: string, remark?: string) {
    return request.post<never, { data: PlanResult }>(`/sales/plans/${planno}/void`, { remark })
}
export function createOutbound(planno: string, whcd?: string, eids?: string[]) {
    return request.post<never, { data: PlanResult }>(`/sales/plans/${planno}/outbound`, { whcd, eids })
}

// 预计划机型可用设备列表（方案 A 预绑定 EID 选择）
export interface AvailableEid {
    eid: string; itemcd: string; whcd: string; whnm: string
    asset_type: string; asset_type_nm: string
    itemtyp: string; itemtyp_nm: string
    sflg: string; qcflg: string
}
export function fetchAvailableEids(params: { model_cd: string; whtyp?: string; asset_types?: string; itemtyp?: string; page?: number; per_page?: number }) {
    return request.get<never, { data: { total: number; items: AvailableEid[] } }>('/sales/plans/available-eids', { params })
}

// ---- 呼出单 ----
export interface ServeRecord {
    dtlid: number; planno: string; plantyp?: string; servetyp?: string
    serve_task?: string; serve_back?: string; serve_mark?: string
    commmode?: string; status: string; gendate?: string; genercd?: string
    [key: string]: unknown
}

export function fetchPlanServes(planno: string) {
    return request.get<never, { data: ServeRecord[] }>(`/sales/plans/${planno}/serve`)
}
export function createPlanServe(planno: string, data: Record<string, unknown>) {
    return request.post<never, { data: ServeRecord }>(`/sales/plans/${planno}/serve`, data)
}
export function updatePlanServe(dtlid: number, data: Record<string, unknown>) {
    return request.put<never, { data: ServeRecord }>(`/sales/plan-serve/${dtlid}`, data)
}
export function transitionPlanServe(dtlid: number, to_status: string) {
    return request.post<never, { data: PlanResult }>(`/sales/plan-serve/${dtlid}/transition`, { to_status })
}

// ---- 销售单据（已有，保留）----
export function fetchSalesBills(p?: Record<string, string>) {
    return request.get<never, { data: PlanPage }>('/sales/bills', { params: p })
}
