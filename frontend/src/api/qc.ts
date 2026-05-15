import request from './request'
export interface QcRecord { qcbillid: string; itemcd: string; eid?: string; qcstatus?: string; gendate: string; refbillid?: string; [key:string]: unknown }
export interface QcPage { items: QcRecord[]; total: number }
export function fetchQcResults(p?:Record<string,string>){return request.get<never,{data:QcPage}>('/qc',{params:p})}
export function fetchQcDetail(id:string){return request.get<never,{data:QcRecord}>(`/qc/${id}`)}
