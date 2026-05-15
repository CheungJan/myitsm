import request from './request'

export interface PlanRecord {
    planno: string; plantyp: string; custcd: string; custnm: string
    custcard: string; plandate: string; plan_status: string
    opercd: string; gendate: string
    [key: string]: unknown
}

export interface PlanPage { items: PlanRecord[]; total: number }

export function fetchPlans(params?: Record<string, string>) {
    return request.get<never, { data: PlanPage }>('/sales/plans', { params })
}
export function fetchPlan(planno: string) {
    return request.get<never, { data: PlanRecord }>(`/sales/plans/${planno}`)
}
export function createPlan(data: Record<string, unknown>) {
    return request.post<never, { data: PlanRecord }>('/sales/plans', data)
}
export function updatePlan(planno: string, data: Record<string, unknown>) {
    return request.put<never, { data: PlanRecord }>(`/sales/plans/${planno}`, data)
}
