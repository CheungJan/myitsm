import request from './request'

export interface AttendRecord { [key: string]: unknown }
export interface AttendPage { items: AttendRecord[]; total: number }

export function fetchAttendance(p?: Record<string, string>) {
    return request.get<never, { data: AttendPage }>('/attendance/attendance', { params: p })
}
export function fetchAttendanceSummary(p?: Record<string, string>) {
    return request.get<never, { data: AttendPage }>('/attendance/attendance/summary', { params: p })
}
