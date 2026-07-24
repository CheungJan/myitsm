import request from './request'

// 通用记录类型（库存预警/价格/调价复用）
export interface InvRecord { [key: string]: unknown }

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

// ---- 库存预警 ----
export function fetchInventoryLimits(p?: Record<string, string>) {
    return request.get<never, { data: { items: InvRecord[]; total: number } }>('/inventory/inventory-limits', { params: p })
}

// ---- 价格规则 ----
export function fetchPrices(p?: Record<string, string>) {
    return request.get<never, { data: { items: InvRecord[]; total: number } }>('/inventory/prices', { params: p })
}

// ---- 调价记录 ----
export function fetchAdjustPrices(pabillidOrParams: string | Record<string, string> = '', extra?: Record<string, string>) {
    const params: Record<string, string> = {}
    if (typeof pabillidOrParams === 'string' && pabillidOrParams) params.pabillid = pabillidOrParams
    else if (typeof pabillidOrParams === 'object') Object.assign(params, pabillidOrParams)
    if (extra) Object.assign(params, extra)
    return request.get<never, { data: { items: InvRecord[]; total: number } }>('/inventory/adjust-prices', { params })
}
