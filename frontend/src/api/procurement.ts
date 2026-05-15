import request from './request'
export interface ProcRecord { [key:string]: unknown }
export interface ProcPage { items: ProcRecord[]; total: number }
export function fetchProcPlans(p?:Record<string,string>){return request.get<never,{data:ProcPage}>('/procurement/plans',{params:p})}
export function fetchProcRegisters(p?:Record<string,string>){return request.get<never,{data:ProcPage}>('/procurement/registers',{params:p})}
export function fetchProcBills(p?:Record<string,string>){return request.get<never,{data:ProcPage}>('/procurement/bills',{params:p})}
