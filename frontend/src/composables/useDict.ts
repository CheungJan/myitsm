import { ref, type Ref } from 'vue'
import request from '@/api/request'

const dictCache = new Map<string, Ref<Record<string, string>>>()
const dictListCache = new Map<string, Ref<{ value: string; label: string }[]>>()
const dictLoaded = new Set<string>()

export function useDict(codeTyp: string): {
    dictMap: Ref<Record<string, string>>
    dictOptions: Ref<{ value: string; label: string }[]>
    dictLabel: (code: string) => string
} {
    let map = dictCache.get(codeTyp)
    let opts = dictListCache.get(codeTyp)
    if (!map) {
        map = ref<Record<string, string>>({})
        dictCache.set(codeTyp, map)
    }
    if (!opts) {
        opts = ref<{ value: string; label: string }[]>([])
        dictListCache.set(codeTyp, opts)
    }
    if (!dictLoaded.has(codeTyp)) {
        dictLoaded.add(codeTyp)
        request.get('/syscodes', {
            params: { code_typ: codeTyp },
            silent: true,
        } as any).then((res: any) => {
            const m: Record<string, string> = {}
            const list: { value: string; label: string }[] = []
            for (const item of res.data || []) {
                const cd = item.code_cd || ''
                const nm = item.code_nm || cd
                m[cd] = nm
                list.push({ value: cd, label: nm })
            }
            map!.value = m
            opts!.value = list
        }).catch(() => {})
    }

    function dictLabel(code: string): string {
        if (!code) return '-'
        const nm = map!.value[code]
        return nm || code
    }

    return { dictMap: map, dictOptions: opts, dictLabel }
}
