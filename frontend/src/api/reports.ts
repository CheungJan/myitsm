import request from './request'

// 通用记录类型
export interface ReportRecord { [key: string]: unknown }

// D2 故障分析报表查询参数
export interface FaultAnalysisParams {
    start_date?: string
    end_date?: string
    bill_type?: string  // MD/MO/MR/BG/BY
    fault_type_cd?: string
}

// 型号故障率
export interface ModelFaultRateRow {
    itemcd: string
    item_nm: string
    fault_count: number
    distinct_device: number
}

// 配件更换频次
export interface AccessoryFrequencyRow {
    itemcd: string
    item_nm: string
    replace_count: number
    distinct_maintenance: number
}

// 修复时长
export interface RepairDurationRow {
    bill_type: string
    avg_minutes: number
    median_minutes: number
    max_minutes: number
    count: number
}

// D2 故障分析：型号故障率
export function fetchModelFaultRate(params: FaultAnalysisParams = {}) {
    return request.get<never, { data: ModelFaultRateRow[] }>('/reports/fault/model-rate', { params })
}

// D2 故障分析：配件更换频次
export function fetchAccessoryFrequency(params: FaultAnalysisParams = {}) {
    return request.get<never, { data: AccessoryFrequencyRow[] }>('/reports/fault/accessory-frequency', { params })
}

// D2 故障分析：修复时长
export function fetchRepairDuration(params: FaultAnalysisParams = {}) {
    return request.get<never, { data: RepairDurationRow[] }>('/reports/fault/repair-duration', { params })
}
