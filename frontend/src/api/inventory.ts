import request from './request'

// 可用标签
export interface AvailableLabel { labelid: string; classcd: string }
export function fetchAvailableLabels(classcd: string, qty: number = 20) {
    return request.get<never, { data: AvailableLabel[] }>('/inventory/labels/available', { params: { classcd, qty } })
}

// 生成标签
export interface GenerateLabelsParams { classcd: string; typflg: string; count: number; date?: string; sign?: string }
export interface GenerateLabelsResult { prefix: string; start_seq: number; inserted: number; count: number }
export function generateLabels(body: GenerateLabelsParams) {
    return request.post<never, { data: GenerateLabelsResult }>('/inventory/labels/generate', body)
}
