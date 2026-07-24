import { ref, type Ref } from 'vue'
import request from '@/api/request'

const userMap = ref<Record<string, string>>({})
let loadingPromise: Promise<void> | null = null

export function useUserNames(): { userMap: Ref<Record<string, string>>; userName: (code: unknown) => string } {
    if (!loadingPromise) {
        loadingPromise = request.get('/users', {
            params: { per_page: '9999' },
            silent: true,
        } as any).then((res: any) => {
            const map: Record<string, string> = {}
            const items = res.data?.items || res.data || []
            for (const u of items) {
                if (u.user_cd) map[u.user_cd.trim()] = u.user_nm
            }
            userMap.value = map
        }).catch(() => {
            loadingPromise = null
        })
    }

    function userName(code: unknown): string {
        const k = code == null ? '' : String(code).trim()
        if (!k) return '-'
        return userMap.value[k] || k
    }

    return { userMap, userName }
}
