import request from './request'

export interface NotifRecord { [key: string]: unknown }
export interface NotifPage { items: NotifRecord[]; total: number }
export interface NotifTemplate {
    template_id: string
    template_name?: string
    channel?: string
    subject?: string
    body?: string
    useflg?: string
    [key: string]: unknown
}

export function fetchNotifTemplates(p?: Record<string, string>) {
    return request.get<never, { data: NotifPage }>('/notification/notification-templates', { params: p })
}
export function fetchNotifTemplate(id: string) {
    return request.get<never, { data: NotifTemplate }>(`/notification/notification-templates/${id}`)
}
export function createNotifTemplate(data: Record<string, unknown>) {
    return request.post<never, { data: NotifTemplate }>('/notification/notification-templates', data)
}
export function updateNotifTemplate(id: string, data: Record<string, unknown>) {
    return request.put<never, { data: NotifTemplate }>(`/notification/notification-templates/${id}`, data)
}
export function previewNotifTemplate(data: { subject: string; body: string; context?: Record<string, string> }) {
    return request.post<never, { data: { subject: string; body: string; error?: string } }>('/notification/notification-templates/preview', data)
}
export function fetchNotifications(p?: Record<string, string>) {
    return request.get<never, { data: NotifPage }>('/notification/notifications', { params: p })
}
export function sendNotification(id: number) {
    return request.post<never, { data: NotifRecord }>(`/notification/notifications/${id}/send`)
}
export function markNotificationRead(id: number) {
    return request.post<never, { data: NotifRecord }>(`/notification/notifications/${id}/read`)
}
export function fetchUnreadCount() {
    return request.get<never, { data: { count: number } }>('/notification/notifications/unread-count')
}

export interface ChannelInfo {
    channel: string
    label: string
    require_config: string
    enabled: boolean
    implemented: boolean
}

export function fetchChannels() {
    return request.get<never, { data: { channels: ChannelInfo[] } }>('/notification/channels')
}
