import { ref, type Ref } from 'vue'
import request from '@/api/request'

interface CustInfo { card: string; name: string }
const custMap = ref<Record<string, CustInfo>>({})
let loadingPromise: Promise<void> | null = null

export function useCustomerCards(): {
    custMap: Ref<Record<string, CustInfo>>
    custCard: (code: unknown) => string
    custName: (code: unknown) => string
} {
    if (!loadingPromise) {
        loadingPromise = request.get('/customers', {
            params: { per_page: '9999' },
            silent: true,
        } as any).then((res: any) => {
            const map: Record<string, CustInfo> = {}
            const items = res.data?.items || []
            for (const c of items) {
                if (c.cust_cd) {
                    map[c.cust_cd.trim()] = {
                        card: c.cust_card || c.cust_cd,
                        name: c.cust_nm || c.cust_cd,
                    }
                }
            }
            custMap.value = map
        }).catch(() => {
            loadingPromise = null
        })
    }

    function custCard(code: unknown): string {
        const k = code == null ? '' : String(code).trim()
        if (!k) return '-'
        const info = custMap.value[k]
        return info ? info.card : k
    }

    function custName(code: unknown): string {
        const k = code == null ? '' : String(code).trim()
        if (!k) return '-'
        const info = custMap.value[k]
        return info ? info.name : k
    }

    return { custMap, custCard, custName }
}
