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

export function fetchSettlements(p?:Record<string,string>){
    return request.get<never,{data:ProcPage}>('/procurement/settlements',{params:p})
}
export function fetchSettlementDetail(pcbillid:string){
    return request.get<never,{data:ProcRecord}>('/procurement/settlements/'+pcbillid)
}
export function createSettlement(body:Record<string,unknown>){
    return request.post<never,{data:ProcRecord}>('/procurement/settlements',body)
}

// ---- 采购退货 ----

export interface ReturnPurchaseRecord {
    pcbillid: string; custcd: string; whcd: string; pcamt: number;
    invoiceflg: string; memo: string; gendate: string; opercd: string;
    ref_rgstbillid?: string;
    details?: ReturnPurchaseDetail[];
    [key:string]: unknown
}
export interface ReturnPurchaseDetail {
    itemcd: string; rpcqty: number; eid: string; units: string;
    ref_rgstlineno?: number;
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
