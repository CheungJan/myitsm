import type { Directive } from 'vue'
import { useAuthStore } from '@/stores/auth'

export const vPermission: Directive = {
    mounted(el, binding) {
        const { value } = binding
        if (!value) return

        const authStore = useAuthStore()
        const hasPermission = authStore.permList.includes(value as string)

        if (!hasPermission) {
            el.parentNode?.removeChild(el)
        }
    }
}
