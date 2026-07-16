import request from './request'

export interface MntRecord { maintenance_id?: string; opening_id?: string; renew_id?: string; change_id?: string; close_id?: string; recycle_id?: string; custcd?: string; custnm?: string; fault_desc?: string; gendate?: string; status?: string; opercd?: string; [key:string]: unknown }
export interface MntPage { items: MntRecord[]; total: number }

export function fetchMaintenanceDaily(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/maintenance-daily',{params:p})}
export function fetchMaintenanceOpen(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/maintenance-open',{params:p})}
export function fetchMaintenanceOpenDetail(opening_id:string){return request.get<never,{data:MntRecord}>(`/itsm/maintenance-open/${opening_id}`)}
export function updateMaintenanceOpen(opening_id:string, data:Record<string,unknown>){return request.put<never,{data:MntRecord}>(`/itsm/maintenance-open/${opening_id}`,data)}
export function transitionMaintenanceOpen(opening_id:string, data:Record<string,unknown>){return request.post<never,{data:Record<string,unknown>}>(`/itsm/maintenance-open/${opening_id}/transition`,data)}
export function fetchMaintenanceRenovate(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/maintenance-renovate',{params:p})}
export function updateMaintenanceRenovate(renew_id:string, data:Record<string,unknown>){return request.put<never,{data:MntRecord}>(`/itsm/maintenance-renovate/${renew_id}`,data)}
export function transitionMaintenanceRenovate(renew_id:string, data:Record<string,unknown>){return request.post<never,{data:Record<string,unknown>}>(`/itsm/maintenance-renovate/${renew_id}/transition`,data)}
export function fetchDeviceChange(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/device-change',{params:p})}
export function updateDeviceChange(change_id:string, data:Record<string,unknown>){return request.put<never,{data:MntRecord}>(`/itsm/device-change/${change_id}`,data)}
export function transitionDeviceChange(change_id:string, data:Record<string,unknown>){return request.post<never,{data:Record<string,unknown>}>(`/itsm/device-change/${change_id}/transition`,data)}
export function fetchStoreClose(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/store-close',{params:p})}
export function updateStoreClose(close_id:string, data:Record<string,unknown>){return request.put<never,{data:MntRecord}>(`/itsm/store-close/${close_id}`,data)}
export function transitionStoreClose(close_id:string, data:Record<string,unknown>){return request.post<never,{data:Record<string,unknown>}>(`/itsm/store-close/${close_id}/transition`,data)}
export function fetchRecycleTask(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/recycle-task',{params:p})}
export function updateRecycleTask(recycle_id:string, data:Record<string,unknown>){return request.put<never,{data:MntRecord}>(`/itsm/recycle-task/${recycle_id}`,data)}
export function transitionRecycleTask(recycle_id:string, data:Record<string,unknown>){return request.post<never,{data:Record<string,unknown>}>(`/itsm/recycle-task/${recycle_id}/transition`,data)}
export function fetchMaintenancePlans(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/maintenance-plans',{params:p})}
export function updateMaintenanceT17(daily_maintenance_id:string, data:Record<string,unknown>){return request.put<never,{data:MntRecord}>(`/itsm/maintenance/${daily_maintenance_id}`,data)}
export function transitionMaintenanceT17(daily_maintenance_id:string, data:Record<string,unknown>){return request.post<never,{data:Record<string,unknown>}>(`/itsm/maintenance/${daily_maintenance_id}/transition`,data)}
export function fetchMaintenanceT17(p?:Record<string,string>){return request.get<never,{data:MntPage}>('/itsm/maintenance',{params:p})}
export function updateMaintenanceDaily(maintenance_id:string, data:Record<string,unknown>){return request.put<never,{data:MntRecord}>(`/itsm/maintenance-daily/${maintenance_id}`,data)}
export function transitionMaintenanceDaily(maintenance_id:string, data:Record<string,unknown>){return request.post<never,{data:Record<string,unknown>}>(`/itsm/maintenance-daily/${maintenance_id}/transition`,data)}

// ---- 收费自动判断 ----
export function shouldCharge(storeId: string) {
    return request.get<never, { data: { should_charge: boolean; chargeable_assets: { eid: string; reason: string }[]; count: number } }>('/itsm/should-charge', { params: { store_id: storeId } })
}

// ---- 历史同业务单据查询（客户信息 Tab 使用） ----
export function fetchHistoryByStore(type: string, storeId: string) {
    const params: Record<string, string> = {}
    if (type === 'recycle') {
        params.cust_cd = storeId
    } else {
        params.store_id = storeId
    }
    switch (type) {
        case 'open': return fetchMaintenanceOpen(params)
        case 'renovate': return fetchMaintenanceRenovate(params)
        case 'device-change': return fetchDeviceChange(params)
        case 'store-close': return fetchStoreClose(params)
        case 'recycle': return fetchRecycleTask(params)
        case 'daily': return fetchMaintenanceDaily(params)
        case 'maintenance': return fetchMaintenanceT17(params)
        default: return fetchMaintenanceOpen(params)
    }
}

// ---- 公用附表 API ----
export interface SubRecord { id?:number; maintenance_id?:string; [key:string]: unknown }
export function fetchD2D(maintenance_id:string){return request.get<never,{data:SubRecord[]}>(`/itsm/d2d/${maintenance_id}`)}
export function createD2D(data:Record<string,unknown>){return request.post<never,{data:SubRecord}>('/itsm/d2d',data)}
export function updateD2D(record_id:number, data:Record<string,unknown>){return request.put<never,{data:SubRecord}>(`/itsm/d2d/${record_id}`,data)}
export function fetchRV(maintenance_id:string){return request.get<never,{data:SubRecord[]}>(`/itsm/rv/${maintenance_id}`)}
export function createRV(data:Record<string,unknown>){return request.post<never,{data:SubRecord}>('/itsm/rv',data)}
export function updateRV(record_id:number, data:Record<string,unknown>){return request.put<never,{data:SubRecord}>(`/itsm/rv/${record_id}`,data)}
export function fetchAccessories(maintenance_id:string){return request.get<never,{data:SubRecord[]}>(`/itsm/accessories/${maintenance_id}`)}
export function createAccessories(data:Record<string,unknown>){return request.post<never,{data:SubRecord}>('/itsm/accessories',data)}
export function updateAccessories(record_id:number, data:Record<string,unknown>){return request.put<never,{data:SubRecord}>(`/itsm/accessories/${record_id}`,data)}
export function fetchPayList(maintenance_id:string){return request.get<never,{data:SubRecord[]}>(`/itsm/paylist/${maintenance_id}`)}
export function createPayList(data:Record<string,unknown>){return request.post<never,{data:SubRecord}>('/itsm/paylist',data)}
export function updatePayList(record_id:number, data:Record<string,unknown>){return request.put<never,{data:SubRecord}>(`/itsm/paylist/${record_id}`,data)}
export function fetchDispatch(maintenance_id:string){return request.get<never,{data:SubRecord[]}>(`/itsm/dispatch/${maintenance_id}`)}
export function createDispatch(data:Record<string,unknown>){return request.post<never,{data:SubRecord}>('/itsm/dispatch',data)}
export function updateDispatch(record_id:number, data:Record<string,unknown>){return request.put<never,{data:SubRecord}>(`/itsm/dispatch/${record_id}`,data)}
export function fetchCloseBills(maintenance_id:string){return request.get<never,{data:SubRecord[]}>(`/itsm/close-bill/${maintenance_id}`)}
export function createCloseBill(data:Record<string,unknown>){return request.post<never,{data:SubRecord}>('/itsm/close-bill',data)}
export function updateCloseBill(record_id:number, data:Record<string,unknown>){return request.put<never,{data:SubRecord}>(`/itsm/close-bill/${record_id}`,data)}

// ---- 设备明细 API ----
export function addOpenEquipment(opening_id:string, data:Record<string,unknown>){return request.post<never,{data:SubRecord}>(`/itsm/maintenance-open/${opening_id}/equipments`,data)}
export function deleteOpenEquipment(opening_id:string, eq_id:number){return request.delete<never,{data:null}>(`/itsm/maintenance-open/${opening_id}/equipments/${eq_id}`)}
export function fetchRenovateEquipments(renew_id:string){return request.get<never,{data:SubRecord[]}>(`/itsm/maintenance-renovate/${renew_id}/equipments`)}
export function addRenovateEquipment(renew_id:string, data:Record<string,unknown>){return request.post<never,{data:SubRecord}>(`/itsm/maintenance-renovate/${renew_id}/equipments`,data)}
export function deleteRenovateEquipment(renew_id:string, eq_id:number){return request.delete<never,{data:null}>(`/itsm/maintenance-renovate/${renew_id}/equipments/${eq_id}`)}
export function fetchRecycleDetails(recycle_id:string){return request.get<never,{data:SubRecord[]}>(`/itsm/recycle-task/${recycle_id}/details`)}
export function addRecycleDetail(recycle_id:string, data:Record<string,unknown>){return request.post<never,{data:SubRecord}>(`/itsm/recycle-task/${recycle_id}/details`,data)}
export function deleteRecycleDetail(recycle_id:string, asset_id:string){return request.delete<never,{data:null}>(`/itsm/recycle-task/${recycle_id}/details/${asset_id}`)}

// ---- 派单规则 (TIT30) ----
export interface DispatchRule {
    rule_id?: number
    rule_name: string
    priority: number
    fault_type?: string | null
    store_id?: string | null
    target_type?: string | null
    target_value?: string | null
    fallback_type?: string | null
    fallback_value?: string | null
    ultimate_fallback_type?: string | null
    ultimate_fallback_value?: string | null
    useflg?: string
}
export function fetchDispatchRules(){return request.get<never,{data:DispatchRule[]}>('/itsm/dispatch-rules')}
export function createDispatchRule(data:Record<string,unknown>){return request.post<never,{data:DispatchRule}>('/itsm/dispatch-rules',data)}
export function updateDispatchRule(rule_id:number, data:Record<string,unknown>){return request.put<never,{data:DispatchRule}>(`/itsm/dispatch-rules/${rule_id}`,data)}
export function deleteDispatchRule(rule_id:number){return request.delete<never,{data:null}>(`/itsm/dispatch-rules/${rule_id}`)}
export function fetchDispatchResolve(faultType:string, storeId:string){return request.get<never,{data:Record<string,unknown>}>(`/itsm/dispatch-rules/resolve?fault_type=${faultType}&store_id=${storeId}`)}
