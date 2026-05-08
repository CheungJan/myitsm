import request from './request'

export function login(userId: string, password: string) {
    return request.post('/login', { user_id: userId, password })
}

export function getSession() {
    return request.get('/session')
}
