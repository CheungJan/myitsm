import request from './request'

export interface WarehouseRecord {
    whcd: string
    whnm: string
    address: string
    phone: string
    leader: string
    useflg: string
}

export function fetchWarehouses() {
    return request.get<never, { data: WarehouseRecord[] }>('/warehouses')
}

export function createWarehouse(data: Record<string, unknown>) {
    return request.post<never, unknown>('/warehouses', data)
}

export function updateWarehouse(whcd: string, data: Record<string, unknown>) {
    return request.put<never, unknown>(`/warehouses/${whcd}`, data)
}

export function deleteWarehouse(whcd: string) {
    return request.delete<never, unknown>(`/warehouses/${whcd}`)
}

// ---- 入库单 ----
export interface StockInRecord { inbillid: string; whcd: string; whnm?: string; suppcd?: string; gendate: string; opercd: string; invtyp?: string; details?: Record<string,unknown>[]; [key:string]: unknown }
export interface StockInPage { items: StockInRecord[]; total: number }
export function fetchStockIn(params?: Record<string,string>) { return request.get<never,{data:StockInPage}>('/warehouse/stock-in',{params}) }
export function fetchStockInDetail(id:string) { return request.get<never,{data:StockInRecord}>(`/warehouse/stock-in/${id}`) }
export function createStockIn(body: Record<string,unknown>) { return request.post<never,{data:StockInRecord}>('/warehouse/stock-in', body) }
export function auditStockIn(id:string, whcd:string, checkmemo?:string) { return request.post<never,unknown>(`/warehouse/stock-in/${id}/audit`, { whcd, ...(checkmemo ? {checkmemo} : {}) }) }

// ---- 出库单 ----
export interface StockOutRecord { outbillid: string; whcd: string; custcd?: string; gendate: string; opercd: string; invtyp?: string; details?: Record<string,unknown>[]; [key:string]: unknown }
export interface StockOutPage { items: StockOutRecord[]; total: number }
export function fetchStockOut(params?: Record<string,string>) { return request.get<never,{data:StockOutPage}>('/warehouse/stock-out',{params}) }
export function fetchStockOutDetail(id:string) { return request.get<never,{data:StockOutRecord}>(`/warehouse/stock-out/${id}`) }
export function auditStockOut(id:string, auditflg?:string, checkmemo?:string) { return request.post<never,unknown>(`/warehouse/stock-out/${id}/audit`, { auditflg: auditflg || '2', ...(checkmemo ? {checkmemo} : {}) }) }

// ---- 库存 ----
export interface StockItem { itemcd: string; item_nm: string; whcd: string; storeqty: number; upperlimit?: number; lowerlimit?: number; [key:string]: unknown }
export interface StockPage { items: StockItem[]; total: number }
export function fetchStock(params?: Record<string,string>) { return request.get<never,{data:StockPage}>('/warehouse/stock',{params}) }

// ---- 库存流水 ----
export interface StockMovement { seqno: number; whcd: string; whnm?: string; itemcd: string; item_nm?: string; gendate: string; billid: string; itemqty: number; iotyp: string; invtyp: string; storeqty: number; [key:string]: unknown }
export interface StockMovementPage { items: StockMovement[]; total: number }
export function fetchStockMovements(params?: Record<string,string>) { return request.get<never,{data:StockMovementPage}>('/warehouse/stock-movement',{params}) }

// ---- 盘盈盘亏 ----
export interface OverLostRecord { olbillid: string; whcd: string; whnm?: string; oltyp?: string; olsign?: string; olreason?: string; memo?: string; auditflg?: string; gendate?: string; opercd?: string; details?: Record<string,unknown>[]; details_eid?: Record<string,unknown>[]; [key:string]: unknown }
export interface OverLostPage { items: OverLostRecord[]; total: number }
export function fetchOverLost(params?: Record<string,string>) { return request.get<never,{data:OverLostPage}>('/warehouse/overlost',{params}) }
export function fetchOverLostDetail(id:string) { return request.get<never,{data:OverLostRecord}>(`/warehouse/overlost/${id}`) }
export function createOverLost(data:Record<string,unknown>) { return request.post<never,unknown>('/warehouse/overlost',data) }
export function auditOverLost(id:string) { return request.post<never,unknown>(`/warehouse/overlost/${id}/audit`) }
