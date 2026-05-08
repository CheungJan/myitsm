import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, getSession } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
    const token = ref(localStorage.getItem('token') || '')
    const userCode = ref('')
    const userName = ref('')
    const permissions = ref<string[]>([])

    async function doLogin(userId: string, password: string) {
        const res = await loginApi(userId, password)
        token.value = res.data.token
        userCode.value = res.data.user_code
        userName.value = res.data.user_name
        localStorage.setItem('token', token.value)
    }

    async function fetchSession() {
        try {
            const res = await getSession()
            userCode.value = res.data.user_code
            userName.value = res.data.user_name
            permissions.value = res.data.permissions || []
        } catch {
            logout()
        }
    }

    function logout() {
        token.value = ''
        userCode.value = ''
        userName.value = ''
        permissions.value = []
        localStorage.removeItem('token')
    }

    return { token, userCode, userName, permissions, doLogin, fetchSession, logout }
})
