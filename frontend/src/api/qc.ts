import request from './request'
export interface QcRecord { qcbillid: string; itemcd: string; eid?: string; qcstatus?: string; gendate: string; refbillid?: string; [key:string]: unknown }
export interface QcPage { items: QcRecord[]; total: number }
export function fetchQcResults(p?:Record<string,string>){return request.get<never,{data:QcPage}>('/qc',{params:p})}
export function fetchQcDetail(id:string){return request.get<never,{data:QcRecord}>(`/qc/${id}`)}
export function fetchQcStats(){return request.get<never,{data:{qcstatus:string;cnt:number}[]}>('/qc/stats')}
export function fetchQcCompletion(){return request.get<never,{data:{total_ov5:number;done_ov5:number;pending_ov5:number;iv11_count:number;ov_out_count:number}}>('/qc/ov5-completion')}
export function createQcResult(body:Record<string,unknown>){return request.post<never,{data:QcRecord}>('/qc',body)}
export function auditQcResult(id:string, auditflg?:string, checkmemo?:string){return request.post<never,{data:unknown}>(`/qc/${id}/audit`,{auditflg:auditflg||'1',checkmemo})}
export function voidQcResult(id:string){return request.post<never,{data:unknown}>(`/qc/${id}/void`)}
export function unauditQcResult(id:string){return request.post<never,{data:unknown}>(`/qc/${id}/unaudit`)}

// 批次
export interface QcBatchItem {
  batch_id: string; refbillid: string; gendate: string; opercd: string
  auditflg: string; total_count: number
  ga_count: number; gb_count: number; gc_count: number; bf_count: number; bh_count: number; th_count: number
}
export interface QcBatchDetail { success: boolean; batch_id: string; records: QcRecord[] }
export function listQcBatches(p?: Record<string, string>) { return request.get<never, {data: {items: QcBatchItem[]; total: number}}>('/qc/batches', {params: p}) }
export function getQcBatch(batchId: string) { return request.get<never, {data: QcBatchDetail}>(`/qc/batches/${batchId}`) }
export function auditQcBatch(batchId: string, auditflg?: string, checkmemo?: string) { return request.post<never, {data: unknown}>(`/qc/batches/${batchId}/audit`, {auditflg: auditflg || '1', checkmemo}) }
export function voidQcBatch(batchId: string) { return request.post<never, {data: unknown}>(`/qc/batches/${batchId}/void`) }

// 批量质检录入明细
export interface QcDetailItem { itemcd: string; qcqty: number; qcstatus?: string; inqty?: number; itemtyp?: string; prddate?: string; fault_desc?: string; remark?: string; lineno?: number }
export interface QcEidDetailItem extends QcDetailItem { eid: string }
export interface QcBatchCreate { refbillid: string; optyp: string; itemcd: string; qcstatus: string; memo?: string; details?: QcDetailItem[]; eid_details?: QcEidDetailItem[] }
