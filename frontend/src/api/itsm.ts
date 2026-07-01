import request from './request'

export interface MntRecord { maintenance_id?: string; opening_id?: string; renew_id?: string; change_id?: string; close_id?: string; recycle_id?: string; custcd?: string; custnm?: string; fault_desc?: string; gendate?: string; status?: string; opercd?: string; [key:string]: unknown }
export interface MntPage { items: MntRecord[]; total: number }

export function fetchMaintenanceDaily(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/maintenance-daily',{params:p})}
export function fetchMaintenanceOpen(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/maintenance-open',{params:p})}
export function fetchMaintenanceOpenDetail(opening_id:string){return request.get<never,{data:MntRecord}>(`/itsm/maintenance-open/${opening_id}`)}
export function fetchMaintenanceRenovate(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/maintenance-renovate',{params:p})}
export function fetchDeviceChange(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/device-change',{params:p})}
export function fetchStoreClose(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/store-close',{params:p})}
export function fetchRecycleTask(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/recycle-task',{params:p})}
export function fetchMaintenancePlans(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/maintenance-plans',{params:p})}
export function fetchMaintenanceT17(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/maintenance',{params:p})}
export interface FreeReplaceRecord { renew_id: string; store_id?: string; short_description?: string; old_device_id?: string; new_device_id?: string; current_status?: string; count?: number; create_time?: string; creator?: string; equipments?: Record<string,unknown>[]; [key:string]: unknown }
export interface FreeReplacePage { items: FreeReplaceRecord[]; total: number }
export function fetchFreeReplace(p?:Record<string,string>){return request.get<never,{data:FreeReplacePage}>('/itsm/free-replace',{params:p})}
