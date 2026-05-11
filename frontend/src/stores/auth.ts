import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, getSession, logout as logoutApi } from '@/api/auth'
import { fetchUserPermissions } from '@/api/system'

export const useAuthStore = defineStore('auth', () => {
    const token = ref(localStorage.getItem('token') || '')
    const userCode = ref('')
    const userName = ref('')
    const permList = ref<string[]>([])

    function hasPerm(menuCd: string, funcCd: string): boolean {
        return permList.value.includes(menuCd + ':' + funcCd)
    }

    function hasAnyPerm(menuCd: string): boolean {
        return permList.value.some(p => p.startsWith(menuCd + ':'))
    }

    async function fetchPermissions() {
        if (!userCode.value) return
        try {
            const res = await fetchUserPermissions(userCode.value)
            const list = (res.data || []) as { menu_cd: string; func_cd: string }[]
            permList.value = list.map(r => r.menu_cd + ':' + r.func_cd)
        } catch {
            permList.value = []
        }
    }

    async function doLogin(userId: string, password: string) {
        const res = await loginApi(userId, password)
        token.value = res.data.token
        userCode.value = res.data.user_code
        userName.value = res.data.user_name
        localStorage.setItem('token', token.value)
        await fetchPermissions()
    }

    async function fetchSession() {
        try {
            const res = await getSession()
            userCode.value = res.data.user_code
            userName.value = res.data.user_name
            await fetchPermissions()
        } catch {
            logout()
        }
    }

    function logout() {
        logoutApi()  // 通知后端清除多点登录标记
        token.value = ''
        userCode.value = ''
        userName.value = ''
        permList.value = []
        localStorage.removeItem('token')
    }

    return { token, userCode, userName, permList, hasPerm, hasAnyPerm, doLogin, fetchSession, logout }
})
