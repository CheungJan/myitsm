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
export function auditStockIn(id:string, whcd:string, checkmemo?:string, auditflg?:string) { return request.post<never,unknown>(`/warehouse/stock-in/${id}/audit`, { whcd, auditflg: auditflg || '2', ...(checkmemo ? {checkmemo} : {}) }) }
export function updateStockIn(id:string, body: Record<string,unknown>) { return request.put<never,{data:StockInRecord}>(`/warehouse/stock-in/${id}`, body) }
export function voidStockIn(id:string) { return request.post<never,unknown>(`/warehouse/stock-in/${id}/void`) }
export function unauditStockIn(id:string) { return request.post<never,unknown>(`/warehouse/stock-in/${id}/unaudit`) }

// ---- 可入库采购订单 ----
export interface ReceivableOrder { rgstbillid: string; rgstdate: string; suppliercd: string; supp_nm: string; total_lines: number; total_receivable: number }
export interface ReceivableOrderLine { lineno: number; itemcd: string; item_nm: string; rgsqty: number; received_qty: number; receivable_qty: number; units?: string }
export function fetchReceivableOrders() { return request.get<never,{data:ReceivableOrder[]}>('/warehouse/stock-in/receivable-orders') }
export function fetchReceivableOrderLines(rgstbillid: string) { return request.get<never,{data:ReceivableOrderLine[]}>(`/warehouse/stock-in/receivable-order-lines/${rgstbillid}`) }

// ---- 服务返还 (ITSM旧配件) ----
export interface ServiceReturnableOrder { maintenance_id: string; create_time: string; engineer_id: string; changetype?: string; items: { eid: string; itemcd: string; item_nm?: string; device_id: string; accessories_type: string }[] }
export function fetchServiceReturnable() { return request.get<never,{data:ServiceReturnableOrder[]}>('/warehouse/stock-in/service-returnable') }

// ---- 可调拨出库单 ----
export interface TransferableOrder { outbillid: string; source_whcd: string; target_whcd: string; total_out: number; total_in: number; pending: number }
export function fetchTransferableOrders() { return request.get<never,{data:TransferableOrder[]}>('/warehouse/stock-in/transferable-orders') }

// ---- Phase B 选择器 ----
export interface LendableOrder { outbillid: string; whcd: string; total_out: number; returned: number; pending: number }
export function fetchLendableOrders() { return request.get<never,{data:LendableOrder[]}>('/warehouse/stock-in/lendable-orders') }
export interface LendableOrderLine { lineno: number; itemcd: string; eid: string; out_qty: number; pending: number }
export function fetchLendableOrderLines(outbillid: string) { return request.get<never,{data:LendableOrderLine[]}>(`/warehouse/stock-in/lendable-order-lines/${outbillid}`) }
export interface RenovationReturnableOrder { outbillid: string; whcd: string; outdate: string; total_out: number; returned: number; pending: number }
export function fetchRenovationReturnableOrders() { return request.get<never,{data:RenovationReturnableOrder[]}>('/warehouse/stock-in/renovation-returnable') }
export interface RenovationReturnableLine { opt: string; lineno: number; itemcd: string; out_qty: number; pending: number; eid?: string; itemtyp?: string; prddate?: string }
export function fetchRenovationReturnableLines(outbillid: string) { return request.get<never,{data:RenovationReturnableLine[]}>(`/warehouse/stock-in/renovation-returnable-lines/${outbillid}`) }
export interface RepairReturnableOrder { outbillid: string; whcd: string; total_out: number; returned: number; pending: number }
export function fetchRepairReturnableOrders() { return request.get<never,{data:RepairReturnableOrder[]}>('/warehouse/stock-in/repair-returnable') }
export interface RepairReturnableLine { opt: string; lineno: number; itemcd: string; out_qty: number; pending: number; eid?: string; itemtyp?: string; prddate?: string }
export function fetchRepairReturnableLines(outbillid: string) { return request.get<never,{data:RepairReturnableLine[]}>(`/warehouse/stock-in/repair-returnable-lines/${outbillid}`) }
export interface ProductionReturnableOrder { outbillid: string; whcd: string; total_out: number; returned: number; pending: number }
export function fetchProductionReturnableOrders() { return request.get<never,{data:ProductionReturnableOrder[]}>('/warehouse/stock-in/production-returnable') }
export interface ProductionReturnableLine { opt: string; lineno: number; itemcd: string; out_qty: number; pending: number; eid?: string; itemtyp?: string; prddate?: string }
export function fetchProductionReturnableLines(outbillid: string) { return request.get<never,{data:ProductionReturnableLine[]}>(`/warehouse/stock-in/production-returnable-lines/${outbillid}`) }
export interface QcReturnableOrder { outbillid: string; whcd: string; outdate: string; total_out: number; returned: number; pending: number }
export function fetchQcReturnableOrders() { return request.get<never,{data:QcReturnableOrder[]}>('/warehouse/stock-in/qc-returnable') }
export interface QcReturnableLine { opt: string; lineno: number; itemcd: string; out_qty: number; pending: number; eid?: string; itemtyp?: string; prddate?: string }
export function fetchQcReturnableLines(outbillid: string) { return request.get<never,{data:QcReturnableLine[]}>(`/warehouse/stock-in/qc-returnable-lines/${outbillid}`) }
export interface QcPendingOrder { inbillid: string; whcd: string; indate: string; refbillid: string }
export function fetchQcPending() { return request.get<never,{data:QcPendingOrder[]}>('/warehouse/stock-out/qc-pending') }
export interface QcPendingLine { opt: string; lineno: number; itemcd: string; item_nm: string; qty: number; eid?: string; itemtyp?: string; prddate?: string; whcd: string }
export function fetchQcPendingLines(inbillid: string) { return request.get<never,{data:QcPendingLine[]}>(`/warehouse/stock-out/qc-pending-lines/${inbillid}`) }
export interface SalesReturnableOrder { outbillid: string; whcd: string; outdate: string; total_out: number; returned: number; pending: number }
export function fetchSalesReturnableOrders() { return request.get<never,{data:SalesReturnableOrder[]}>('/warehouse/stock-in/sales-returnable') }
export interface SalesReturnableLine { opt: string; lineno: number; itemcd: string; out_qty: number; pending: number; eid?: string; itemtyp?: string; prddate?: string }
export function fetchSalesReturnableLines(outbillid: string) { return request.get<never,{data:SalesReturnableLine[]}>(`/warehouse/stock-in/sales-returnable-lines/${outbillid}`) }

// ---- 出库单 ----
export interface StockOutRecord { outbillid: string; whcd: string; custcd?: string; gendate: string; opercd: string; invtyp?: string; details?: Record<string,unknown>[]; [key:string]: unknown }
export interface StockOutPage { items: StockOutRecord[]; total: number }
export function fetchStockOut(params?: Record<string,string>) { return request.get<never,{data:StockOutPage}>('/warehouse/stock-out',{params}) }
export function fetchStockOutDetail(id:string) { return request.get<never,{data:StockOutRecord}>(`/warehouse/stock-out/${id}`) }
export function fetchQcOutOrders() {
  return request.get<never, { data: StockOutRecord[] }>('/warehouse/stock-out/ov5-qc-pending')
}
export function createStockOut(body: Record<string,unknown>) { return request.post<never,{data:StockOutRecord}>('/warehouse/stock-out', body) }
export function auditStockOut(id:string, auditflg?:string, checkmemo?:string) { return request.post<never,unknown>(`/warehouse/stock-out/${id}/audit`, { auditflg: auditflg || '2', ...(checkmemo ? {checkmemo} : {}) }) }
export function updateStockOut(id:string, body: Record<string,unknown>) { return request.put<never,{data:StockOutRecord}>(`/warehouse/stock-out/${id}`, body) }
export function voidStockOut(id:string) { return request.post<never,unknown>(`/warehouse/stock-out/${id}/void`) }
export function unauditStockOut(id:string) { return request.post<never,unknown>(`/warehouse/stock-out/${id}/unaudit`) }
export function closeStockOutLines(id:string, lines: {lineno:number; type:string}[], reason:string) { return request.post<never,unknown>(`/warehouse/stock-out/${id}/close-lines`, { lines, reason }) }

// ---- 可退货出库 ----
export interface ReturnableOrder { pcbillid: string; ref_rgstbillid: string; suppliercd: string; supp_nm: string; total_lines: number; total_returnable: number }
export interface ReturnableOrderLine { lineno: number; itemcd: string; item_nm: string; rpcqty: number; eid?: string; seid?: string; returned_qty: number; returnable_qty: number }
export function fetchReturnableOrders() { return request.get<never,{data:ReturnableOrder[]}>('/warehouse/stock-out/returnable-orders') }
export function fetchReturnableOrderLines(pcbillid: string) { return request.get<never,{data:ReturnableOrderLine[]}>(`/warehouse/stock-out/returnable-order-lines/${pcbillid}`) }

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

// ---- 仓库报表 ----
export function fetchInventorySummary(params?: Record<string,string>) {
    return request.get<never,{data:{items:Record<string,unknown>[],total:number,period:string}}>('/warehouse/reports/inventory-summary',{params})
}
export function fetchDailySnapshot(params?: Record<string,string>) {
    return request.get<never,{data:{items:Record<string,unknown>[],total:number,date:string}}>('/warehouse/reports/daily-snapshot',{params})
}
export function fetchInventoryAging(params?: Record<string,string>) {
    return request.get<never,{data:{items:Record<string,unknown>[],total:number}}>('/warehouse/reports/aging',{params})
}
