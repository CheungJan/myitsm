import request from './request'

export interface IotRecord { [key: string]: unknown }
export interface IotPage { items: IotRecord[]; total: number }

export function fetchDeviceConns(p?: Record<string, string>) {
    return request.get<never, { data: IotPage }>('/iot/connections', { params: p })
}
export function fetchDeviceData(eid: string, p?: Record<string, string>) {
    return request.get<never, { data: IotPage }>(`/iot/data/${eid}`, { params: p })
}
export function fetchAlertRules(p?: Record<string, string>) {
    return request.get<never, { data: IotPage }>('/iot/alert-rules', { params: p })
}
export function fetchAlertLogs(p?: Record<string, string>) {
    return request.get<never, { data: IotPage }>('/iot/alerts', { params: p })
}
