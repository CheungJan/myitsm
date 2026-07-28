import request from './request'

export interface PortalRecord { [key: string]: unknown }
export interface PortalPage { items: PortalRecord[]; total: number }

export function fetchPortalUsers(p?: Record<string, string>) {
    return request.get<never, { data: PortalPage }>('/portal/users', { params: p })
}
export function fetchRepairRequests(p?: Record<string, string>) {
    return request.get<never, { data: PortalPage }>('/portal/repairs', { params: p })
}
export function fetchServiceRatings(p?: Record<string, string>) {
    return request.get<never, { data: PortalPage }>('/portal/ratings', { params: p })
}
