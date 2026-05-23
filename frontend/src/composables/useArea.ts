import { ref, type Ref } from 'vue'
import request from '@/api/request'

const areaMap = ref<Record<string, string>>({})
let loadingPromise: Promise<void> | null = null

export function useArea(): {
    areaMap: Ref<Record<string, string>>
    areaName: (code: string | number) => string
} {
    if (!loadingPromise) {
        loadingPromise = request.get('/areas', { silent: true } as any).then((res: any) => {
            const map: Record<string, string> = {}
            for (const a of res.data || []) {
                if (a.area_cd) {
                    map[a.area_cd.trim()] = a.area_nm || a.name || a.area_cd
                }
            }
            areaMap.value = map
        }).catch(() => {
            loadingPromise = null
        })
    }

    function areaName(code: string | number): string {
        if (code === undefined || code === null) return '-'
        const c = String(code).trim()
        return areaMap.value[c] || c
    }

    return { areaMap, areaName }
}
