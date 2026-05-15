import request from './request'

export interface NotifRecord { [key: string]: unknown }
export interface NotifPage { items: NotifRecord[]; total: number }

export function fetchNotifTemplates(p?: Record<string, string>) {
    return request.get<never, { data: NotifPage }>('/notification/notification-templates', { params: p })
}
export function fetchNotifications(p?: Record<string, string>) {
    return request.get<never, { data: NotifPage }>('/notification/notifications', { params: p })
}
