import request from './request'

export function login(userId: string, password: string) {
    return request.post('/login', { user_id: userId, password })
}

export function getSession() {
    return request.get('/session')
}

export function logout() {
    return request.post('/logout').catch(() => { /* 静默失败，确保清除本地状态 */ })
}
