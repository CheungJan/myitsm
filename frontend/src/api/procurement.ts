import request from './request'
export interface ProcRecord { [key:string]: unknown }
export interface ProcPage { items: ProcRecord[]; total: number }
export function fetchProcPlans(p?:Record<string,string>){return request.get<never,{data:ProcPage}>('/procurement/plans',{params:p})}
export function fetchProcPlanDetail(pcplanid:string){return request.get<never,{data:ProcRecord}>('/procurement/plans/'+pcplanid)}
export function createProcPlan(body:Record<string,unknown>){return request.post<never,{data:ProcRecord}>('/procurement/plans',body)}
export function fetchProcRegisters(p?:Record<string,string>){return request.get<never,{data:ProcPage}>('/procurement/registers',{params:p})}
export function fetchProcBills(p?:Record<string,string>){return request.get<never,{data:ProcPage}>('/procurement/bills',{params:p})}
export interface ReturnPurchaseRecord { pcbillid: string; custcd?: string; whcd?: string; pcamt?: number; invoiceflg?: string; memo?: string; gendate?: string; opercd?: string; details?: Record<string,unknown>[]; [key:string]: unknown }
export interface ReturnPurchasePage { items: ReturnPurchaseRecord[]; total: number }
export function fetchReturnPurchase(p?:Record<string,string>){return request.get<never,{data:ReturnPurchasePage}>('/procurement/returns',{params:p})}
