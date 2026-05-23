import { ref, type Ref } from 'vue'
import request from '@/api/request'

const dictCache = new Map<string, Ref<Record<string, string>>>()

export function useDict(codeTyp: string): {
    dictMap: Ref<Record<string, string>>
    dictLabel: (code: string) => string
} {
    let map = dictCache.get(codeTyp)
    if (!map) {
        map = ref<Record<string, string>>({})
        dictCache.set(codeTyp, map)
        request.get('/syscodes', {
            params: { code_typ: codeTyp },
            silent: true,
        } as any).then((res: any) => {
            const m: Record<string, string> = {}
            for (const item of res.data || []) {
                const cd = item.code_cd || ''
                const nm = item.code_nm || cd
                m[cd] = nm
            }
            map!.value = m
        }).catch(() => {})
    }

    function dictLabel(code: string): string {
        if (!code) return '-'
        const nm = map!.value[code]
        return nm || code
    }

    return { dictMap: map, dictLabel }
}
