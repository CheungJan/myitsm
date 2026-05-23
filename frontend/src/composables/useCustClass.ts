import { ref, type Ref } from 'vue'
import request from '@/api/request'

const classMap = ref<Record<string, string>>({})
let loadingPromise: Promise<void> | null = null

export function useCustClass(): {
    classMap: Ref<Record<string, string>>
    className: (code: string) => string
} {
    if (!loadingPromise) {
        loadingPromise = request.get('/custclasses', { silent: true } as any).then((res: any) => {
            const map: Record<string, string> = {}
            for (const c of res.data || []) {
                if (c.class_cd) map[c.class_cd.trim()] = c.class_nm || c.class_cd
            }
            classMap.value = map
        }).catch(() => {
            loadingPromise = null
        })
    }

    function className(code: string): string {
        if (!code) return '-'
        return classMap.value[code.trim()] || code
    }

    return { classMap, className }
}
