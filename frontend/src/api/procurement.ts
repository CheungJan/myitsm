import request from './request'

export interface ProcRecord { [key:string]: unknown }
export interface ProcPage { items: ProcRecord[]; total: number }

// ---- 采购需求 ----

export function fetchRequisitions(p?:Record<string,string>){
    return request.get<never,{data:ProcPage}>('/procurement/requisitions',{params:p})
}
export function fetchRequisitionDetail(pcplanid:string){
    return request.get<never,{data:ProcRecord}>('/procurement/requisitions/'+pcplanid)
}
export function createRequisition(body:Record<string,unknown>){
    return request.post<never,{data:ProcRecord}>('/procurement/requisitions',body)
}

// ---- 采购订单 ----

export function fetchOrders(p?:Record<string,string>){
    return request.get<never,{data:ProcPage}>('/procurement/orders',{params:p})
}
export function fetchOrderDetail(rgstbillid:string){
    return request.get<never,{data:ProcRecord}>('/procurement/orders/'+rgstbillid)
}
export function createOrder(body:Record<string,unknown>){
    return request.post<never,{data:ProcRecord}>('/procurement/orders',body)
}
export function fetchAvailableItems(p?:Record<string,string>){
    return request.get<never,{data:ProcRecord[]}>('/procurement/available-items',{params:p})
}

// ---- 采购结算单 ----

export interface SettlementRecord {
    pcbillid: string; suppliercd: string; pay_type: string;
    invoice_no?: string; invoice_date?: string; pcdate?: string;
    total_settle_amt: number; whcd: string; invoiceflg: string;
    auditflg: string; auditman?: string; auditdate?: string;
    memo?: string; gendate: string; opercd: string;
    details?: SettlementDetail[];
    [key:string]: unknown
}
export interface SettlementDetail {
    lineno: number; ref_rgstbillid: string; ref_rgstlineno: number;
    itemcd: string; order_qty: number; received_qty: number;
    already_settled: number; settle_qty: number;
    settle_price: number; settle_amt: number;
    [key:string]: unknown
}
export interface SettlementPage { items: SettlementRecord[]; total: number }

export function fetchSettlements(p?:Record<string,string>){
    return request.get<never,{data:SettlementPage}>('/procurement/settlements',{params:p})
}
export function fetchSettlementDetail(pcbillid:string){
    return request.get<never,{data:SettlementRecord}>('/procurement/settlements/'+pcbillid)
}
export function createSettlement(body:Record<string,unknown>){
    return request.post<never,{data:SettlementRecord}>('/procurement/settlements',body)
}
export function updateSettlement(pcbillid:string, body:Record<string,unknown>){
    return request.put<never,{data:{success:boolean}}>('/procurement/settlements/'+pcbillid, body)
}
export function auditSettlement(pcbillid:string, auditflg:string='2'){
    return request.post<never,{data:{success:boolean}}>('/procurement/settlements/'+pcbillid+'/audit',{auditflg})
}
export function voidSettlement(pcbillid:string){
    return request.post<never,{data:{success:boolean}}>('/procurement/settlements/'+pcbillid+'/void')
}
export function fetchSettlementPayable(pcbillid:string){
    return request.get<never,{data:PayableRecord | null}>('/procurement/settlements/'+pcbillid+'/payable')
}
export interface PayableRecord {
    ap_id: string; supp_cd: string; po_id: string; ap_date: string;
    due_date: string; amount: number; paid_amount: number; balance: number;
    status: string; remark: string;
    [key:string]: unknown
}
export function fetchSettleableItems(rgstbillid:string){
    return request.get<never,{data:ProcRecord[]}>('/procurement/orders/'+rgstbillid+'/settleable-items')
}

/** 查询某供应商某月的入库订单汇总（月结用） */
export function fetchMonthlyReceiving(suppliercd:string,period:string){
    return request.get<never,{data:{rgstbillid:string;whcd:string;indate:string}[]}>('/procurement/orders/monthly-receiving',{params:{suppliercd,period}})
}

// ---- 采购退货 ----

export interface ReturnPurchaseRecord {
    pcbillid: string; suppliercd: string; whcd: string; pcamt: number;
    invoiceflg: string; memo: string; gendate: string; opercd: string;
    ref_rgstbillid?: string; return_reason?: string;
    auditflg?: string; auditman?: string; auditdate?: string;
    details?: ReturnPurchaseDetail[];
    [key:string]: unknown
}
export interface ReturnPurchaseDetail {
    itemcd: string; rpcqty: number; eid: string; units: string;
    ref_rgstlineno?: number; return_price?: number; return_amt?: number;
    line_reason?: string;
    [key:string]: unknown
}
export interface ReturnPurchasePage { items: ReturnPurchaseRecord[]; total: number }

export function fetchReturns(p?:Record<string,string>){
    return request.get<never,{data:ReturnPurchasePage}>('/procurement/returns',{params:p})
}
export function fetchReturnDetail(pcbillid:string){
    return request.get<never,{data:ReturnPurchaseRecord}>('/procurement/returns/'+pcbillid)
}
export function createReturn(body:Record<string,unknown>){
    return request.post<never,{data:ReturnPurchaseRecord}>('/procurement/returns',body)
}
export function updateReturn(pcbillid:string, body:Record<string,unknown>){
    return request.put<never,{data:{success:boolean}}>('/procurement/returns/'+pcbillid, body)
}
export function auditReturn(pcbillid:string, auditflg:string='2'){
    return request.post<never,{data:{success:boolean}}>('/procurement/returns/'+pcbillid+'/audit',{auditflg})
}
export function voidReturn(pcbillid:string){
    return request.post<never,{data:{success:boolean}}>('/procurement/returns/'+pcbillid+'/void')
}
export function fetchReturnableOrders(){
    return request.get<never,{data:{rgstbillid:string;suppliercd:string}[]}>('/procurement/orders/returnable')
}
export function fetchReturnableItems(rgstbillid:string){
    return request.get<never,{data:ProcRecord[]}>('/procurement/orders/'+rgstbillid+'/returnable-items')
}
