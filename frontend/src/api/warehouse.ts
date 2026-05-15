import request from './request'

export interface WarehouseRecord {
    wh_cd: string
    wh_nm: string
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

// ---- 出库单 ----
export interface StockOutRecord { outbillid: string; whcd: string; custcd?: string; gendate: string; opercd: string; invtyp?: string; details?: Record<string,unknown>[]; [key:string]: unknown }
export interface StockOutPage { items: StockOutRecord[]; total: number }
export function fetchStockOut(params?: Record<string,string>) { return request.get<never,{data:StockOutPage}>('/warehouse/stock-out',{params}) }

// ---- 库存 ----
export interface StockItem { itemcd: string; item_nm: string; whcd: string; storeqty: number; upperlimit?: number; lowerlimit?: number; [key:string]: unknown }
export interface StockPage { items: StockItem[]; total: number }
export function fetchStock(params?: Record<string,string>) { return request.get<never,{data:StockPage}>('/warehouse/stock',{params}) }
