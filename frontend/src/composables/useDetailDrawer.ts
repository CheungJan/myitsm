import { ref, type Ref } from 'vue'

export function useDetailDrawer<T extends Record<string,unknown>>() {
  const drawer = ref(false)
  const detail = ref<T | null>(null) as Ref<T | null>

  function open(data: T) { detail.value = data; drawer.value = true }
  function close() { drawer.value = false }

  return { drawer, detail, open, close }
}
