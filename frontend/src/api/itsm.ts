import request from './request'
export interface MntRecord { [key:string]: unknown }
export interface MntPage { items: MntRecord[]; total: number }
export function fetchMaintenanceDaily(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/maintenance-daily',{params:p})}
