import { ref, type Ref } from 'vue'
import request from '@/api/request'

interface CustInfo { card: string; name: string }
const custMap = ref<Record<string, CustInfo>>({})
let loadingPromise: Promise<void> | null = null

export function useCustomerCards(): {
    custMap: Ref<Record<string, CustInfo>>
    custCard: (code: string) => string
    custName: (code: string) => string
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

    function custCard(code: string): string {
        if (!code) return '-'
        const info = custMap.value[code.trim()]
        return info ? info.card : code
    }

    function custName(code: string): string {
        if (!code) return '-'
        const info = custMap.value[code.trim()]
        return info ? info.name : code
    }

    return { custMap, custCard, custName }
}
